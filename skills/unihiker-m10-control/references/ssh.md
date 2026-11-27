# SSH、连接诊断与文件传输

官方产品镜像通常已启用 SSH/22，官方[SSH 指南](https://www.unihiker.com.cn/wiki/m10/ssh)列出出厂账户信息。实际用用户确认的账号和认证方式，不默认使用出厂凭据，不在命令、仓库和日志中存口令。

## 连接方式

1. **USB Type-C 数据线直连**：官方默认目标 `10.1.2.3`，不是串口。v0.4.2 实测板端 `usb0` / `usb1` 加入 `br0` 网桥，控制电脑只看到活动的 USB 网络接口。不要锁死板端接口名、子网或控制电脑获配的地址；尤其多板和自定义 IP 环境。
2. **同一 2.4 GHz Wi-Fi 或局域网**：从 Home → 查看网络信息取得板子的真实地址。共享热点的典型板端地址是 `192.168.123.1`。也可接 Linux 兼容的 USB-A 转网口设备。
3. **云端/沙箱 Harness**：把 SSH 工具放在实际可达板子的本地执行端。云端不能直接访问控制电脑的 USB 网段；不要为此把 SSH 暴露到公网。

## 先连通，再认证，再识别板子

以下变量是占位值，运行前替换。命令在 Skill 根目录执行，`BOARD_USER` 是已确认的 SSH 用户：

```sh
python scripts/host/m10.py --host BOARD_IP ssh tcp
python scripts/host/m10.py --host BOARD_IP discover-key
python scripts/host/m10.py --host BOARD_IP --user BOARD_USER --host-key VERIFIED_SHA256 ssh check
python scripts/host/m10.py --host BOARD_IP --user BOARD_USER --host-key VERIFIED_SHA256 status
```

- `ssh tcp` 是指定地址的 TCP/22 测试；成功不代表 SSH 可登录。Windows 可用 `Get-NetIPConfiguration` / `Test-NetConnection` 检查本地路由和端口；Linux 可用 `ip -br addr` / `ip route get BOARD_IP`；macOS 可用 `ifconfig` / `route -n get BOARD_IP`。不默认扫描整个网段或进行带流量的测速；主机识别优先靠板载菜单和标签。
- `discover-key` 的结果**未经验证**。在可信板端控制台或事先记录中对照 `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` 的公钥指纹。首次未知或重刷后改变，不自动接纳；校验后用正常 `known_hosts` 或 `--host-key SHA256:...`。脚本使用 `--host-key` 时只接受匹配的键。
- 推荐使用 SSH 密钥/agent；可选 `--identity`。密码方式使用由用户提供的进程环境变量 `UNIHIKER_SSH_PASSWORD` 并要求已校验的 `--host-key`；Windows 使用 PuTTY `plink -pwfile`（临时文件），其他平台需要 `sshpass` + OpenSSH。不把口令写在参数、工具配置或聊天结果里。临时任务结束后关闭或清除此变量。
- `ssh check` 验证登录与远程运行；`status` 才报告检测到的 M10 产品镜像布局。无设备或密钥不匹配时停止，别改 `StrictHostKeyChecking`。

## 文件和远程命令

上传项目文件用系统 OpenSSH `sftp BOARD_USER@BOARD_IP`（先建立可信 `known_hosts`）；创建专门的用户项目目录，用 `put` 发单文件或项目所需资源。Windows PuTTY 环境也可用已固定主机键的 PSFTP。不要把文件写进 `/opt/unihiker`、覆盖用户原有程序或传 SSH 私钥。`m10.py ... ssh run '...'` 接受**经过审查的显式远程命令**，运行在板端 Linux shell，经 `timeout` 限制；不要把未经验证的外部文本拼成 shell 命令。需要真实终端的密码输入、交互式配网等用交互式 SSH，不用 `ssh run`。
