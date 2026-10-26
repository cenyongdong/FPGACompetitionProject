/* Own-router RAM-only supervisor. No persistent radio config, no board SDK.
 * RX: one bounded TCP buffer, fresh capture per connection, finite backoff.
 * TX: finite jobs for legacy runs; tx.lease selects one locally renewed task.
 */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <float.h>
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
#include "tx_lease_protocol.h"

static volatile sig_atomic_t stop_requested;
static double began, deadline, paused_until, next_state;
static unsigned generation, failures, completed;
static unsigned tx_renewals, tx_renewal_failures;
static const char *tx_stop_reason = "none";
static unsigned long long forwarded;
static const char *state = "starting";
static int last_exit, fault;
static int continuous;
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
    FILE *f = fopen("lease.tmp", "w");
    if (f) { fprintf(f, "%u\n", (unsigned)t); if (!fclose(f)) rename("lease.tmp", "lease"); }
    f = fopen("guard-status.tmp", "w");
    if (f) {
        fprintf(f, "{\"pid\":%d,\"state\":\"%s\",\"elapsed\":%.3f,\"generation\":%u,\"failures\":%u,\"completed_TX_jobs\":%u,\"forwarded_bytes\":%llu,\"last_exit\":%d,\"fault\":%d,\"TX_renewals\":%u,\"TX_renewal_failures\":%u,\"TX_stop_reason\":\"%s\"}\n",
                getpid(), state, t-began, generation, failures, completed, forwarded, last_exit, fault,
                tx_renewals,tx_renewal_failures,tx_stop_reason);
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
        snprintf(seconds, sizeof(seconds), "%u", continuous ? 0 : (unsigned)(deadline-now())+1);
        pid_t pid = fork();
        if (pid == 0) {
            int error = open(logname, O_WRONLY|O_CREAT|O_TRUNC, 0600);
            dup2(p[1], 1); if(error>=0) { dup2(error, 2); close(error); }
            close(p[0]); close(p[1]); close(net);
            execl("./capture-metadata-stream", "./capture-metadata-stream", interface, "-", seconds, continuous ? "0" : "4000000", (char *)0);
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
/* Only the wait gets shorter. A fresh, valid 433 completion is still required
 * before 432/free and the next finite 429/430 job. In absolute mode words[2]
 * is Hz and words[3] is remaining slots (submitted OR skipped by firmware).
 * The 32-bit enqueue TSF counters are diagnostics, never a host start trigger.
 */
static double tx_poll_interval(const uint32_t words[12]) {
    return (words[2]==50 || words[2]==300) && words[3]<=words[2]/2 ? .02 : .25;
}
static void tx_wait(double seconds) {
    double until=now()+seconds;
    while(running()) {
        double left=until-now();
        if(left<=0) break;
        if(left>.01) left=.01;
        struct timespec delay={0,(long)(left*1e9)};
        nanosleep(&delay,NULL);
    }
}
/* The native lease status is 32 bytes, including one base64 padding byte.
 * Decode words explicitly: router and test-host byte order need not match.
 */
static int decode_lease(const char *text,uint32_t words[8]) {
    unsigned char data[32];unsigned bits=0,value=0;size_t count=0,padding=0;
    const char *alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    for(const char *p=text;*p;++p) {
        if(*p=='\n'||*p=='\r'||*p==' ') continue;
        if(*p=='=') {++padding;continue;}
        const char *at=strchr(alphabet,*p);
        if(!at||padding) return -1;
        value=(value<<6)|(unsigned)(at-alphabet);bits+=6;
        if(bits>=8) {bits-=8;if(count==sizeof(data))return -1;data[count++]=(unsigned char)(value>>bits);}
    }
    if(count!=32||padding!=1||bits!=2||(value&3))return -1;
    for(unsigned i=0;i<8;++i) words[i]=(uint32_t)data[4*i]|((uint32_t)data[4*i+1]<<8)|((uint32_t)data[4*i+2]<<16)|((uint32_t)data[4*i+3]<<24);
    return words[0]==PIW_TX_LEASE_MAGIC&&words[1]==PIW_TX_LEASE_VERSION&&words[2] ? 0:-1;
}
static int tx_lease_status(uint32_t words[8],char output[4096]) {
    char *argv[]={"./nexutil","-Ieth6","-g435","-l32","-R",NULL};
    last_exit=command(argv,output,4096,3);
    FILE *f=fopen("tx-lease.status","w");if(f){fputs(output,f);fclose(f);}
    if(last_exit)return -1;
    if(decode_lease(output,words))return -2;
    return 0;
}
static int tx_lease_renew(uint32_t token,uint32_t sequence,char output[4096]) {
    const char *alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    uint32_t words[3]={PIW_TX_LEASE_MAGIC,token,sequence};unsigned char bytes[12];char encoded[17];
    for(unsigned i=0;i<12;++i)bytes[i]=(unsigned char)(words[i/4]>>(8*(i%4)));
    for(unsigned i=0,o=0;i<12;i+=3) {
        unsigned v=((unsigned)bytes[i]<<16)|((unsigned)bytes[i+1]<<8)|bytes[i+2];
        encoded[o++]=alphabet[(v>>18)&63];encoded[o++]=alphabet[(v>>12)&63];
        encoded[o++]=alphabet[(v>>6)&63];encoded[o++]=alphabet[v&63];
    }
    encoded[16]=0;
    char *argv[]={"./nexutil","-Ieth6","-s434","-b","-l12","-v",encoded,NULL};
    last_exit=command(argv,output,4096,3);return last_exit;
}
static const char *tx_guard_stop_reason(void) {
    if(stop_requested)return "guard_signal";
    if(now()>=deadline)return "guard_deadline";
    if(exists("stop.request"))return "stop_request";
    if(exists("restored"))return "already_restored";
    return "guard_disarmed";
}
static void tx_leased(char *const configure[]) {
    char output[4096];uint32_t lease[8]={0},native[12]={0};
    uint32_t token=0,sequence=0;unsigned queries=0,diagnostics=0;
    int stopped=0,freed=0,configure_attempted=0;
    const char *reason="guard_stop";
    if(!running())return;
    state="transmitting";++generation;configure_attempted=1;
    last_exit=command(configure,output,sizeof(output),3);
    if(last_exit){fault=1;reason="configure_failed";goto cleanup;}
    if(tx_lease_status(lease,output)){fault=1;reason="lease_config_status_invalid";goto cleanup;}
    token=lease[2];
    if(lease[3]||lease[5]||lease[6]||lease[7]){fault=1;reason="lease_config_state_invalid";goto cleanup;}
    if(!running()){reason=tx_guard_stop_reason();goto cleanup;}
    last_exit=tx_command("-s430",output,sizeof(output));
    if(last_exit){fault=1;reason="start_failed";goto cleanup;}
    event("TX lease started: one context; local renewal every 10s; 60s lease");
    double next_renew=now()+PIW_TX_LEASE_RENEW_SECONDS,next_probe=now(),next_diagnostic=now();
    while(running()) {
        if(paused()){reason="pause_requested";break;}
        double t=now();
        if(t>=next_renew) {
            /* No retry: a timed-out ioctl may have reached firmware. Stop and
             * inspect rather than resubmitting or creating a second context.
             */
            if(sequence==UINT32_MAX){fault=1;reason="renew_sequence_exhausted";break;}
            ++sequence;
            if(tx_lease_renew(token,sequence,output)){++tx_renewal_failures;fault=1;reason="renew_command_failed";break;}
            if(tx_lease_status(lease,output)){++tx_renewal_failures;fault=1;reason="renew_status_invalid";break;}
            ++queries;
            if(lease[2]!=token||lease[3]!=sequence||lease[7]!=sequence){++tx_renewal_failures;fault=1;reason="renew_identity_mismatch";break;}
            if(!lease[4]||!lease[5]||lease[6]){++tx_renewal_failures;fault=1;reason="renew_not_running";break;}
            ++tx_renewals;next_renew=now()+PIW_TX_LEASE_RENEW_SECONDS;next_probe=now()+1;
        }
        if(t>=next_probe) {
            if(tx_lease_status(lease,output)){fault=1;reason="lease_status_invalid";break;}
            ++queries;
            if(lease[2]!=token||lease[3]!=sequence||lease[7]!=sequence){fault=1;reason="lease_identity_mismatch";break;}
            if(lease[6]){fault=1;reason="firmware_error";break;}
            if(!lease[5]||!lease[4]){fault=1;reason="lease_expired_or_stopped";break;}
            next_probe=now()+1;
        }
        if(t>=next_diagnostic) {
            last_exit=tx_command("-g433",output,sizeof(output));++diagnostics;
            FILE *f=fopen("tx-0.status","w");if(f){fputs(output,f);fclose(f);}
            if(last_exit||decode(output,native)){fault=1;reason="status_invalid";break;}
            if(native[6]||!native[1]){fault=1;reason="firmware_error_or_stopped";break;}
            next_diagnostic=now()+10;
        }
        tx_wait(.05);
    }
    if(!fault&&!running())reason=tx_guard_stop_reason();
cleanup:
    tx_stop_reason=reason;
    /* Stop is independent of the userspace command timeout. A fresh matching
     * 435 must prove running=0 before freeing this context. On missing proof,
     * leave ownership to restore.sh's radio restoration, never double-free.
     */
    if(configure_attempted) {
        int original_exit=last_exit;
        int stop_exit=tx_command("-s431",output,sizeof(output));
        int query_exit=tx_lease_status(lease,output);
        stopped=!query_exit&&token&&lease[2]==token&&!lease[5];
        int free_exit=-1;
        if(stopped){
            free_exit=tx_command("-s432",output,sizeof(output));freed=!free_exit;
            if(freed){FILE *f=fopen("tx.released","w");if(f){fputs("1\n",f);fclose(f);}}
        }
        if(!stopped||!freed)fault=1;
        char detail[768];
        snprintf(detail,sizeof(detail),
                 "TX lease end reason=%s renewals=%u renewal_failures=%u lease_queries=%u diagnostics=%u submitted=%u skipped=%u task_exit=%d stop_exit=%d stop_proven=%d free_exit=%d",
                 reason,tx_renewals,tx_renewal_failures,queries,diagnostics,native[4],native[5],original_exit,stop_exit,stopped,free_exit);
        event(detail);
    }
}
static void tx(void) {
    char params[2048], output[4096];
    FILE *f=fopen("run.params","r");
    if(!f||!fgets(params,sizeof(params),f)) {if(f)fclose(f);fault=1;return;}
    fclose(f);params[strcspn(params,"\r\n")]=0;
    char *argv[]={"./nexutil","-Ieth6","-s429","-b","-l64","-v",params,NULL};
    if(exists("tx.lease")){tx_leased(argv);return;}
    double previous_done=0, previous_stop_ms=0;
    while(running()) {
        state="transmitting"; ++generation;
        double configured=now(), config_ms, start_ms=0, started=0;
        double observed_done=0, previous_poll=0, poll_gap_ms=0, max_query_ms=0;
        double interval=.25;
        unsigned polls=0, tail_polls=0;
        uint32_t words[12]={0};
        int finished=0, have_status=0;
        const char *reason="guard_stop";
        /* 432 frees the firmware context; each finite job needs fresh 429. */
        last_exit=command(argv,output,sizeof(output),3);
        config_ms=(now()-configured)*1000;
        if(last_exit) {fault=1;reason="configure_failed";}
        else if(running()) {
            double at=now();
            last_exit=tx_command("-s430",output,sizeof(output));
            started=now();start_ms=(started-at)*1000;
            if(last_exit) {fault=1;reason="start_failed";}
            else {
                char detail[512];
                snprintf(detail,sizeof(detail),
                         "TX start config_ms=%.3f start_ms=%.3f previous_stop_ms=%.3f completion_to_start_ms=%.3f",
                         config_ms,start_ms,previous_stop_ms,previous_done ? (started-previous_done)*1000 : -1.0);
                event(detail);
            }
        }
        while(!fault&&started&&running()&&now()-started<65) {
            tx_wait(interval);
            if(!running()) break;
            double query=now();
            last_exit=tx_command("-g433",output,sizeof(output));
            double observed=now(), query_ms=(observed-query)*1000;
            ++polls;if(interval<.25) ++tail_polls;
            if(query_ms>max_query_ms) max_query_ms=query_ms;
            poll_gap_ms=previous_poll ? (observed-previous_poll)*1000 : (observed-started)*1000;
            previous_poll=observed;
            char name[64];snprintf(name,sizeof(name),"tx-%u.status",generation%4);
            FILE *status_file=fopen(name,"w");if(status_file){fputs(output,status_file);fclose(status_file);}
            have_status=0;memset(words,0,sizeof(words));
            if(last_exit) {reason="status_command_failed";fault=1;break;}
            if(decode(output,words)) {reason="status_invalid";fault=1;break;}
            have_status=1;
            if(words[6]) {reason="firmware_error";fault=1;break;}
            if(!words[1]) {
                if(words[4]>0&&!words[3]) {++completed;finished=1;observed_done=observed;reason="completed";}
                else {reason="incomplete_status";fault=1;}
                break;
            }
            interval=tx_poll_interval(words);
        }
        if(!fault&&!finished&&running()) {reason="job_timeout";fault=1;}
        if(fault) event("TX job failed; latest raw status retained");
        /* One cleanup attempt per configured/partially configured context.
         * Real 432 reports an error when no context exists: never issue it a
         * second time merely because the outer guard is now finishing.
         */
        int job_exit=last_exit;
        double stopping=now();
        last_exit=tx_command("-s432",output,sizeof(output));
        double stop_ms=(now()-stopping)*1000;
        if(last_exit) fault=1;
        char detail[1024];
        snprintf(detail,sizeof(detail),
                 "TX end reason=%s job_exit=%d stop_exit=%d config_ms=%.3f start_ms=%.3f stop_ms=%.3f active_ms=%.3f polls=%u tail_polls=%u last_poll_gap_ms=%.3f max_query_ms=%.3f status_valid=%d remaining=%u submitted=%u skipped=%u firmware_error=%u enqueue_age_us=%u",
                 reason,job_exit,last_exit,config_ms,start_ms,stop_ms,started ? (stopping-started)*1000 : 0.0,
                 polls,tail_polls,poll_gap_ms,max_query_ms,have_status,words[3],words[4],words[5],words[6],
                 have_status&&words[4] ? (uint32_t)(words[10]-words[9]) : 0);
        event(detail);
        if(fault||!finished) break;
        previous_done=observed_done;previous_stop_ms=stop_ms;
    }
}
int main(int argc,char **argv) {
    if(argc!=7||(strcmp(argv[1],"rx")&&strcmp(argv[1],"tx"))) {
        fprintf(stderr,"usage: router_guard rx|tx RAM_DIRECTORY SECONDS HOST PORT INTERFACE\n");return 2;
    }
    unsigned seconds=(unsigned)strtoul(argv[3],NULL,10),port=(unsigned)strtoul(argv[5],NULL,10);
    if(seconds>3300||!port||port>65535||chdir(argv[2])||!exists("armed")||exists("restored")) return 2;
    /* Zero is an explicit persistent-service mode, never an accidental empty
     * or invalid finite budget. TX still has its independent 60-second lease. */
    continuous=!strcmp(argv[3],"0")&&exists("continuous");
    if(!seconds&&(!continuous||(!strcmp(argv[1],"tx")&&!exists("tx.lease")))) return 2;
    int marker=open("source.attempt",O_WRONLY|O_CREAT|O_EXCL,0600);if(marker<0)return 2;close(marker);
    pid_t pid=fork();if(pid<0)return 3;if(pid){printf("{\"guard_pid\":%d,\"detached\":true}\n",pid);return 0;}
    if(setsid()<0)return 3;
    int nil=open("/dev/null",O_RDWR);dup2(nil,0);dup2(nil,1);dup2(nil,2);if(nil>2)close(nil);
    signal(SIGTERM,stop_handler);signal(SIGINT,stop_handler);signal(SIGHUP,SIG_IGN);signal(SIGPIPE,SIG_IGN);
    began=now();deadline=continuous?DBL_MAX:began+seconds;
    FILE *f=fopen("guard.pid","w");if(f){fprintf(f,"%d\n",getpid());fclose(f);}
    if(!strcmp(argv[1],"rx"))rx(argv[4],port,argv[6]);else tx();
    state="restoring";next_state=0;status();event("source finished; restoring stock runtime");
    char output[4096];char *restore[]={"/bin/sh","restore.sh",NULL};
    int restored=command(restore,output,sizeof(output),60);
    f=fopen("guard-restore.log","w");if(f){fputs(output,f);fclose(f);}
    last_exit=restored;state=restored?"restore_failed":"stopped";next_state=0;status();
    f=fopen("guard-final.json","w");
    if(f){fprintf(f,"{\"guard_fault\":%d,\"restore_exit\":%d,\"generations\":%u,\"completed_TX_jobs\":%u,\"bytes\":%llu,\"TX_renewals\":%u,\"TX_renewal_failures\":%u,\"TX_stop_reason\":\"%s\"}\n",fault,restored,generation,completed,forwarded,tx_renewals,tx_renewal_failures,tx_stop_reason);fclose(f);}
    return fault||restored ? 1:0;
}
