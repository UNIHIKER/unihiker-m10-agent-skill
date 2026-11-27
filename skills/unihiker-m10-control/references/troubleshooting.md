# 排障与恢复

先用 [官方中文 FAQ](https://www.unihiker.com.cn/wiki/m10/FAQ) / [英文 Troubleshooting](https://www.unihiker.com/wiki/Troubleshooting/) 定位，并对照当前产品镜像版本。检查时优先只读，不把官方 FAQ 里的重启、关闭全部 Python 或重刷建议当成默认动作。

| 症状 | 优先检查 | 不要做 |
|---|---|---|
| USB/SSH TCP 不通 | 确认是数据线，板启动后看控制端 USB 网卡和路由；在 Home 看 USB IP。网络上可能有多个 M10。 | 改地址、盲扫网段，将密码试到其他主机。 |
| SSH 密钥变化/认证失败 | 分清 `HOST_KEY_REJECTED` 与 `AUTH_FAILED`；实物核对可能的换板/刷机，或核对账号和认证方式。 | 关闭校验、清空 known_hosts 或重复猜密码。 |
| Wi-Fi 配好但 SSH 不通 | 查无线接口 IPv4、执行端同网段、AP 隔离；保留 USB 链路。 | 从唯一的远程链路直接切断网络后再排障。 |
| `pyenv` 不见 / 找不到库 | 核对 SSH 非交互 PATH、`$HOME/.pyenv/bin/pyenv`、实际解释器和项目文件；查版本与架构。 | 改系统 Python，或自动安装同名包。 |
| PNG 没生成 / `NO_DISPLAY` / `DISPLAY_ACCESS` | 确认是产品镜像，查看板载 X11 会话、授权和 `ffmpeg x11grab`；必要时用人工 VNC。 | 用虚拟桌面、静态图片代替物理屏幕截图。 |
| PinPong 超时、读数全零 | 核对已选解释器的库版本、是否有其他程序使用硬件、当前固件支持的设备接口；用 `hw api` 查实际代码。 | 全局杀 Python、自动升级或刷协处理器。单次全零也不是传感器损坏的充分证据。 |
| 触屏偏移 | 让用户在板旁从 Home 进入官方校准，注意可能重启。 | 静默触发 `ts_calibrate` 或用模拟点击假装物理校准。 |

断线或超时后，先重新确认同一设备，再读状态；如果不确定写操作发生到哪一步，报告「未验证」，别无条件重发。只清理本任务产生的文件或进程；用户已有程序和系统配置不动。
