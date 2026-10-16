# 原厂 Vivado＋JFM／Procise 路径二审查结果

2026-10-16，Windows，工作目录D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1。用户批准审查原厂混合路径并更新超时规则；同配置IP重建授权继续有效。原参考工程297份逐项SHA恢复到隔离目录；只复制工程和必要JFM资料，没有复制Vivado工具目录。本机2018.3沿用上一批030ai九项补丁，本批无新增安装写入。

## 实际执行与通过标准

| 阶段 | 实际用时/退出 | 结果与范围 |
|---|---|---|
| 原厂参数/DRC定义查询 | 10.400216秒/0 | 正常加载原厂受保护过程，只读查询四项DRC |
| 原始工程状态 | 16.263756秒/0 | 28项IP未锁定，无修订升级；缓存/OOC属性分别核对 |
| 隔离hook配置预览 | 13.030318秒/1 | add_hook已返回；驱动错误调用save_project导致17-163，原失败保留 |
| 独立重开/后处理预览 | 9.376277秒/0 | 六项hook实际落盘；29份XCI/BD SHA当时不变；exec被拦截，无输出bit |
| Procise命令查询 | 0.290259秒/0 | 存在increment_bit_cfg_v3及BOOT命令；无实际输入位流处理 |
| 同配置MIG OOC | 262.133509秒/0 | 实际DCP、完整日志和资源报告生成；XCI非运行时配置/DDR PRJ字节通过 |
| MIG后原厂前置检查 | 9.815504秒/0 | pre_patch_check返回0，没有执行顶层hook或位流生成 |

阶段原始结果与命令分别在对应目录的execution.json、stage.tcl/build.tcl、stdout/stderr/vivado.log；MIG完整子运行日志、utilization及实际DCP均已保存。通过依据为真实退出码、产物及配置契约，脚本准备或工具stdout提示不替代执行。

## 保留的错误和自主超时判断

[配置驱动首次原值](hook-preview/)的save_project错误不是超时。原add_hook未重跑；修正未来驱动后仅独立重开确认绑定，修正版本并未重新执行。首次[前置检查](post-command-preview/post-command-preview.txt)报告MIG缺少OOC，随后单独完成原配置MIG综合，[再次原厂门检](precheck-after-mig/precheck.txt)通过；不回写首次失败。

MIG初始180秒门限到达时仍有新日志、未见ERROR，按用户新规则有界延至360秒，继续原进程至262.133509秒成功，没有重启或重复负载。[预算判断](mig-ooc/timeout-decisions.json)、[进程祖先链](process-ancestry-snapshot.json)、[资源快照](runtime-resource-snapshot.json)保留。资源快照的direct-path owned_by_this_batch布尔值只是初筛，不能识别相对路径子进程；后续祖先链证实四个Vivado进程均属本批。MIG最终exit0，未触发最终超时终止；历史超时记录不改。

前提及停止条件：只运行同配置MIG OOC，maxThreads=2、jobs=1；门限到达依据进展决定继续，预算上界540秒，实际只调整一次至360秒。无进展、错误或资源问题停止并取证；确认的参数/身份变化、OOM/逻辑故障不因新超时授权而放行。最终EDA进程盘点为空，无板端连接或后台工作。

## 实现职责与尚待确定的构建配置

实际链路为原始2018.3 IP/OOC→Vivado＋JFM实现/bit→30TAI专用ICAP的Procise后处理→核对后的BOOT打包。通用PS7→PCPU7导入旧失败不再作为该链路必经步骤，但保留其全部证据。

[32项全局IP库只读清单](IP-library-readonly-inventory.json)的源/目标均存在且32项全部不同。-xfft_modify默认TRUE并非只改FFT，还含本工程确有的counter，故审查用FALSE不代表已证明可省略。HARC安装与原厂源同SHA并跳过复制；-change_speed审查用FALSE。REQP-44/46/52/56实际均启用、Error级，针对GTHE2/GTXE2的GTGREFCLK；生成的未来脚本有关闭分支，但本批未执行，不是HDMI时序/CDC豁免。

实际ICAP分支device=0按xc7z030推导JFMQL30TAI676H；[原厂生成命令](post-command-preview/procise_run_disable_icap.tcl)保留，exec在[预览日志](post-command-preview/post-command-preview.txt)中明确SUPPRESSED。没有生成_disable_icap.bit，厂商“runs success”不能算真实后处理通过。原工程根不存在procise_incr_cfg.txt，不套包中的K325流水灯示例。

原脚本引擎5.3.1.8与包标签5.3.2.1_100AI_LV分别记录；没有据此擅自换包。BOOT_Gen五份输入[SHA/ELF身份](BOOT-Gen-input-identities.json)及[参考bit头](factory-reference-bit-header.json)已保存，不等同现用BOOT分区身份，原BIF旧路径与apu_x32文本未自行改动。

## 交付、限制与恢复

[参数、影响及正式构建范围](../../../../FPGA/hdmi_candidate/ROUTE2-AUDIT.md)已明确。32项全局IP库替换及4项GT规则处理需要确定具体范围后才能采用正式配置；本批不将审查授权扩展为额外库替换或DRC豁免。尚无顶层完整位流、STA/CDC或实屏验收；BOOT/SDK/模型/PS/AI_Mate不改，旧DATA继续暂停，无下载或重启。

原始297份参考、9份扫描RTL、2019九项目标、既有2018补丁及其余备份目标状态复核通过，见baseline-review.json。Agents已落实超时自主判断，保留取证、原值、范围控制和其它故障停止要求。文档修改前后SHA独立记录，Agents快照隐去认证口令，原文SHA与脱敏快照SHA分开；历史完成清单不回写。所有新证据另作SHA封存。
