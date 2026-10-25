# Native RGB565 HDMI renderer

`hdmi_renderer.hpp/.cpp` implement `pose::hdmi::render(scores, poses, id, status)` and return an independent `Rendered` owning value. The output is exactly 1920×1080×2 = 4,147,200 tightly packed bytes, RGB565 with the low byte first and a 3,840-byte row stride. Colors are quantized directly; there is no per-frame RGB24 image or 1280→1920 bilinear resampling.

The immutable RGB565 gradient, panels, fixed text, grid and coordinate axes are cached once; each frame copies that 4,147,200-byte background and draws only changing frame/slot/score/status text, skeletons and joint numbers. First-frame render_ms includes initialization. There are no SDK, model, NPU, MMIO, network or protocol operations here.

## Latest layout constraint

- Main clip viewport: x=36..1538, y=116..1018; information panel: x=1568..1919, width 352.
- Projection centre: (780,535). The original public projection is transformed by `(old-(460,355))*1.5+(780,535)`; its original angles, centring in model units and axis meaning stay intact. Scale is **330 pixels/model-unit**, the old 220×1.5 size; **350 was not adopted**. More viewport space does not enlarge the skeleton.
- Joint radius: 6 pixels (old 4×1.5); joint-number glyph scale: 1.5 with floor-mapped glyph cell edges and 9-pixel character advance. Joint labels have not been enlarged to scale 2.
- Bone stroke: nominal 4.5 pixels (old 3×1.5), mapped to four/five-pixel rectangles according to subpixel phase; no additional 6/7-pixel stamp. Grid strokes are nominal 1.5 pixels.
- All 14 joint numbers and frame, selected slot, score, status remain visible where geometrically in range. Candidate selection, finite checks, selected raw values and topology follow the former renderer.

## Compilation and integration

Compile hdmi_renderer.cpp as C++17; add this directory and the existing directories containing skeleton_render.hpp and hdmi_format.hpp to include paths. Width, height and frameBytes come from that existing hdmi_format.hpp; they are not redefined here. `font5x7.hpp` holds the original 41 glyph definitions; `raster565.hpp` supplies the native pixel/rectangle/clip/line/text primitives. No .cpp file is included by another .cpp file.

This module calls the existing `pose_v1::render::project()` symbol. It must be linked from the original skeleton_render.cpp object or a parent-owned extraction of the unchanged public projection implementation. It reuses the public bones/Status declarations, and does not call the old RGB draw(), canvas(), rgb565_le() or YUV routines. Production integration should call render() and submit its rgb565 owning buffer directly; integrating that caller is outside this directory.

Pixel output intentionally differs from the former bilinear path: direct RGB565 color quantization, native hard raster edges, relocated view centre and larger clipping area, compact information panel. **It is not claimed byte-identical to the old resampled image.** Non-timing model values and selection should still be compared independently. Compilation, previews, CPU benchmarks and hardware validation belong to the parent task; none has been run by this source-only change.
