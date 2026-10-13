# 离线复现与构建

这些步骤在隔离源码目录内执行，不加载 kext、不修改 EFI、不控制无线硬件。需要 macOS、现有 Command Line Tools、Python 3、Git；内核构建还需要现有 MacKernelSDK。上游推荐的正式构建方式仍是对应 Xcode scheme，本仓库的 CLT 工具是实验构建路径。

## 获取精确基线并应用补丁

在本仓库根目录执行，`work/itlwm` 必须是新建的隔离 checkout：

```sh
git clone --filter=blob:none https://github.com/laobamac/itlwm.git work/itlwm
git -C work/itlwm checkout --detach f26a3afc8a0eecd6995ebdba48498f36bac107ad
git -C work/itlwm apply --check ../../patches/wifi/0001-scan-cursor-and-numeric-diagnostics.patch
git -C work/itlwm apply ../../patches/wifi/0001-scan-cursor-and-numeric-diagnostics.patch
```

源码许可证、版权头及原始第三方声明保留在上游 checkout。不得把此步骤用于含有其他未提交改动的日用源码目录。

## 运行实际函数测试

```sh
python3 tests/hp14/run_scan_tests.py work/itlwm build/scan-tests
```

测试 runner 将实际生产函数提取到临时编译单元，使用 ASAN / UBSAN；fixture 中的网络数据是虚构的。检查 `build/scan-tests/result.json`，当前预期 14 项通过。该结果不验证内核 ABI 或无线硬件。

## 完整实验 kext 构建

先单独准备 [MacKernelSDK](https://github.com/acidanthera/MacKernelSDK) 的固定提交 `3f750085caa17ec3a7880f11c11bf4f48cd6a164`。工具不会安装 SDK 或 Xcode，也不会运行生成的驱动。

```sh
git clone https://github.com/acidanthera/MacKernelSDK.git work/MacKernelSDK
git -C work/MacKernelSDK checkout --detach 3f750085caa17ec3a7880f11c11bf4f48cd6a164
python3 tools/hp14/build_sequoia_clt.py work/itlwm build/sequoia-clt --sdk work/MacKernelSDK --diagnostics 1
```

构建器解析精确上游 Xcode 工程的 Sequoia 源文件列表，使用现有 CLT 编译、生成模块信息并链接。在编译阶段会嵌入上游 firmware；不执行 firmware、不刷写。上游工程中有一个空 source reference，构建回执会明确记录跳过它。

默认 `--diagnostics 0`。本仓库证据对应显式开启诊断的构建。构建生成器、完整编译日志及 bundle metadata 都应在本地检查；目前不提供二进制下载或自动安装流程。

构建输出含本地诊断路径，默认被 Git 忽略，不能把整个 `build/` 上传。公开结果只从白名单字段生成。不同工具链与环境不保证生成相同二进制 SHA；这里的哈希用于追溯已观察产物。
