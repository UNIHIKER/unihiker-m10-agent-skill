---
name: unihiker-m10
description: >-
  UNIHIKER 官方维护的行空板 M10（UNIHIKER M10）操作技能。
  只要用户要操作行空板 M10，就可以调用此 Skill。
  例如开发行空板M10上的程序、通过 SSH 连接、查看状态和版本、选择 Python、运行程序、配置网络、操作屏幕和截图、控制板载硬件或排查故障。
license: MIT
metadata:
  publisher: UNIHIKER
  repository: https://github.com/UNIHIKER/unihiker-m10-agent-skill
  repository-backup: https://gitee.com/unihiker/unihiker-m10-agent-skill
---

# UNIHIKER M10

M10 是运行 Linux 和完整 Python 的单板电脑。直接经 SSH 操作，不需要 Mind+，也不用把 Agent 安装在板上。此 Skill 提供文档和脚本，不能授予网络、USB 或 SSH 权限。

## 首次使用：检查 Skill 更新

每次 Agent 会话首次使用此 Skill 时，在开始任务前从控制电脑运行一次 `python scripts/host/check_update.py`（必要时用 `python3` 或脚本的绝对路径）。不要在 M10 板端运行，也不要对后续每条命令重复检查。

只有脚本报出新版时，才简短告知用户当前版本、可用版本和 GitHub Releases 地址，然后继续原任务。无输出、无法联网、缺少运行权限或检查失败时，直接继续，不提醒、不重试。只提示，不下载或安装更新，不接触 M10 的系统或依赖版本。

## 默认流程

1. **明确任务和目标。** 用户问方法时只说明；请求操作时，确认是 M10、地址、SSH 账号和主机身份。官方典型 USB 地址是 `10.1.2.3`，但板子可以改过地址，不得覆盖用户指定值。局域网或多板环境不要猜板子、扫描其他主机或试密码。
2. **先只读检查。** 从能实际连接板子的电脑运行 `scripts/host/m10.py`，先 `ssh check`，再 `status`。设备树显示 `Radxa ROCK Pi S` 在已验证的产品镜像上是正常现象，但单凭这个字符串不能认定型号。遇到 BSP 或定制镜像，按实际能力判断，勿套用产品镜像的账号、目录和显示条件。
3. **用已核实的步骤。** 操作前只读相关参考页；优先用现有快捷工具。应用任务若已安装并满足依赖，优先选择 Python `3.12.7` 单次运行，不改变全局选择。判断硬件 API 时，先用 `hw api` 核对当前解释器里的库。判断屏幕时，区分板载真实截图、远程桌面和离屏渲染。
4. **验证并报告。** 返回目标、动作实际结果和证据；例如截图路径和分辨率、真正运行的 Python 路径、光敏原始值。LED 命令成功不代表目视确认，X11 显示服务器接收输入也不代表应用响应。超时先核对状态，不盲目重试带副作用的动作。

## 操作边界

- `--confirm` 只能用于用户已授权且目标、坐标/动作、设备占用已确认的操作；不是自动批准。点击或按键前读当前截图、确认窗口焦点；不要自动点击重启、校准或权限提示。不把键盘接口用于输入密码。
- `/opt/unihiker` 只读。不写 Home 配置、系统目录或用户现有项目；试验应用使用独立目录、有时限，只清理本次创建的文件和进程。不要全局结束 Python 程序。
- 默认不改 Wi-Fi、不改 `pyenv global`、不安装/升级依赖、不校准、不重启、不重刷系统或协处理器。分别说明影响、恢复方法，按用户的明确授权执行。不要关闭 SSH 主机密钥校验，也不要从资料猜密码。
- PinPong 状态读取与硬件初始化是两回事。`status` / `hw api` 不导入 PinPong；`hw read` / `hw blink` 只允许已审阅的 PinPong 构建。外接 I/O 先确认模块、引脚、电平、供电和安全状态。

## 按任务查阅

- [快捷指令与参数](references/commands.md) · [SSH 与文件传输](references/ssh.md) · [Wi-Fi 与热点](references/wifi.md)
- [板型与版本](references/board-and-versions.md) · [Python 选择与依赖安装](references/python.md)
- [显示、截图、键鼠和触屏校准](references/screen.md) · [PinPong 与硬件](references/hardware.md)
- [排障与恢复](references/troubleshooting.md) · [官方资料与证据分级](references/sources.md)
- [使用示例](examples/README.md) · [实板验收范围](tests/board-acceptance.md)
