"""进程内高分辨率等待；不修改系统定时器、频率或电源配置。"""
import sys, time

count=int(sys.argv[1]); hz=float(sys.argv[2]); epoch=time.perf_counter_ns()+200_000_000
for i in range(count):
    deadline=epoch+round(i*1e9/hz)
    while True:
        left=deadline-time.perf_counter_ns()
        if left<=0: break
        if left>1_500_000: time.sleep((left-1_000_000)/1e9)
    # 父进程收到tick后，在自己的单调时钟域标记实际CSI发送时刻。
    print(i,flush=True)
