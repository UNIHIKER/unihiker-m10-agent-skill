# Python 选择、运行和安装依赖

## 先看实际解释器

`python list` 报告活跃解释器、`/usr/bin/python3` 和 pyenv。官方产品镜像从 v0.4.1 内置 pyenv 与 3.8.5/3.12.7；v0.4.2 真机的 `/usr/bin/python3` 是 3.7.3，SSH 的活跃解释器是 pyenv 3.12.7，Home 程序不一定用同一个。低于 v0.4.1 的设备缺 pyenv 时先用已具备依赖的系统 Python，或和用户讨论[官方更新](https://www.unihiker.com.cn/wiki/m10/burner) / [手动安装 pyenv](https://gitee.com/liliang9693/unihiker-pyenv-python)。不自动更新。

- **新任务优先 3.12.7**，条件是已安装且项目依赖支持；旧应用用它实际需要的解释器。先读 `pyenv versions`，不能猜版本存在。
- 快捷命令 `python run --version 3.12.7 /absolute/on/board/app.py` 只对子进程设置 `PYENV_VERSION`，要求该脚本已上传。需要用指定工作目录、屏幕会话或长期运行，明确启动方案，不把一次性工具改为自启。
- 手工等价动作：`PYENV_VERSION=3.12.7 pyenv exec python -V`；运行程序/检查库执行相同的 `PYENV_VERSION=… pyenv exec python`。非交互 SSH 找不到 pyenv 时检查 `$HOME/.pyenv/bin/pyenv`；不能直接假定初始化文件已加载。
- [官方 pyenv 指南](https://www.unihiker.com.cn/wiki/m10/pyenv)展示了 `pyenv global`。它会影响该账号其他调用，只在用户明确要全局切换且记录原值时使用，不能当作一次任务的前置操作。
- 更换 Home 当前运行 `.py` 是应用管理，不是更换 Python；交由 Home → 切换运行程序或明确停止本任务程序再启动另一个。注意 Home 的 `AutoStart`。

## 补依赖，优先最小改动

1. `ModuleNotFoundError` 先查项目本地文件、相对导入、部署目录和选到的解释器；不要看到模块名就装同名 PyPI 包。用目标解释器 `-m pip show DIST_NAME`，并确认发行包名称与兼容版本。
2. 在线安装经用户同意后使用该解释器 `-m pip`，优先用项目独立环境和固定依赖。不要自动 `pip install -U`，特别是 PinPong 和屏幕栈；别混用系统和项目的 pip。
3. **板端离线**：先读 CPython 版本/ABI、`uname -m`、`getconf GNU_LIBC_VERSION`，用目标解释器的 `-m pip debug --verbose` 核对兼容 tag。主机用 `pip download --only-binary=:all:`，依目标指定 `--platform`、`--python-version`、`--implementation`、`--abi` 并获取所有依赖。主机上能装的 Win/macOS/x86 wheel 不能据此上板。上传到项目的 wheelhouse，板端用目标解释器 `-m pip install --no-index --find-links /path/to/wheelhouse -r /path/to/requirements.txt`。没有兼容 wheel 就说明，不在板上自动编译。主机 pip 的环境标记解析不一定等同于板端，安装前在目标上核对依赖清单。
4. **apt 仅用于系统依赖**。旧 Buster 产品镜像的源可能失效；先核对系统版本和官方变更，不覆盖现有源、不自动 `apt upgrade`。仅在用户确认且备份后，对确为 Debian 10 的镜像参考 [Debian 归档](https://www.debian.org/distrib/archive)：`archive.debian.org/debian` 的 `buster` 与 `archive.debian.org/debian-security` 的 `buster/updates`。保留厂商所需的源；不把 Buster 源应用到 Debian 12 BSP，不关闭签名校验规避错误。
