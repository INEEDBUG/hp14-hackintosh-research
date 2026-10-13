# HP14 Hackintosh Research

HP14 / Intel Ice Lake / macOS Sequoia 的公开研发记录：原生 Wi-Fi、睡眠唤醒与 AirDrop。包含脱敏项目经历、可复现的源码补丁、离线测试和构建工具。

**项目仍在进行。当前发布是实验源码与证据，尚没有通过实机验收的 Wi-Fi 稳定性修复、睡眠修复或双向 AirDrop。**

English: An evidence-driven HP14 Hackintosh research log with experimental Intel Wi-Fi patches and offline tests. Physical Wi-Fi stability, macOS sleep/wake and bidirectional AirDrop remain unresolved.

## 测试环境

| 项目 | 基线 |
| --- | --- |
| 机器 | HP14，Intel Ice Lake，x86_64 |
| 无线 PCI | `8086:34F0`，Subsystem `8086:0264` |
| 蓝牙 USB | `8087:0AAA` |
| macOS | Sequoia 15.8.1 / Build 24H32 / Darwin 24.6.0 |
| 无线软件 | 从 itlwm + HeliPort 迁移至 AirportItlwm 原生界面候选 |
| Wi-Fi 源码基线 | [laobamac/itlwm @ f26a3af](https://github.com/laobamac/itlwm/tree/f26a3afc8a0eecd6995ebdba48498f36bac107ad) |
| 电源条件 | 用户报告未安装电池，测试时持续接交流电源 |

PCI ID 记录来自本机证据，不据此把无线硬件直接归类为 AX210，也不外推其他网卡的成功案例。

## 当前结果

| 能力 | 已有证据 | 状态 / 边界 |
| --- | --- | --- |
| 启动、内屏、物理光标和触控板 | 用户多次确认可见桌面及输入正常 | 稳定基线保留 |
| 原生 Wi-Fi 基础功能 | 系统界面扫描、连接、开关后重连和指定接口流量曾通过 | 基础烟测通过，日用稳定性未通过 |
| 原生 Wi-Fi 稳定性 | 控制中心跨路由器切换失败、扫描慢、偶发断开后重连 | OPEN；当前最高优先级 |
| Apple ID / FaceTime | 用户完成登录并确认正常 | 用户登录验收通过；不代表所有连续互通功能通过 |
| Linux 深度睡眠对照 | 用户按普通键后内屏及命令行恢复 | 本机对照通过 |
| macOS 完整睡眠 | 系统 / SSH 恢复但内屏黑屏 | FAIL；尚未修复 |
| AirPlay 接收 | 用户报告 iPhone 控制中心屏幕镜像能显示 | 用户报告通过；实际承载链路未确认 |
| Finder 原生 AirDrop | 可发现自己的 iPhone，发送持续等待；反向发现 / 传输未通过 | FAIL；双向传输未完成 |
| iPhone Mirroring 应用 | HP14 不满足 Apple silicon / T2 官方硬件要求 | 不作为当前驱动修复的验收目标 |

## 本次实质性进展：Wi-Fi 源码修正

2026-10-13 的离线工作复现并修正了扫描结果游标的三类问题：枚举结束后新扫描被拒绝、部分枚举污染下一次扫描、缓存释放后继续使用旧节点指针；同时修正速率数组填充顺序及边界。

- 原始 8 项实际函数测试：3 通过、5 失败，其中两项触发 AddressSanitizer 的释放后使用报告。
- 当前 14 项测试：全部通过，启用 AddressSanitizer / UndefinedBehaviorSanitizer。
- 73 个实际源文件编译完成，完整实验 kext 链接成功，未安装或加载。
- 为 WCL 扫描、关联、取消、断开和驱动重置增加默认关闭的数值诊断，帮助区分实际调用路径与首次断开原因。

这些结果证明了隔离测试中的缺陷与修正；尚未证明 Sequoia 界面调用的是这条扫描路径，更未证明三个实机症状都已解决。自动掉线的原因仍为 UNKNOWN。

入口：[Wi-Fi 修正说明](docs/wifi-stability.md) · [复现与构建](docs/reproduce.md) · [测试证据](evidence/wifi-tests-20261013.json) · [构建证据](evidence/wifi-build-20261013.json)

## 项目经历与后续

- [研发经历与决策](docs/project-history.md)
- [睡眠问题与 Linux 对照](docs/sleep-wake.md)
- [AirDrop / AWDL 与镜像功能边界](docs/airdrop.md)
- [验收条件](docs/acceptance.md)
- [隐私与发布流程](docs/publication.md)

每次经过验证的实质性里程碑都会更新对应源码、测试、证据和状态，并提交至本仓库。失败实验也记录结果和回退，不用“编译成功”替代“功能修好”。本仓库不配置定时轮询或自动部署。

## 开源与归属

本仓库自有代码、补丁和文档采用 [GPL-2.0-only](LICENSE)。上游版权及第三方许可证保留，见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。不包含 Apple 系统二进制、私有日志、设备身份或完整个人 EFI。

设备所有者负责现场操作、授权与账号验收；Codex 协助研究、实现和离线验证。上游驱动与协议实现归各自作者，本仓库不宣称其为原创。
