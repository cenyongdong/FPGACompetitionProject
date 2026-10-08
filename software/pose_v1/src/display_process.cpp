#include "display_process.hpp"
#include <spawn.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>
#include <fstream>
#include <thread>
#include <cerrno>
#include <dirent.h>
#include <stdexcept>

extern char** environ;
namespace pose::display {
namespace {void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}}
struct Process::Impl {
    int socket=-1;pid_t child=-1;bool done=false,failed=false;std::ofstream log;
    bool reap(unsigned ms,int& status){
        const auto deadline=wire::now()+uint64_t(ms)*1000000;
        do{pid_t r=::waitpid(child,&status,WNOHANG);if(r==child){child=-1;return true;}
            if(r<0&&errno!=EINTR){child=-1;return false;}std::this_thread::sleep_for(std::chrono::milliseconds(5));
        }while(wire::now()<deadline);return false;
    }
    void cleanup()noexcept{
        if(socket>=0){::shutdown(socket,SHUT_RDWR);::close(socket);socket=-1;}
        if(child>0){int status=0;if(!reap(300,status)&&child>0){::kill(child,SIGTERM);if(!reap(300,status)&&child>0){::kill(child,SIGKILL);while(::waitpid(child,&status,0)<0&&errno==EINTR){}child=-1;}}
            if(log)log<<"{\"event\":\"error_cleanup_reaped\",\"wait_status\":"<<status<<"}\n";
        }
    }
    Impl(const std::filesystem::path& exe,const std::filesystem::path& out){
        need(!std::filesystem::exists(out),"Preserve display process evidence");std::filesystem::create_directory(out);log.open(out/"parent.jsonl");need(bool(log),"Display parent log failed");
        int pair[2]{-1,-1};need(::socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC|SOCK_NONBLOCK,0,pair)==0,"Display socketpair failed");
        posix_spawn_file_actions_t actions;bool initialized=false;
        try{
            need(posix_spawn_file_actions_init(&actions)==0,"Display spawn actions failed");initialized=true;
            need(posix_spawn_file_actions_adddup2(&actions,pair[1],3)==0,"Display spawn dup failed");
            // After dup2, keep only0/1/2/3. No parent evidence/device fd crosses exec.
            DIR* directory=::opendir("/proc/self/fd");need(directory!=nullptr,"Display fd inventory failed");
            const int inventoryFd=::dirfd(directory);bool closedActions=true;
            while(auto* entry=::readdir(directory)){if(entry->d_name[0]=='.')continue;const int fd=std::stoi(entry->d_name);if(fd>=4&&fd!=inventoryFd)closedActions &= posix_spawn_file_actions_addclose(&actions,fd)==0;}
            ::closedir(directory);need(closedActions,"Display spawn close action failed");
            auto stdoutPath=(out/"child.stdout.log").string(),stderrPath=(out/"child.stderr.log").string();
            need(posix_spawn_file_actions_addopen(&actions,1,stdoutPath.c_str(),O_WRONLY|O_CREAT|O_EXCL,0600)==0,"Display stdout action failed");
            need(posix_spawn_file_actions_addopen(&actions,2,stderrPath.c_str(),O_WRONLY|O_CREAT|O_EXCL,0600)==0,"Display stderr action failed");
            auto executable=std::filesystem::canonical(exe).string();auto evidence=std::filesystem::canonical(out).string();char fd[]="3";
            char* argv[]{const_cast<char*>(executable.c_str()),fd,const_cast<char*>(evidence.c_str()),nullptr};
            need(::posix_spawn(&child,executable.c_str(),&actions,nullptr,argv,environ)==0,"Display exec failed");
            posix_spawn_file_actions_destroy(&actions);initialized=false;::close(pair[1]);pair[1]=-1;socket=pair[0];pair[0]=-1;
            auto h=wire::readHeader(socket);need(h.kind==wire::Kind::Ready&&h.frame==uint64_t(child)&&h.begin<=wire::now(),"Display readiness identity differs");
            log<<"{\"event\":\"spawned\",\"pid\":"<<child<<",\"parent_pid\":"<<::getpid()<<",\"one_request_credit\":true}"<<std::endl;
        }catch(...){if(initialized)posix_spawn_file_actions_destroy(&actions);for(int fd:pair)if(fd>=0)::close(fd);cleanup();throw;}
    }
    ~Impl(){cleanup();}
};
Process::Process(const std::filesystem::path& exe,const std::filesystem::path& out):p_(std::make_unique<Impl>(exe,out)){}
Process::~Process()=default;
int Process::pid()const{return p_->child;}
Image Process::render(const Pose& request,const Cancel& cancel){
    need(!p_->done&&!p_->failed,"Display process stopped");validate(request);
    try{
        wire::writeHeader(p_->socket,{wire::Kind::Render,poseBytes,request.frame,request.invocation,request.publishedNs},cancel);
        wire::write(p_->socket,request.scores.data(),sizeof(request.scores),cancel);wire::write(p_->socket,request.poses.data(),sizeof(request.poses),cancel);
        const auto h=wire::readHeader(p_->socket,cancel);
        need(h.kind==wire::Kind::Image&&h.frame==request.frame&&h.invocation==request.invocation&&request.publishedNs<=h.begin&&h.begin<=h.drawEnd&&h.drawEnd<=h.convertEnd&&h.convertEnd<=wire::now(),"Display reply identity/clock differs");
        Image image{h.frame,h.invocation,h.begin,h.drawEnd,h.convertEnd,0,{}};image.nv12.resize(nv12Bytes);wire::read(p_->socket,image.nv12.data(),image.nv12.size(),cancel);image.receivedEnd=wire::now();return image;
    }catch(...){p_->failed=true;throw;}
}
void Process::finish(){
    need(!p_->done&&!p_->failed,"Display process cannot finish after error");
    try{wire::writeHeader(p_->socket,{wire::Kind::Stop});const auto h=wire::readHeader(p_->socket);need(h.kind==wire::Kind::Stopped,"Display STOP acknowledgment missing");
        int status=0;need(p_->reap(1000,status)&&WIFEXITED(status)&&WEXITSTATUS(status)==0,"Display child failed to exit cleanly");
        ::close(p_->socket);p_->socket=-1;p_->done=true;p_->log<<"{\"event\":\"cleanly_reaped\",\"wait_status\":0}"<<std::endl;
    }catch(...){p_->failed=true;throw;}
}
}
