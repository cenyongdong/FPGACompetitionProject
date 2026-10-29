# 源码已按模块归位

原 `board/` 的运行时、公共类型和测试已迁到 [../src/](../src/README.md) 与 [../tests/](../tests/README.md)。正式入口是 `src/app/main.cpp`，严格链入口是 `src/app/strict_main.cpp`，SDK 在 `src/inference/`。此目录只保留旧入口指引；部署包中的 `board/` 布局不受影响。
