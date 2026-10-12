"""User-requested pause: record existing evidence only; no new test or connection."""
import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2];t=root/'tools/pose-v1';e=t/'evidence/picture-20261010-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fresh(p,text):assert not p.exists();p.write_text(text,encoding='utf-8',newline='\n')
def prepend(p,text):
    old=p.read_text(encoding='utf-8');head,_,tail=old.partition('\n');p.write_text(head+'\n\n'+text.strip()+'\n\n'+tail.lstrip('\n'),encoding='utf-8',newline='\n')
refs=['build.acceptance.json','baseline.acceptance.json','contracts.acceptance.json','picture.failed-review.json','picture.objects.json','picture.counts.json','failure-host-comparison.json','failure-block-pattern.json','failure-late-sources.json','video-prefix-review/review.json','native-marked/review.json']
facts=dict(status='user_paused_picture_failed_at192_existing_evidence_reviewed',program_SHA256='7d421b40b9fbd50376347ff6283c83474c4857b305227e6d5bbee0495b1b59e9',manifest_SHA256='e7c4b944b124034c6758a0211563044647dad6cef448524da5665e71101adb98',payloads=403,build_sources=118,Native_ARM_contracts_each={'source':13,'sequence':13,'producer':16,'load':6,'run':9},Host107_new_run=False,Host107_identity_reused=107,correct_calls=20,attempted_calls=21,FP32_compared=302000,three_stage_correct=4,long_stage_correct=16,long_stage_not_passed=True,failed_invocation=20,failed_local_index=16,failed_frame=100020,failed_case='S23_30_330',failed_op=192,failed_index_changed_FP32=144,failed_index_noninteger=144,failed_index_nonfinite=0,failed_index_first_bad=3680,changed_ranges=8,all_changed_bytes_equal_same_invocation_previous_slot0_copy_same_offset=True,Host_owned_failed_inputs=3,Host_owned_failed_bytes=47760,device_late_reads=2,device_late_read_bytes=94080,all_four_late_slot_reads_bitwise_gold=True,late_reads_do_not_prove_source_at_copy_time=True,source_addresses=[109232128,109285376],failed_Host_destination_mod64=[32,0],public_object_rows=326,owned_shadow_rows=163,producer192_queries=168,all192_counts234=True,copy_metadata_rows=183,kernel_unchanged=True,VPU_first_capture=True,Engine_created=True,VPU_contexts=1,Engine_instances=1,published_pictures=20,adopted_pictures=20,overwritten=0,coalesced=0,queue_high_water=1,decoded_prefix_frames=392,captured_NoInput_frames=297,captured_real_frames=95,repeated_real_frames=75,unique_captured_real_sources=20,uncaptured_sample_tail=3,submitted_as_logged=395,input_returned_as_logged=394,VPU_return_struct_defaults_not_actual_counts=True,normal_drain_LAST=False,partial_stream_bytes=485017,NV12_files_compared=21,NV12_bytes_compared=29030400,marked_sample_diagnostic_hashes_checked=395,joint_visibility_checks=1330,both_abort_STREAMOFF_succeeded=True,worker_joined_before_Engine_release=True,persistence_tasks_saved=7,agent_compactions=1,compaction_ms=66.20272,ordinary_units_before_after_compaction=[9,16],ordinary_units_entry_raw_capture_first=[14,12,6,5],final_MemAvailable_KiB=745428,final_CmaFree_KiB=1604,final_ordinary_units=10,root_cause_fixed=False,VPU_or_render_cause_proven=False,drop_caches=False,reboot=False,CMA_BOOT_model_SDK_changed=False,normal_source_reads_added=0,all_agent_sessions_closed=True,services_running=False,active_tests=False,management_estimate=83,evidence_SHA256={name:sha(e/name) for name in refs},archive_SHA256={'contracts.tar':sha(e/'contracts.tar'),'picture.tar':sha(e/'picture.tar')})
fresh(e/'pause-progress-review.json',json.dumps(facts,indent=2)+'\n')
checkpoint=dict(status=facts['status'],user_paused=True,active_tests=False,services_running=False,SSH_SCP_closed=True,background_jobs=False,automatic_wakeup=False,package='.local/pose-v1-picture/package-20261010-r1',build='.local/pose-v1-build/mixed-20261010-picture-r1',board='/tmp/pose-picture-20261010-r1',program_SHA256=facts['program_SHA256'],manifest_SHA256=facts['manifest_SHA256'],pause_progress_review_SHA256=sha(e/'pause-progress-review.json'),failed_invocation=20,failed_op=192,correct_calls=20,compactions=1,resume='Wait for explicit user wakeup. Read RESUME-PICTURE-20261010.md, ADR_29 and this checkpoint. Do not rerun failed picture directory or resume at invocation21 on the stopped Engine. First local frozen identity/evidence review and minimal public-copy/read-path investigation; preserve CPU bad Host bytes and both late SDK reads. No new device tests/reset/cache/CMA/BOOT/model/SDK changes during pause. A new candidate and bounded hardware plan are needed to test a transfer-path change; stable real-picture103/5Hz/long-term/HDMI/RTSP/zero-copy remain pending.')
fresh(e/'pause-checkpoint.json',json.dumps(checkpoint,indent=2)+'\n');(e/'active-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8',newline='\n')
fresh(t/'RESUME-PICTURE-20261010.md','''# 真实拥有画面阶段：用户暂停恢复入口

2026-10-10，用户明确要求记录进度并暂停，等待唤醒。所有板测、回传、Native参考／解码审查已结束，无后台程序或代理连接；暂停期间不构建、连接、板测或自动唤醒。

## 已完成与未通过

隔离picture-r1程序7d421b40…b1b59e9／manifest e7c4b944…01adb98，403载荷118来源。单VPU实际capture→主线程单Engine，真实最高分骨架与拥有NV12、容量2源、10fps编码／2Hz三窗→103入口已实现。Native／ARM各画面13、阶段13、计数16、生命周期6、Run9拒绝过；旧主／常驻入口／模型／数学／SDK／BOOT保持，Host107／12注册59600仅冻结身份复用。

一次新目录运行：前三窗＋重复4次正确，随后103阶段前16次正确，合20前向302000FP32逐位旧参考。第21次inv20／local16／frame100020／S23_30_330，在GatherElements192索引非有限整数检查退出1，103没有通过，未重跑。

## 当前故障证据

保存3个CPU拥有输入47760字节。188.slot0与192.slot0逐位同CSI旧中间参考；192.slot1有144个有限但非整数索引，首3680，8坏段起点mod256均128，全部坏段等于同次、紧邻此前192.slot0复制的相同偏移字节，并非“上一帧”已证。两轮稍后真实PL DDR源读取94080字节，两slot四读取均逐位正确；晚于原复制，不能证明复制瞬间源或具体写入者。

326对象／163shadow稳定，168查询全234、183复制元数据；真实192源109232128／109285376合法不重叠，Host目标mod64分别32／0、FP32对齐合法。计数234不是DMA/cache fence，坏indices目标已64对齐，不以等待234／64对齐当修复。此次2Hz也复现，不能把问题限定为5Hz请求频率；真实绘图、NV12复制、写盘与堆／时序同时变化，不直接归罪渲染或VPU。

## 画面与清理

20画面全部发布／采用，队列水位1、覆盖／合并0。21份NV12（含NoInput）29030400字节逐位Native冻结渲染一致；395采样标记诊断hash一致。已捕获392图像：297NoInput＋95真实图像（20新来源／75重复），实际PTS、ID、1330关节及来源前缀过；3采样未捕获，485017字节部分H264保留，不记正常drain／LAST或完整视频验收。VPU summary submitted/returned为异常返回前默认0，不当实际计数；日志395输入queued／394归还。两abort STREAMOFF返回0、worker join后Engine释放、七项独立保存成功；内核无新增变化。

一次规整66.20272ms普通9→16；编码进入14→raw12→capture6→首次5，首次启动成功。最终MemAvailable745428KiB／CmaFree1604／普通10是释放后现场，不证明泄漏或永久可靠。无清缓存、重启、CMA／BOOT／SDK变化。

## 唤醒后的顺序

1. 读[暂停检查点](evidence/picture-20261010-r1/pause-checkpoint.json)和[进度证据](evidence/picture-20261010-r1/pause-progress-review.json)，核验冻结包／程序和已有失败。旧运行及失败数据不覆盖，不从停止的Engine继续inv21。
2. 完成本机公共SDK搬运路径审计：当前输入桥是`dst.copyFrom(0,src,0,bytes)`，晚源路径是`Tensor::read`。它们共享设备区域入口但目标与时刻不同，不能假定改API即修复。下一最小候选可评估公开read直接写入自有Host CPTR，保持dtype／范围／wait／CPU数学与输出写回，先明确actual API签名、所有权和测试边界；不猜ADDR映射、cache helper或寄存器。
3. 提出新身份／新目录的最小单路径变更与Host／三窗／有界长序列门检，再执行新验证；当前仅记录恢复建议，未写入该修复或新板测。保留异常Host暂存及两晚源，不放宽非整数、有限性或完整候选门禁。

稳定真实画面103、持续5Hz／长期、HDMI／在线RTSP、安全连续申请和零拷贝仍待；管理粗估83/100保持。

证据：[数值失败审查](evidence/picture-20261010-r1/picture.failed-review.json)、[Host对照](evidence/picture-20261010-r1/failure-host-comparison.json)、[坏段](evidence/picture-20261010-r1/failure-block-pattern.json)、[两晚源](evidence/picture-20261010-r1/failure-late-sources.json)、[视频前缀](evidence/picture-20261010-r1/video-prefix-review/review.json)、[样片拼图](evidence/picture-20261010-r1/video-prefix-review/contact-sheet.png)、[ADR_29](../../ADR/ADR_29.md)。
''')
summary='真实拥有画面picture-r1已实现、构建及Native／ARM五组契约通过；一次硬件首次VPU启动成功，单上下文三窗4＋长阶段16共20前向302000FP32正确，第21次inv20／S23_30_330／192索引144有限非整数／8坏段失败，完整103未过。坏段同次前一slot0复制同偏移，两轮PL DDR源94080字节正确，对象稳定／168计数234；具体瞬时复制责任未证。20画面采用、21NV12逐位Native、392解码前缀／20来源／实际PTS／1330关节过，3采样未捕获，不记正常drain／LAST。异常原文及3输入47760／两晚源保留；两abort STREAMOFF／join／七项保存／原内核同，全部程序／连接结束。一规整66.20272ms普通9→16，最终745428KiB／CmaFree1604／普通10仅现场，无清缓存／重启／CMA／BOOT变化。根因未修，83/100保持。'
links='[恢复入口](tools/pose-v1/RESUME-PICTURE-20261010.md)／[ADR_29](ADR/ADR_29.md)／[暂停点](tools/pose-v1/evidence/picture-20261010-r1/pause-checkpoint.json)。'
prepend(root/'Done.md','## 2026-10-10：真实拥有画面前缀验证与用户暂停\n\n### 工程内容总结\n\n'+summary+'\n\n### 对后续开发的参考\n\n用户明确暂停，等待唤醒；只归档既有证据，不继续构建／连接／测试。2Hz真实画面条件也复现192残留，不能归因只在5Hz发生、单纯候选颠倒或首次VPU分配失败。后续先审计公开copyFrom与read路径及Host目标所有权，保留旧失败，不自动继续停止的Engine或重跑目录。'+links+'以下当前为历史。')
prepend(root/'Agents.md','- 用户主动暂停真实拥有画面任务（2026-10-10）：'+summary+' 当前整个任务暂停，停止构建／连接／板测／后台／自动唤醒，等待用户明确恢复。7d421b40…b1b59e9／manifest e7c4b944…01adb98，403包118来源；旧主和单次常驻保持。恢复先读RESUME-PICTURE-20261010、ADR_29及picture-20261010-r1 pause-checkpoint；不重跑旧失败或接续inv21，先本机身份和公共搬运路径审查。旧“当前已完成”仅前阶段历史。')
prepend(root/'PROJECT-PROGRESS.md','## 当前：用户暂停，真实画面20正确后192坏值复现\n\n'+summary+'\n\n首版全流程已贯通，当前仍在并发数值可靠性定位；真实画面103、长期／5Hz与视频终版未验收。管理粗估83/100是工程估算，不是通过率。'+links+'暂停期间不连接或新测试。以下当前为历史。')
prepend(root/'DIFFICULTIES.md','2026-10-10当前：[ADR_29](ADR/ADR_29.md)真实拥有画面2Hz条件inv20的192残留复现：144非整数／8段同此前slot0字节，两晚源正确，对象／计数稳定；20正确输出与视频前缀已核验，root未修。用户要求暂停，[恢复入口](tools/pose-v1/RESUME-PICTURE-20261010.md)。以下当前为历史。')
prepend(root/'ADR/README.md','2026-10-10当前：[ADR_29](ADR_29.md)新增真实拥有画面决策及192坏值复发证据；Native／ARM过，20前向和视频前缀过，103未过。用户明确暂停，下一仅读恢复点并审计公共搬运路径，[入口](../tools/pose-v1/RESUME-PICTURE-20261010.md)。以下当前为历史。')
prepend(t/'README.md','> 2026-10-10当前：真实拥有画面已实现，20正确前向后192坏值复发，103未过；用户明确暂停，全部服务／连接结束。[恢复入口](RESUME-PICTURE-20261010.md)／[暂停点](evidence/picture-20261010-r1/pause-checkpoint.json)。以下当前为历史。')
adr=root/'ADR/ADR_29.md';text=adr.read_text(encoding='utf-8').replace('状态：用户已批准；结果待验证。','状态：Native／ARM及20结果前缀通过，103在192坏值复发而未过；用户暂停。')
text+='\n\n## 实际结果与暂停（2026-10-10）\n\n'+summary+'\n\n21次尝试中只有20完整返回；144坏索引无NaN／Inf，但非整数，首3680，7段64字节＋1段128字节，起点mod256皆128。所有坏段等于同次192.slot0复制同偏移，非“上一帧”身份已证。坏idx的Host目标mod64=0，另一数据目标32，合法不重叠；两晚源正确只证明晚时刻，计数234不证明DMA/cache fence。NV12、渲染、堆和文件缓存改变条件，不能把复现当渲染或VPU因果证明。\n\nNative／ARM各13画面＋13阶段＋16计数＋6生命周期＋9 Run拒绝过，旧主／数学／SDK／BOOT保持，Host107身份复用。父主线程Engine全程同实例，Source容量2水位1、发布20／采用20／覆盖0。395输入queued、394归还、393非空packet（1参数集＋392图像），3采样未capture；异常结束无LAST，EncodeResult字段默认0不当真实计数。\n\n本机坏段工具首次误用--review而实际需--gold-review，已只修正工具调用，保留情况；未板测重跑或改数据／阈值。用户此时要求暂停，尚未进行公开read直写Host目标候选修复。\n\n[完整恢复说明](../tools/pose-v1/RESUME-PICTURE-20261010.md)／[已核进度](../tools/pose-v1/evidence/picture-20261010-r1/pause-progress-review.json)／[暂停点](../tools/pose-v1/evidence/picture-20261010-r1/pause-checkpoint.json)。\n'
adr.write_text(text,encoding='utf-8',newline='\n')
print('User pause recorded; no new connection, build, test, or automation.')
