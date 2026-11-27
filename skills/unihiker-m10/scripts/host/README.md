# 主机端工具

`m10.py`：用 Python 3.9+ 标准库调用 OpenSSH 或 Windows PuTTY，输出 JSON。`python m10.py --help` 查看入口；SSH 和子命令用法见 [快捷指令](../../references/commands.md) 与 [SSH](../../references/ssh.md)。无内置板子地址、账号、密码或主机键。板端块通过 SSH stdin 临时送入，不安装远程服务。

`check_update.py`：从控制电脑对比本地 [`VERSION`](../../VERSION) 与 GitHub 最新的正式 Release。默认仅在有新版时打印提示，`--verbose` 可查看其他结果。不需要 SSH 也不会下载或安装更新。
