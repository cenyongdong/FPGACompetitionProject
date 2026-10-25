#include "journal.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>
using namespace pose180_demo;
namespace fs=std::filesystem;
void check(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
int main(int argc,char**argv) {
    try {
        check(argc==2,"Need fresh test output directory");fs::path root=argv[1];
        check(fs::create_directory(root),"Test output already exists");
        fs::create_directory(root/"rotation");Shared shared;
        {
            Journal journal(shared,root/"rotation");
            for(unsigned i=0;i<900;++i) {
                const auto text="{\"event\":\"csi_test\",\"ordinal\":"+std::to_string(i)+",\"pad\":\""+std::string(960,'x')+"\"}\n";
                journal.diagnostic(text);std::this_thread::sleep_for(std::chrono::milliseconds(2));
            }
        }
        std::uintmax_t total=0;unsigned files=0,lines=0;
        for(const auto& file:fs::directory_iterator(root/"rotation")) {
            check(file.path().filename().string().find("diagnostic-")==0,"CSI log spilled into normal archive");
            ++files;total+=file.file_size();check(file.file_size()<=256*1024,"Diagnostic segment exceeded cap");
            std::ifstream input(file.path());std::string line;
            while(std::getline(input,line)){check(!line.empty()&&line.front()=='{'&&line.back()=='}'&&line.size()<1024,"Partial diagnostic line");++lines;}
        }
        check(files==2&&total>256*1024&&total<=512*1024&&lines>260,"Rotation did not retain bounded whole lines");
        fs::create_directory(root/"disk-full");
        fs::create_symlink("/dev/full",root/"disk-full/diagnostic-0.jsonl");
        Shared failed;
        {
            Journal journal(failed,root/"disk-full");
            journal.diagnostic("{\"event\":\"csi_test\"}\n");
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            Record record{};journal.record(record);
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            check(fs::file_size(root/"disk-full/recent-0.full")==record.size(),"Diagnostic failure blocked normal result recording");
        }
        std::cout<<"journal rotation and diagnostic disk-full isolation passed; retained_lines="<<lines<<'\n';return 0;
    }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
}
