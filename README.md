# UNIHIKER M10 Agent Skill

An Agent Skill for inspecting and controlling the UNIHIKER M10 over SSH.

让电脑上的 Agent 查询行空板 M10 的系统和 Python 版本、运行程序、截取板载屏幕，并调试板载硬件。不依赖 Mind+、板端 Agent、常驻进程或 MCP 服务。此 Skill 仅适用于 UNIHIKER M10。

## 安装与使用

- **技能名称：** `unihiker-m10-control`。将整个 [`skills/unihiker-m10-control/`](skills/unihiker-m10-control/) 目录放入所用 Harness 支持的 Skills 目录；不要只复制 [`SKILL.md`](skills/unihiker-m10-control/SKILL.md)。
- **电脑端环境：** Python 3.9+。推荐 OpenSSH 和 SSH 密钥；Windows 密码自动化可用 PuTTY `plink`，macOS/Linux 则需要额外的 `sshpass`。执行环境必须能通过 USB 网络或局域网访问 M10。板端助手通过 SSH 发送，无需安装服务。
- **文档：** [快捷指令](skills/unihiker-m10-control/references/commands.md) · [SSH 与主机身份校验](skills/unihiker-m10-control/references/ssh.md) · [官方资料和验证来源](skills/unihiker-m10-control/references/sources.md) · [实板验收](skills/unihiker-m10-control/tests/board-acceptance.md)。

从仓库根目录运行（macOS/Linux 上可以用 `python3`）：

```sh
cd skills/unihiker-m10-control
python scripts/host/m10.py --host BOARD_IP discover-key
python scripts/host/m10.py --host BOARD_IP --user BOARD_USER status
```

`discover-key` 只列出未验证的指纹。先通过可信渠道确认并写入 `known_hosts`，或用 `--host-key` 固定已验证的指纹。`BOARD_IP` 和 `BOARD_USER` 是占位值，必须替换。

## 版本与更新

所安装 Skill 的版本见 [`VERSION`](skills/unihiker-m10-control/VERSION)。Agent 在会话中首次使用此 Skill 时会从控制电脑检查 [GitHub Releases](https://github.com/UNIHIKER/unihiker-m10-agent-skill/releases)；只在有更高的正式发布版本时提醒，不自动安装。没发现新版、离线或检查失败时不打扰后续任务。需要完全离线时，可为控制端进程设置 `UNIHIKER_M10_SKIP_UPDATE_CHECK=1`。

也可在 Skill 根目录手动运行 `python scripts/host/check_update.py --verbose` 查看检查状态。发布新版时先改 `VERSION`，再发布对应的正式版本，例如版本 `0.1.0` 对应 `v0.1.0`；仅推送代码或发布预览版不会触发提醒。收到提示后，从 Releases 获取需要的版本，手动替换已安装的整个 Skill 目录，再按所用 Harness 的方式重新加载。这个检查不涉及 M10 固件或官方 Wiki 更新。

## 测试

从仓库根目录运行 `python -B -m unittest discover -s skills/unihiker-m10-control/tests -v`。离线测试不连接板子；真机验收已覆盖 Windows + M10 v0.4.2，尚未在 macOS/Linux 主机上复测。

## 许可

本仓库的文档和代码采用 [MIT License](LICENSE)。链接指向的外部资料仍适用其原有许可。
