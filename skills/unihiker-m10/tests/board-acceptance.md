# 实板验收记录

日期：2026-11-27（控制电脑日期）。授权目标：一块 USB 直连、使用自定义地址的 M10。控制端为 Windows + Python + PuTTY，主机指纹固定。记录不保存地址、截图或登录凭据。

| 软件/硬件状态 | 实测 |
|---|---|
| 产品镜像 | `/opt/unihiker/Version` 为 `v0.4.2`，Debian 10 Buster，aarch64，glibc 2.28；设备树显示 `Radxa ROCK Pi S`。 |
| Python | `/usr/bin/python3` 为 3.7.3；pyenv 2.5.7，安装 3.8.5、3.12.7；SSH 当时活跃 3.12.7。该解释器下 `unihiker` 0.0.30.1、PinPong 0.6.2、Pygame 2.6.1、ttkbootstrap 1.20.1、Flask 3.1.2；未探测到 Qt/PySide 或 pywebview。 |
| 屏幕 | Xorg `:0`，`xdpyinfo` 为 240×320；有 `ffmpeg x11grab`、`libX11`、`libXtst`。 |
| 网络 | USB 成员 `usb0`/`usb1` 位于 `br0`；`nmcli` 可读，测试时 WLAN 未连接；板端本地 Web `/pc/network-setting` 返回 HTTP 200。 |

## 已执行

- `ssh check`、`status`、`wifi status`、`python list`：真实 SSH 与读取正常；错误主机指纹被拒绝；未改网络和 Home 配置。
- 指定 Python 3.8.5 和 `system`（实测 3.7.3）运行临时脚本，解释器路径与脚本自身报告一致；前后 pyenv 默认选择保持为 3.12.7。板端助手的状态查询也以原生 Python 3.7.3 通过。
- `screen shot`：真实回传两张 240×320、可解码且非空白的 PNG。板载 Home 网络页由图片检查确认；临时 Tk 预览截图包含预期背景，退出后恢复原屏。临时截图与测试文件不纳入 Skill。
- `screen pointer/move/click/key`：移动坐标回读一致，受控预览应用收到 `click 120 160`、`key a` 事件；测试退出后恢复初始光标位置。
- `hw api`：静态查到 `pinpong.extension.unihiker` 的 `light` 和 `pinpong.board.DHT11`，不执行传感器示例。板载光敏返回有效原始值，A 键返回未按；灯完成一轮写入及熄灭指令，**没有现场目视确认灯态**。
- `calibration-guide`：确认设备有 `ts_calibrate` 并返回 Home 菜单路径；未写触屏配置、未校准、未重启。

## 未覆盖

macOS/Linux 主机及各 Harness 的真机运行、旧产品镜像和 Debian 12 BSP、Wi-Fi 实际写入、触屏物理校准、外接模块、Qt/WebKit、烧录。不能据 v0.4.2 的结果推断这些场景通过。

## 复测顺序

1. 确认具体板型、SSH 主机身份及操作者授权；先检查连接、环境、显示会话和当前程序。
2. 检查版本、单次解释器、截图（核对屏内内容，不只测文件存在与尺寸）。用一次性自有应用测试输入，确认事件收到并退出。
3. 用户确认没有其他应用占用时读板载传感器、闪灯。记录返回和物理观察的区别；不升级 PinPong 以使测试通过。
4. 删除本任务临时文件，确认 Home/全局 Python 不变。涉及改 Wi-Fi、触摸校准和固件升级的试验不进默认验收。
