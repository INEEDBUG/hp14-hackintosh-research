# AirDrop、AWDL 与两种镜像

本机 Finder 可发现自己的 iPhone，但发送文件持续等待，iPhone 到 Mac 的发现及文件传输未通过。双向原生 AirDrop 仍未完成。

## 分层判断

| 层 | 当前判断 |
| --- | --- |
| 普通原生 Wi-Fi | 基础连接通过，稳定性存在待修问题 |
| 发现设备 | Finder 发现本人的 iPhone；不证明文件通道成立 |
| AWDL 接口与链路 | 未建立满足本机双向传输验收的证据 |
| AirDrop 协议及文件内容 | 发送等待，双向内容校验未通过 |

普通 AP 连接、蓝牙发现、AirPlay 接收和 AWDL 文件通道不能互相替代。

## 已阅读的可复用方向

- [OpenIntelWireless FAQ](https://openintelwireless.github.io/itlwm/FAQ.html)：用于区分普通网络与连续互通支持范围。
- [itlwm Issue #1047](https://github.com/OpenIntelWireless/itlwm/issues/1047)：发送侧与网络栈刷新经验，尚非本机复现或双向修复证明。
- [laobamac/itlwm 固定基线](https://github.com/laobamac/itlwm/tree/f26a3afc8a0eecd6995ebdba48498f36bac107ad)：Sequoia WCL 原生 Wi-Fi 方向；不能据此承诺 AWDL。
- [seemoo-lab/owl](https://github.com/seemoo-lab/owl)：开源 AWDL 实现和协议参考。现有离线测试记录为 52 项通过；并不建立本机 macOS monitor / injection 能力。
- [seemoo-lab/opendrop](https://github.com/seemoo-lab/opendrop)：AirDrop 协议实现；依赖下层连接能力。
- [t4t5/omdrop-owl](https://github.com/t4t5/omdrop-owl) 与 [omdrop-plugin PR #25](https://github.com/brentkearney/omdrop-plugin/pull/25)：Linux / Windows 等环境的新线索，适配性需按接口、硬件和目标界面核验，不能由演示标题推出 Finder 原生双向成功。

这里列的是已有研究来源，不声称本次发布重新测试了全部外部项目，也未捆绑这些实现。相关项目各自许可证不因列入参考而改变。

## 两种镜像

用户报告 iPhone 控制中心“屏幕镜像”能在 Mac 上显示，这是 AirPlay 接收的功能证据，实际承载链路尚未确认。

Dock 中 iPhone Mirroring 应用用于交互控制。[Apple 官方要求](https://support.apple.com/en-us/120421)包括 Apple silicon 或 T2 芯片；HP14 不满足这一硬件条件。不能把应用连接失败直接归因于距离或 Wi-Fi，也不能从 AirPlay 成功推断 AirDrop 成功。

优先稳定普通 Wi-Fi，再安排独立的原生 AirDrop 双向测试；不让协议实验干扰睡眠或日用网络验收。
