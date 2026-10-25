/* Own-router RAM-only supervisor. No persistent radio config, no board SDK.
 * RX: one bounded TCP buffer, fresh capture per connection, finite backoff.
 * TX: repeat existing finite 60-second jobs, verify native 48-byte status.
 */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t stop_requested;
static double began, deadline, paused_until, next_state;
static unsigned generation, failures, completed;
static unsigned long long forwarded;
static const char *state = "starting";
static int last_exit, fault;
static void stop_handler(int sig) { (void)sig; stop_requested = 1; }
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec / 1e9; }
static int exists(const char *p) { return !access(p, F_OK); }
static void event(const char *message) {
    struct stat s;
    if (!stat("guard.log", &s) && s.st_size >= 65536) rename("guard.log", "guard.previous.log");
    FILE *f = fopen("guard.log", "a");
    if (f) { fprintf(f, "%.3f %s generation=%u exit=%d\n", now()-began, message, generation, last_exit); fclose(f); }
}
static void status(void) {
    double t = now();
    if (t < next_state) return;
    next_state = t + 1;
    FILE *f = fopen("lease", "w");
    if (f) { fprintf(f, "%u\n", (unsigned)t); fclose(f); }
    f = fopen("guard-status.tmp", "w");
    if (f) {
        fprintf(f, "{\"pid\":%d,\"state\":\"%s\",\"elapsed\":%.3f,\"generation\":%u,\"failures\":%u,\"completed_TX_jobs\":%u,\"forwarded_bytes\":%llu,\"last_exit\":%d,\"fault\":%d}\n",
                getpid(), state, t-began, generation, failures, completed, forwarded, last_exit, fault);
        fclose(f); rename("guard-status.tmp", "guard-status.json");
    }
}
static int running(void) {
    status();
    return !stop_requested && now() < deadline && exists("armed") && !exists("restored") && !exists("stop.request");
}
static int paused(void) {
    if (exists("pause.seconds")) {
        unsigned seconds = 0;
        FILE *f = fopen("pause.seconds", "r");
        if (f) { if (fscanf(f, "%u", &seconds) != 1) seconds = 0; fclose(f); }
        unlink("pause.seconds");
        if (seconds && seconds <= 120) { paused_until = now() + seconds; event("pause requested"); }
    }
    return now() < paused_until;
}
static void rest(double seconds) {
    double until = now() + seconds;
    while (running() && now() < until) usleep(50000);
}
static int reap(pid_t pid, int terminate) {
    int s = 0;
    if (terminate) kill(pid, SIGTERM);
    double until = now() + 1;
    for (;;) {
        pid_t got = waitpid(pid, &s, WNOHANG);
        if (got == pid) return WIFEXITED(s) ? WEXITSTATUS(s) : 128 + WTERMSIG(s);
        if (got < 0) return 99;
        if (now() > until) { kill(pid, SIGKILL); waitpid(pid, &s, 0); return 128 + SIGKILL; }
        usleep(10000);
    }
}
/* Only own userspace capture/nexutil children are ever terminated. */
static int command(char *const argv[], char *output, size_t capacity, unsigned budget) {
    int p[2];
    if (pipe2(p, O_CLOEXEC)) return 99;
    pid_t pid = fork();
    if (pid == 0) {
        dup2(p[1], 1); dup2(p[1], 2); close(p[0]); close(p[1]);
        execv(argv[0], argv); _exit(127);
    }
    close(p[1]);
    if (pid < 0) { close(p[0]); return 99; }
    fcntl(p[0], F_SETFL, O_NONBLOCK);
    size_t used = 0; double until = now() + budget; int s = 0, done = 0;
    while (!done) {
        char bytes[1024]; ssize_t n;
        while ((n = read(p[0], bytes, sizeof(bytes))) > 0) {
            size_t take = (size_t)n < capacity-1-used ? (size_t)n : capacity-1-used;
            memcpy(output+used, bytes, take); used += take;
        }
        if (waitpid(pid, &s, WNOHANG) == pid) { done = 1; break; }
        if (now() > until) { close(p[0]); output[used] = 0; return reap(pid, 1); }
        status(); usleep(10000);
    }
    /* Drain bytes already in the pipe after the child exited. */
    while (used < capacity-1) { ssize_t n = read(p[0], output+used, capacity-1-used); if (n <= 0) break; used += n; }
    output[used] = 0; close(p[0]);
    return WIFEXITED(s) ? WEXITSTATUS(s) : 128 + WTERMSIG(s);
}
static void rx(const char *host, unsigned port, const char *interface) {
    unsigned char buffer[65536];
    while (running()) {
        if (paused()) { state = "paused"; rest(.1); continue; }
        state = "connecting";
        int net = socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
        if (net < 0) { fault = 1; return; }
        struct sockaddr_in address = {.sin_family=AF_INET, .sin_port=htons(port)};
        if (inet_pton(AF_INET, host, &address.sin_addr) != 1) { close(net); fault = 1; return; }
        int connected = !connect(net, (struct sockaddr *)&address, sizeof(address));
        double until = now()+2;
        while (!connected && running() && now() < until) {
            struct pollfd fd = {net, POLLOUT, 0};
            if (poll(&fd, 1, 50) > 0) {
                int error=0; socklen_t length=sizeof(error);
                if (!getsockopt(net, SOL_SOCKET, SO_ERROR, &error, &length) && !error) connected=1;
                else break;
            }
        }
        if (!connected || !running()) { close(net); ++failures; state="backoff"; rest(failures<5 ? (1u<<failures) : 30); continue; }
        int p[2];
        if (pipe2(p, O_CLOEXEC)) { close(net); fault=1; return; }
        ++generation;
        char logname[64], seconds[32];
        snprintf(logname, sizeof(logname), "capture-%u.json", generation%4);
        snprintf(seconds, sizeof(seconds), "%u", (unsigned)(deadline-now())+1);
        pid_t pid = fork();
        if (pid == 0) {
            int error = open(logname, O_WRONLY|O_CREAT|O_TRUNC, 0600);
            dup2(p[1], 1); if(error>=0) { dup2(error, 2); close(error); }
            close(p[0]); close(p[1]); close(net);
            execl("./capture-metadata-stream", "./capture-metadata-stream", interface, "-", seconds, "4000000", (char *)0);
            _exit(127);
        }
        close(p[1]);
        if (pid < 0) { close(p[0]); close(net); fault=1; return; }
        FILE *identity=fopen("capture.pid","w");
        if(identity){fprintf(identity,"%d\n",pid);fclose(identity);}
        fcntl(p[0], F_SETFL, O_NONBLOCK);
        state="streaming"; event("connected fresh capture");
        size_t begin=0, end=0; int eof=0; double progress=now(), connection_started=now();
        while (running() && !paused()) {
            struct pollfd fds[2]={{p[0], end==begin ? POLLIN : 0, 0},{net, POLLIN|(end>begin ? POLLOUT : 0),0}};
            poll(fds,2,50);
            if (fds[1].revents&(POLLERR|POLLHUP|POLLNVAL)) break;
            if (fds[1].revents&POLLIN) break; /* FIN or unexpected reverse payload */
            if (end==begin && fds[0].revents&(POLLIN|POLLHUP)) {
                ssize_t n=read(p[0],buffer,sizeof(buffer));
                if(n>0) {begin=0;end=n;progress=now();}
                else if(!n) eof=1;
                else if(errno!=EAGAIN&&errno!=EINTR) break;
            }
            if (end>begin) {
                ssize_t n=send(net,buffer+begin,end-begin,MSG_NOSIGNAL);
                if(n>0) {begin+=n;forwarded+=n;progress=now();}
                else if(n<0&&errno!=EAGAIN&&errno!=EINTR) break;
                if(now()-progress>.5) {event("TCP backlog discarded");break;}
            }
            if(eof&&end==begin) break;
        }
        close(p[0]); close(net); last_exit=reap(pid,1);
        if (now()-connection_started>5) failures=0;
        ++failures; state="backoff"; event("capture generation ended");
        if(last_exit==2||last_exit==3||last_exit==127) {fault=1;return;}
        rest(failures<5 ? (1u<<failures) : 30);
    }
}
static int decode(const char *text, uint32_t words[12]) {
    unsigned char data[48]; size_t count=0; unsigned bits=0, value=0;
    const char *alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    for(const char *p=text;*p;++p) {
        if(*p=='\n'||*p=='\r'||*p==' ') continue;
        const char *at=strchr(alphabet,*p); if(!at||count==48) return -1;
        value=(value<<6)|(unsigned)(at-alphabet); bits+=6;
        if(bits>=8) {bits-=8;data[count++]=(unsigned char)(value>>bits);}
    }
    if(count!=48||bits) return -1;
    for(unsigned i=0;i<12;++i) words[i]=(uint32_t)data[4*i]|((uint32_t)data[4*i+1]<<8)|((uint32_t)data[4*i+2]<<16)|((uint32_t)data[4*i+3]<<24);
    return words[0]==0x3158544e&&words[11]==1 ? 0 : -1;
}
static int tx_command(const char *operation, char *result, size_t capacity) {
    char *argv[]={"./nexutil","-Ieth6",(char *)operation,"-l48","-R",NULL};
    if(operation[1]=='s') argv[3]=NULL;
    return command(argv,result,capacity,3);
}
static void tx(void) {
    char params[2048], output[4096];
    FILE *f=fopen("run.params","r");
    if(!f||!fgets(params,sizeof(params),f)) {if(f)fclose(f);fault=1;return;}
    fclose(f);params[strcspn(params,"\r\n")]=0;
    char *argv[]={"./nexutil","-Ieth6","-s429","-b","-l64","-v",params,NULL};
    while(running()) {
        state="transmitting"; ++generation;
        /* 432 frees the firmware context; each finite job needs fresh 429. */
        last_exit=command(argv,output,sizeof(output),3);
        if(last_exit) {fault=1;break;}
        last_exit=tx_command("-s430",output,sizeof(output));
        if(last_exit) {fault=1;break;}
        double started=now(); int finished=0;
        while(running()&&now()-started<65) {
            rest(.25);
            last_exit=tx_command("-g433",output,sizeof(output));
            uint32_t words[12];
            char name[64];snprintf(name,sizeof(name),"tx-%u.status",generation%4);
            FILE *status_file=fopen(name,"w");if(status_file){fputs(output,status_file);fclose(status_file);}
            if(last_exit||decode(output,words)||words[6]) {event("TX status failed; raw status retained");fault=1;break;}
            if(!words[1]) {if(words[4]>0&&!words[3]){++completed;finished=1;}else fault=1;break;}
        }
        last_exit=tx_command("-s432",output,sizeof(output));
        if(last_exit) fault=1;
        event("finite TX job ended");
        if(fault||(!finished&&running())) {fault=1;break;}
    }
    /* Also stop a finite radio job when the guard's own budget expires. */
    last_exit=tx_command("-s432",output,sizeof(output));
    if(last_exit) fault=1;
}
int main(int argc,char **argv) {
    if(argc!=7||(strcmp(argv[1],"rx")&&strcmp(argv[1],"tx"))) {
        fprintf(stderr,"usage: router_guard rx|tx RAM_DIRECTORY SECONDS HOST PORT INTERFACE\n");return 2;
    }
    unsigned seconds=(unsigned)strtoul(argv[3],NULL,10),port=(unsigned)strtoul(argv[5],NULL,10);
    if(!seconds||seconds>3300||!port||port>65535||chdir(argv[2])||!exists("armed")||exists("restored")) return 2;
    int marker=open("source.attempt",O_WRONLY|O_CREAT|O_EXCL,0600);if(marker<0)return 2;close(marker);
    pid_t pid=fork();if(pid<0)return 3;if(pid){printf("{\"guard_pid\":%d,\"detached\":true}\n",pid);return 0;}
    if(setsid()<0)return 3;
    int nil=open("/dev/null",O_RDWR);dup2(nil,0);dup2(nil,1);dup2(nil,2);if(nil>2)close(nil);
    signal(SIGTERM,stop_handler);signal(SIGINT,stop_handler);signal(SIGHUP,SIG_IGN);signal(SIGPIPE,SIG_IGN);
    began=now();deadline=began+seconds;
    FILE *f=fopen("guard.pid","w");if(f){fprintf(f,"%d\n",getpid());fclose(f);}
    if(!strcmp(argv[1],"rx"))rx(argv[4],port,argv[6]);else tx();
    state="restoring";next_state=0;status();event("source finished; restoring stock runtime");
    char output[4096];char *restore[]={"/bin/sh","restore.sh",NULL};
    int restored=command(restore,output,sizeof(output),60);
    f=fopen("guard-restore.log","w");if(f){fputs(output,f);fclose(f);}
    last_exit=restored;state=restored?"restore_failed":"stopped";next_state=0;status();
    f=fopen("guard-final.json","w");
    if(f){fprintf(f,"{\"guard_fault\":%d,\"restore_exit\":%d,\"generations\":%u,\"completed_TX_jobs\":%u,\"bytes\":%llu}\n",fault,restored,generation,completed,forwarded);fclose(f);}
    return fault||restored ? 1:0;
}
