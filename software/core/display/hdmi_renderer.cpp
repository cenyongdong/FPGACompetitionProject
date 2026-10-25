#include "hdmi_renderer.hpp"
#include "raster565.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <utility>

namespace pose::hdmi {
    namespace {
        using namespace detail;
        using Vec = std::array<double, 3>;
        constexpr Vec camera{{5, 4.05, 7}};
        constexpr double center_x = width / 2.0, center_y = (top + bottom + 1) / 2.0;
        constexpr double hidden = -1e6;
        const double focal = (bottom - top + 1) / (2 * std::tan(36 * std::acos(-1.0) / 360));
        const Vec forward{{-5 / std::sqrt(83.0), -3 / std::sqrt(83.0), -7 / std::sqrt(83.0)}};
        const Vec side{{7 / std::sqrt(74.0), 0, -5 / std::sqrt(74.0)}};
        const Vec up{{-15 / std::sqrt(6142.0), 74 / std::sqrt(6142.0), -21 / std::sqrt(6142.0)}};
        double dot(const Vec& a, const Vec& b) {return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
        Vec relative(const Vec& p) {return {{p[0]-camera[0],p[1]-camera[1],p[2]-camera[2]}};}
        std::array<double, 2> project_scene(const Vec& p) {
            const auto v=relative(p);const double depth=dot(v,forward);
            // Do not mirror geometry behind the perspective camera or divide at its eye plane.
            if (depth <= 0.05) return {{hidden,hidden}};
            return {{center_x+focal*dot(v,side)/depth,center_y-focal*dot(v,up)/depth}};
        }
        std::array<double, 2> project(double a, double b, double c) {
            // Same display-only coordinates, target (0,1.05,0), camera and 36deg
            // vertical FOV as demo_v1/web/scene.js perspective. No per-pose fit.
            return project_scene({{a-1.75,4.2-c,1.75-b}});
        }
        uint16_t ground_ink(const Vec& p, const Vec& rgb, double opacity) {
            const auto v=relative(p);
            const double mix=opacity*std::exp(-0.075*0.075*dot(v,v));
            return color(unsigned(14+(rgb[0]-14)*mix),unsigned(25+(rgb[1]-25)*mix),
                         unsigned(37+(rgb[2]-37)*mix));
        }
        void ground_line(std::vector<uint8_t>& image, const Vec& a, const Vec& b,
                         const Vec& rgb, double opacity=0.6) {
            const auto p=project_scene(a),q=project_scene(b);
            if (p[0]==hidden || q[0]==hidden) return;
            const Vec middle{{(a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2}};
            line(image,p[0],p[1],q[0],q[1],ground_ink(middle,rgb,opacity),1.5);
        }

        const std::vector<uint8_t>& background() {
            static const std::vector<uint8_t> pixels = [] {
                std::vector<uint8_t> image(frame_bytes);
                rect(image,0,0,width,height,color(11,17,27));
                // Ground and fog are cached once; each live frame still only copies
                // the fixed RGB565 base and draws the current owning pose values.
                for (int y=top;y<=bottom;++y) for (int x=left;x<=right;++x) {
                    const double sx=(x-center_x)/focal,sy=(center_y-y)/focal;
                    const Vec ray{{forward[0]+sx*side[0]+sy*up[0],
                                   forward[1]+sy*up[1],forward[2]+sx*side[2]+sy*up[2]}};
                    if (ray[1]>=0) continue;
                    const double t=(-0.013-camera[1])/ray[1];
                    const double px=camera[0]+t*ray[0],pz=camera[2]+t*ray[2];
                    if (std::abs(px)>8 || std::abs(pz)>8) continue;
                    const double fog=std::exp(-0.075*0.075*t*t*dot(ray,ray));
                    pixel(image,x,y,color(unsigned(11+3*fog),unsigned(17+8*fog),unsigned(27+10*fog)));
                }
                for (int n=-9;n<=9;++n) {
                    const double v=n*.5;
                    const Vec grid=n ? Vec{{30,48,62}} : Vec{{49,73,84}};
                    ground_line(image,{{v,0,-4.5}},{{v,0,4.5}},grid);
                    ground_line(image,{{-4.5,0,v}},{{4.5,0,v}},grid);
                }
                for (int n=0;n<100;++n) {
                    const double a=n*2*std::acos(-1.0)/100,b=(n+1)*2*std::acos(-1.0)/100;
                    ground_line(image,{{-1+1.353*std::cos(a),.002,.4+1.353*std::sin(a)}},
                                      {{-1+1.353*std::cos(b),.002,.4+1.353*std::sin(b)}},{{107,174,167}},.28);
                }
                const Vec origin{{-1.6,.006,1.6}};
                ground_line(image,origin,{{-1.15,.006,1.6}},{{179,123,104}},.7);
                ground_line(image,origin,{{-1.6,.45,1.6}},{{129,225,213}},.7);
                ground_line(image,origin,{{-1.6,.006,1.15}},{{102,138,179}},.7);
                text(image,32,28,"WIFI 3D POSE",4,color(229,237,247));
                text(image,1760,34,"PS/NPU",2.5,color(159,200,231));
                const auto label=color(194,214,223);
                text(image,400,84,"FRAME",2.5,label);
                text(image,850,84,"SLOT",2.5,label);
                text(image,1100,84,"SCORE",2.5,label);
                text(image,32,146,"HIGHEST SCORE / ORIGINAL MODEL UNITS",2,color(159,200,231));
                text(image,32,196,"FIXED PERSPECTIVE / 14 JOINTS / NO TRACKING / NO CALIBRATION",2,
                     color(149,168,185));
                return image;
            }();
            return pixels;
        }
    }

    static void draw_pose(Rendered& result) {
        for (const auto bone : pose_v1::render::bones) {
            const auto a = result.projected[bone[0]], b = result.projected[bone[1]];
            if (a[0]==hidden || b[0]==hidden) continue;
            // Match the reference screenshot's lit/fogged appearance, rather
            // than the much brighter unlit WebGL material RGB values.
            line(result.rgb565,a[0],a[1],b[0],b[1],color(96,128,128),3);
        }
        for (size_t i = 0; i < result.projected.size(); ++i) {
            const auto p = result.projected[i];
            if (code(p[0], p[1])) continue;
            const int x = int(std::lround(p[0])), y = int(std::lround(p[1]));
            for (int dy=-4;dy<=4;++dy) for (int dx=-4;dx<=4;++dx)
                if (dx*dx+dy*dy<=16 && !code(x+dx,y+dy))
                    pixel(result.rgb565,x+dx,y+dy,color(128,128,112));
        }
    }
    static void draw_result_fields(Rendered& result, uint64_t id) {
        const auto white = color(236, 241, 247);
        text(result.rgb565,500,84,std::to_string(id),2.5,white);
        text(result.rgb565,950,84,std::to_string(result.top_index),2.5,white);
        std::ostringstream score;
        score << std::fixed << std::setprecision(4) << result.score;
        std::string shown = score.str();
        if (shown.size() > 15) shown = "OUT OF RANGE";
        text(result.rgb565,1220,84,shown,2.5,color(194,214,223));
    }

    static void draw_status(Rendered& result,const char* label,bool live) {
        rect(result.rgb565,32,72,350,116,live?color(23,61,54):color(73,61,35));
        text(result.rgb565,46,84,label,2.5,live?color(179,244,219):color(255,224,160));
    }

    static Rendered render_impl(PreparedBackground* prepared,
                    const float* scores, const float* poses, std::size_t candidates,
                    uint64_t id, pose_v1::render::Status status) {
        const auto begin = std::chrono::steady_clock::now();
        if (!scores || !poses || (candidates != 100 && candidates != 180))
            throw std::runtime_error("Unsupported candidate raster input");
        for (std::size_t i=0;i<candidates;++i)
            if (!std::isfinite(scores[i])) throw std::runtime_error("Non-finite candidate score");
        for (std::size_t i=0;i<candidates*42;++i)
            if (!std::isfinite(poses[i])) throw std::runtime_error("Non-finite candidate pose");
        using pose_v1::render::Status;
        if (status != Status::Result && status != Status::NoInput && status != Status::Stopped)
            throw std::runtime_error("Unknown result status");

        if (prepared && prepared->rgb565.size() != frameBytes)
            throw std::runtime_error("Prepared HDMI background byte count differs");
        Rendered result;
        result.top_index = unsigned(std::max_element(scores, scores+candidates) - scores);
        result.score = scores[result.top_index];
        std::copy_n(poses + result.top_index * 42, 42, result.selected_raw.begin());
        if (prepared) result.rgb565 = std::move(prepared->rgb565);
        else result.rgb565 = background(); // Existing one-call API keeps its timing scope.
        // Keep the full 20-digit frame id and recovery state in the top header.
        draw_result_fields(result,id);
        draw_status(result,status==Status::Result?"RESULT":status==Status::NoInput?"NO INPUT":"STOPPED",
                    status==Status::Result);

        for (size_t i = 0; i < result.projected.size(); ++i) {
            result.projected[i] = project(result.selected_raw[i * 3],
                                          result.selected_raw[i * 3 + 1],
                                          result.selected_raw[i * 3 + 2]);
            if (code(result.projected[i][0], result.projected[i][1])) ++result.clipped_joints;
        }
        if (status == Status::Result) draw_pose(result);
        result.render_ms = std::chrono::duration<double, std::milli>(
            std::chrono::steady_clock::now() - begin).count();
        return result;
    }
    PreparedBackground prepare_background() {
        return PreparedBackground{background()};
    }
    void prepare_background(PreparedBackground& reusable) {
        reusable.rgb565.assign(background().begin(),background().end());
    }
    Rendered render_notice(PreparedBackground&& prepared, const Rendered* last_result,
                           uint64_t last_frame_id, const Notice& notice) {
        const auto begin = std::chrono::steady_clock::now();
        if (prepared.rgb565.size()!=frameBytes || bool(last_result)!=notice.has_result ||
            notice.kind==NoticeKind::Result)
            throw std::runtime_error("Invalid HDMI notice context");
        Rendered result;
        result.rgb565=std::move(prepared.rgb565);
        if (last_result) {
            result.top_index=last_result->top_index;result.score=last_result->score;
            result.clipped_joints=last_result->clipped_joints;
            result.selected_raw=last_result->selected_raw;result.projected=last_result->projected;
            draw_result_fields(result,last_frame_id);draw_pose(result);
        } else {
            const auto muted=color(167,184,204);
            text(result.rgb565,500,84,"--",2.5,muted);
            text(result.rgb565,950,84,"--",2.5,muted);
            text(result.rgb565,1220,84,"--",2.5,muted);
        }
        const char* label=notice.kind==NoticeKind::Stale ? "RESULT STALE" :
            notice.kind==NoticeKind::Resynchronizing ? "RESYNCHRONIZING" : "WAITING INPUT";
        draw_status(result,label,false);
        const std::string age=notice.has_result ? "AGE " + std::to_string(notice.age_seconds) + " S" : "NO RESULT YET";
        text(result.rgb565,1500,146,age,2,color(236,241,247));
        if (notice.kind==NoticeKind::Stale)
            text(result.rgb565,1500,196,notice.resynchronizing?"RESYNC":"WAITING INPUT",2,color(167,184,204));
        result.render_ms=std::chrono::duration<double,std::milli>(
            std::chrono::steady_clock::now()-begin).count();
        return result;
    }
    Rendered render(PreparedBackground&& prepared, const float* scores,
                    const float* poses, std::size_t candidates, uint64_t id,
                    pose_v1::render::Status status) {
        return render_impl(&prepared,scores,poses,candidates,id,status);
    }

    Rendered render(PreparedBackground&& prepared,
                    const std::array<float, 100>& scores,
                    const std::array<float, 4200>& poses,
                    uint64_t id, pose_v1::render::Status status) {
        return render_impl(&prepared, scores.data(), poses.data(), scores.size(), id, status);
    }

    Rendered render(const std::array<float, 100>& scores,
                    const std::array<float, 4200>& poses,
                    uint64_t id, pose_v1::render::Status status) {
        return render_impl(nullptr, scores.data(), poses.data(), scores.size(), id, status);
    }

}
