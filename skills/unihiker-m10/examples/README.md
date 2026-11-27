# 使用示例

命令在 Skill 根目录运行。把 `BOARD_IP`、`BOARD_USER` 换成已确认的信息；以下简写使用已有可信 `known_hosts` 和 SSH 密钥，也可按 [SSH 指南](../references/ssh.md)给全局参数添加 `--host-key`。

## 「查看我的行空板版本，不要改设置」

```sh
python scripts/host/m10.py --host BOARD_IP --user BOARD_USER status
```

返回当前镜像/系统、运行解释器和包版本。若用户只是问「怎么看」，优先告诉他 Home → 查看系统信息，而不是连接板子。

## 「在板载屏预览这个项目，然后截图」

将 `screen_preview.py` 用 SFTP 上传到已授权的项目目录。确认当前 `DISPLAY` 后，以下是 v0.4.2 上 `:0` 的做法；命令中的路径替换为板端真实路径。

```sh
python scripts/host/m10.py --host BOARD_IP --user BOARD_USER ssh run --seconds 25 'DISPLAY=:0 PYENV_VERSION=3.12.7 pyenv exec python /absolute/path/screen_preview.py --seconds 15'
```

在另一个终端于显示期间执行 `screen shot`，结束后查看实际 PNG，不判断单靠运行退出状态：

```sh
python scripts/host/m10.py --host BOARD_IP --user BOARD_USER screen shot --output ./m10-preview-new.png
```

示例只依赖板端 Tk，时间到自行退出。不提供显示会话时先解释无法显示，不启动虚拟桌面代替验屏。

## 「用 3.12 跑一次，不改默认 Python」

先 `python list`，再 `python run --version 3.12.7 /absolute/path/app.py`。报告实际解释器。若依赖缺失，核对是否漏传项目文件，不自动装同名包。

## 「这个 DHT11 怎么导入？顺便读一下板载光敏」

- `hw api DHT11 --version 3.12.7` 查真实安装包；先确认是否为外接模块、用的引脚和供电。只查 API 不触发硬件。
- 另一步在确认无 PinPong 占用后调用 `hw read light --version 3.12.7 --confirm`，用于**板载**光线传感器，给出 0–4095 原始值。

## 「换 Wi-Fi」或「触屏不准」

Wi-Fi：先用 `wifi status`，保留 USB，按 [Wi-Fi 指南](../references/wifi.md)人工配网；不要拿到密码后拼命令。触屏：`calibration-guide` 返回物理 Home 菜单路径，跟用户说明可能重启；不通过鼠标模拟触屏校准。
