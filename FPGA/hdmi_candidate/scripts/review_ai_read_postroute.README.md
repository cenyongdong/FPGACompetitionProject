# r6独立正式报告门

Windows工作目录`D:/FPGACompetitionProject`。`review_ai_read_postroute.py --check-only`只核冻结源码与11处精确AST身份适配；无参数时只读实际r6报告，不运行EDA、上板或加入豁免。

保留r5审查器SHA48a150…0053c全文不动，仅按明确line／column／old／new清单调整r6阶段、native身份和common输出别名。完整反向AST须与原源相同；base `__file__`及其`review_driver_SHA256`仍如实指向旧算法，另记录实际新adapter、base、转换表、编译AST与SHA。先独立核r6物理profile与原值链，再复用全部原STA／DRC／CDC／来源算法；只有所有旧门真实通过才生成`common-routed-review.json`。最终`review.json`另行独占写入实际优化链、adapter／contract／common结果SHA，失败不生成放行文件。

纯共享门`ai_read_postroute_contract.py`固定9a71988…e99d4归档driver的公开纯函数及原r5 driver ee11b668…1504b，核同r4固定physopt、937源／41库profile。实际顺序只能是原NoTimingRelaxation route、一次`-placement_opt -routing_opt -rewire -critical_pin_opt`、首次完整原厂JFM route_post、原checkpoint及报告。三边界完整route-status报告须routable=fully且errors0，配对原值必须`ROUTED_FULLY|1`／`ERRORS_IN_ROUTES|0`；实际Tcl必须包含完整优化块，且只有这两个物理命令、一次完整JFM source，不允许额外route／retime／place。逐phase完整源码SHA与自有owner核同；允许bit启用源码版本不同，但四个公开优化函数AST必须与冻结9a相同。

`hardware_change:false`继承字段仅表达RTL／外部接口未改；r6 canonical profile明确`physical_implementation_change:true`。现r5正式setup拒绝保留；r6任何新setup／hold／DRC错误继续拒绝，不套旧两个AI例外。bit仍需实际正式门通过。

bit／packager另用`ai_read_postroute_release.py`核11字段实际release对象：formal／common／adapter／contract SHA、完整优化链和AST转换、真实factory／default DRC profile，input-proof与bit-identity须完全相同，不丢弃未知字段。源码依赖由新planner逐次固定SHA核验并纳入local_review；动态现场暂停状态不纳固定哈希。

本组`E3/postroute-r6-adapters-r1/mock-r5`55项纯mock通过、3.141秒。保留r1的AST父节点拒绝及r3测试异常类型处理失败，未记通过。此证据不证明实际r6 STA、bit或板测通过；本组没有启动EDA、SDK、SSH或串口。
