# 快捷指令

从 Skill 根目录运行：`python scripts/host/m10.py --host BOARD_IP --user BOARD_USER [--host-key VERIFIED_SHA256] <命令>`。全局 SSH 参数要放在子命令前。`BOARD_IP` 等是占位值；`discover-key` 和 `ssh tcp` 可以省略 `--user`。Windows 下建议用 PowerShell；用 Git Bash 调用 Windows Python 时，给含板端绝对路径的命令加 `MSYS2_ARG_CONV_EXCL='*'`，以免 Git Bash 转换 Linux 路径。认证和跨平台前置条件见 [SSH](ssh.md)。

| 命令 | 行为/限制 |
|---|---|
| `discover-key` | 列出明确指定目标的未验证指纹，不登录，不自动添加信任。 |
| `ssh tcp` / `ssh check` | 测试端口 / 测试登录与远程运行。都不是板型识别。 |
| `status` | 系统、Python、Home 开关、网络和屏幕工具状态，只读；不初始化 PinPong。 |
| `ssh run 'uname -m'` | 显式板端 shell 命令，默认 15 秒；可在命令文本前加 `--seconds`（1–120）。执行前确认命令的副作用。 |
| `python list` | 当前、系统和 pyenv 的版本及选项。 |
| `python run --version 3.12.7 /absolute/path/app.py` | 已上传 `.py` 单次运行；`--seconds` 等选项放路径前，路径后的参数传给脚本。验证结果包含版本、实际解释器路径及标准输出。 |
| `wifi status` | `nmcli` 与 IPv4 接口状态，不自动扫描或配网。 |
| `screen shot --output ./new.png` | 真实板载 X11 PNG，仅新路径；输出路径、大小、分辨率。 |
| `screen pointer` | 读取 X11 光标坐标和屏幕大小。 |
| `screen move 120 160 --confirm` | 移动，并验证读回的 X11 坐标。 |
| `screen click 120 160 --confirm` | 已核实画面后向 X11 发送一次左键点击。 |
| `screen key a --confirm` | 已核实焦点后发送单个直接映射 keysym。 |
| `calibration-guide` | 查询校准工具与 Home 菜单路径，不触发校准。 |
| `hw api DHT11 --version 3.12.7` | 静态查板端库。找不到返回 `found: false`，不要凭记忆补 API。 |
| `hw read light --version 3.12.7 --confirm` | 使用已审阅的 PinPong，允许 `light` / `button-a` / `button-b`。 |
| `hw blink --count 3 --version 3.12.7 --confirm` | 板载 L 灯 1–5 次；结束发熄灯指令，不保证已目视验证。 |

- 显示命令支持 `--display :0`，换号前确认是物理板载 X11 会话。输入命令先核实已获授权且焦点正确；一次只做一个事件。
- 通常输出一行 JSON，`ok: false` + `error` 表示出错，CLI 退出非零；参数错误走 argparse。看具体字段，不把 `authenticated`、`event_sent`、`off_command_sent` 当成业务验收。`wifi status` 还需看 `nmcli_status_read`；`status` 里的 `null` 是未取得，不是版本 0。
- 无 GUI、旧系统或 PinPong 构建未审阅，相关工具明确报错；见对应参考页，不自动加包或修改配置。Wi-Fi 连接、触屏校准和固件操作使用人工确认路径，不封装成无交互快捷指令。
