"""Archive bounded contract evidence and exact remaining gaps; no execution."""
from pathlib import Path
import json,hashlib,ast
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-contract-20261011-r2';assert not (E/'completion-review.json').exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
data=json.loads((E/'data-review.json').read_text())
def insert(path,body):
    p=R/path;s=p.read_text(encoding='utf-8');head,tail=s.split('\n',1);p.write_text(head+'\n\n'+body.strip()+'\n'+tail,encoding='utf-8',newline='\n')
insert('Done.md','''## 2026-10-11：生产者检查路径、零指令Cast及官方部署映射核验

### 工程内容总结

匹配ZG／XRT二进制与六ARM／Windows头文件审查完成；Tensor检查函数以layerCount≥阈值判定，并有条件区域内memcpy／PL→PL DMA路径，实际触发与DDR完成保证仍未证明。XIR-only e51ea127…da1d47在ARM通过三视图，无RAW／Device／Session；8629／8631是零指令零层Cast，保留19成员组为11层、223＋11＝234，输入486和带填充FP16的478、含Matmul真实参数，独立参考未闭合。

官方apply/log入口复用36冻结对象，原CPU／桥／模型／RAW／SDK／BOOT保持；r2 8576af7f…5e1bbe7 exit0，两日志已有；r3 97641b15…40864be新增门检误预期1而SDK实际2，exit1原错保留，均无forward／VPU。两官方日志418328／56218字节已核验，8467/4386共址109232128，8479/4390共址109285376，均is_ocm=false、与旧失败相同。12注册／七ZG组／真实参数通过，原Gather保持，无新Host107／FP32验收。

首次rg查找受Git忽略影响，我误判r2日志不存在并推断目录问题；原档案证明已有文件，推断撤回。r3普通文件流目录契约不构成官方日志故障证据。两文件门检已修正并编译r4 7ec4e3cc…2e27b78，未传输／板测，不改原exit1或再跑设备。FPAI codegen头缺失、ISO/GNU宏、冻结旧头告警及传输前路径／清单假设修正均保留。

### 对后续开发的参考

软件检查路径存在条件搬运；逻辑Cast不等于真实计算生产者，官方映射也不等于失败瞬间私有输入映射。下一先通过公开SDK仅读原RAW，闭合19成员真实参数／FP16布局／NumPy参考；不闭合则不执行独立组。必要时准备只透传公开UDMA同步属性写调用的有界观察，板端无strace，本轮未安装。原异常读取／门禁保持，根因未修；全连接／程序关闭，规整0／内核同，最终MemAvailable751964／CmaFree37600KiB仅现场，83/100／103／严格5Hz／长期／HDMI待。[结果](tools/pose-v1/PRODUCER-CONTRACT-RESULTS-20261011.md)／[ADR_37](ADR/ADR_37.md)／[下一](tools/pose-v1/PRODUCER-CONTRACT-NEXT-20261011.md)／[恢复](tools/pose-v1/evidence/producer-contract-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
insert('PROJECT-PROGRESS.md','''## 当前：SDK检查与部署映射更明确，真实生产者参考／硬件完成契约待闭合

本轮完成六匹配头与后端检查路径审查、ARM XIR-only三视图和官方apply/log映射；没有NPU前向／视频或新增数值验收。8629／8631为零指令Cast，原组19成员11层，检查器有计数达标后条件copy；实际触发／DDR保证未证。官方数据与索引地址同旧失败，均非OCM。

r2 apply/log exit0；r3误预期一日志而实际两份导致门禁exit1，数据完整、原错保留。误判日志缺失源于Git过滤，目录故障推断撤回。纠正r4仅编译；无硬件重跑。当前仍处于首版全链后的并发数据可靠性定位，管理83/100不变（非通过率／工期），103／严格5Hz／长期／HDMI待；全部连接与程序结束、规整0、内核同。

[结果](tools/pose-v1/PRODUCER-CONTRACT-RESULTS-20261011.md)／[ADR_37](ADR/ADR_37.md)／[下一](tools/pose-v1/PRODUCER-CONTRACT-NEXT-20261011.md)／[当前恢复点](tools/pose-v1/evidence/producer-contract-20261011-r2/next-checkpoint.json)。以下当前为历史。
''')
insert('Agents.md','''- 生产者契约本轮结束（2026-10-11）：用户批准AXI-READ-NEXT，ADR_37。六匹配ARM/Windows头和ZG/XRT完整符号核验；检查器layerCount≥阈值后有条件区域copy/PL→PL DMA，实际触发及DDR完成未证。XIR-only e51ea127…da1d47在ARM三视图过、无RAW/Device/Session；8629/8631为零指令零层Cast，原9186组19成员11层/223＋11＝234、输入486及带填充FP16的478，独立参考未闭合，未独立NPU测试。官方apply/log复用36冻结对象，r2 8576af7f…5e1bbe7 exit0已有两日志；r3 97641b15…40864be错预期1而实际2、exit1，均无forward/VPU。两日志418328/56218字节核验，8467/4386共址109232128，8479/4390共址109285376，均非OCM、同旧失败。首次rg受Git忽略误判r2日志缺失，目录缺陷推断撤回；普通流目录契约不证明官方log故障。两文件门检修正r4 7ec4e3cc…2e27b78仅编译未板测，不伪改exit1/重跑。12注册/原七组/参数通过，CPU/Gather/桥/模型/RAW/SDK/BOOT保持，Host107引用前批不重跑。FPAI头缺失/ISO宏/旧头告警/传输前路径清单错误与修正留存。全内核同、规整0、进程端口/SSH/SCP全结束；最终MemAvailable751964/CmaFree37600KiB仅现场。现读PRODUCER-CONTRACT-RESULTS/NEXT、ADR_37及producer-contract-20261011-r2 completion/next-checkpoint。下一先公开RAW仅读、实际19成员参数/布局/NumPy参考闭合，再考虑只透传公开UDMA属性的有界观察；无现成strace/未安装、无新动态观察。根因未修，原异常读取保留，83/100/完整103/严格5Hz/长期/HDMI待。以下当前为历史。''')
for path in ('DIFFICULTIES.md','REFERENCES.md','ToDoLists.md'):
    insert(path,'2026-10-11最新：[ADR_37](ADR/ADR_37.md)记录生产者检查器条件copy、零指令Cast、19成员参考缺口、官方部署映射与日志门检/误检索修正。[结果](tools/pose-v1/PRODUCER-CONTRACT-RESULTS-20261011.md)／[下一](tools/pose-v1/PRODUCER-CONTRACT-NEXT-20261011.md)／[数据核验](tools/pose-v1/evidence/producer-contract-20261011-r2/data-review.json)／[恢复](tools/pose-v1/evidence/producer-contract-20261011-r2/next-checkpoint.json)。无模型前向，新根因未修；r3 exit1为一/两日志数量错误，原码/数据保留，r4仅编译。全部会话结束，以下当前为历史。')
insert('ADR/README.md','最新：[ADR_37](ADR_37.md)生产者完成契约、零指令Cast与官方日志核验。确认条件copy与非OCM部署地址，实际触发/DDR语义未证；[结果](../tools/pose-v1/PRODUCER-CONTRACT-RESULTS-20261011.md)／[下一](../tools/pose-v1/PRODUCER-CONTRACT-NEXT-20261011.md)。以下当前为历史。')
insert('tools/pose-v1/README.md','> 2026-10-11最新：[生产者契约／官方日志结果](PRODUCER-CONTRACT-RESULTS-20261011.md)已归档；零指令Cast不能单独做NPU实验，19成员参考尚未闭合。官方地址同旧失败且非OCM；r3日志数量门禁exit1原错保留，r4仅编译，无模型前向/新数值验收。原异常读取保持，根因未修，程序/连接关闭。[ADR_37](../../ADR/ADR_37.md)／[下一](PRODUCER-CONTRACT-NEXT-20261011.md)／[恢复](evidence/producer-contract-20261011-r2/next-checkpoint.json)。以下当前为历史。')
docs=['Agents.md','Done.md','PROJECT-PROGRESS.md','DIFFICULTIES.md','REFERENCES.md','ToDoLists.md','ADR/ADR_37.md','ADR/README.md','tools/pose-v1/README.md','tools/pose-v1/PRODUCER-CONTRACT-RESULTS-20261011.md','tools/pose-v1/PRODUCER-CONTRACT-NEXT-20261011.md']
for p,h in data['archives_sha256'].items():assert sha(E/p)==h
for buildtag in ('producer-view-20261011-r2','producer-deployment-20261011-r2','producer-deployment-20261011-r3','producer-deployment-20261011-r4'):
    b=json.loads((R/('.local/pose-v1-build/'+buildtag+'/build-result.json')).read_text())
    if 'frozen_sources_sha256' in b:
        for p,h in b['frozen_sources_sha256'].items():
            if p.startswith('software/'):assert sha(R/p)==h
for p in (R/'tools/pose-v1').glob('*producer*py'):ast.parse(p.read_text(encoding='utf-8-sig'))
c={'status':'bounded_producer_contract_audit_finished_root_unresolved','date':'2026-10-11','data_review_sha256':sha(E/'data-review.json'),'audit_identity_sha256':sha(E/'audit.identity.json'),'offline_ARM_passed':True,'offline_Device_opened':False,'apply_r2_exit':0,'apply_r3_exit':1,'r3_log_gate_error_preserved':True,'official_logs_each_apply':2,'official_log_bytes':[418328,56218],'NPU_forward':False,'VPU_streaming':False,'new_numerical_FP32_validation':0,'Host107_new_run':False,'root_fixed':False,'DDR_completion_proven':False,'all_programs_ports_connections_closed':True,'kernel_unchanged':True,'compactions':0,'strace_available':False,'management_estimate':83,'estimate_is_not_acceptance_rate':True,'initial_missing_log_claim_retracted':True,'corrected_log_gate_compiled_not_executed':True,'documents_sha256':{p:sha(R/p) for p in docs},'scripts_sha256':{p.name:sha(p) for p in (R/'tools/pose-v1').glob('*producer*py')},'sources_sha256':{p.name:sha(p) for p in (R/'software/pose_v1/src').glob('producer_*audit.cpp')},'current_corrected_entry_sha256':sha(R/'software/pose_v1/src/producer_deployment_log.cpp'),'failed_r3_entry_sha256':data['failed_r3_source_sha256'],'build_result_sha256':{tag:sha(R/('.local/pose-v1-build/'+tag+'/build-result.json')) for tag in ('producer-view-20261011-r2','producer-deployment-20261011-r2','producer-deployment-20261011-r3','producer-deployment-20261011-r4')},'build_failures_sha256':{tag:sha(R/('.local/pose-v1-build/'+tag+'/build.log')) for tag in ('producer-view-20261011-r1','producer-deployment-20261011-r1')},'static_function_windows_sha256':{p.name:sha(p) for p in E.glob('*.stdout')}}
(E/'completion-review.json').write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8',newline='\n')
n={'status':c['status'],'user_paused':False,'active_tests':False,'services_running':False,'SSH_SCP_closed':True,'root_fixed':False,'completion_sha256':sha(E/'completion-review.json'),'board_offline':'/tmp/pose-producer-contract-20261011-r2','board_apply':'/tmp/pose-producer-deployment-20261011-r3','corrected_gate_build':'.local/pose-v1-build/producer-deployment-20261011-r4','corrected_gate_executed':False,'next':'Read PRODUCER-CONTRACT-RESULTS/NEXT and ADR_37. Zero-instruction Cast producers cannot supply NPU computation; full19-member view needs exact parameters/FP16 layout/reference closure. First public RAW-only extraction and independent reference design, no graph/math/SDK/BOOT change. Conditional ready-copy actual use and DDR guarantee unproven; keep original failure snapshots/late reads. No new dynamic observer or dependency installed; strace unavailable. r3 exit1 is log-count gate error, both logs valid, no hardware rerun for corrected gate. Strict5Hz/103/long-term/HDMI pending.'}
(E/'next-checkpoint.json').write_text(json.dumps(n,indent=2)+'\n',encoding='utf-8',newline='\n');print('Current completion',sha(E/'completion-review.json'))
