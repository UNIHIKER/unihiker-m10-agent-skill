# M10 板型与版本检查

## 先了解目标

M10 是 DFRobot 的 Python 单板机：官方规格为 Rockchip RK3308 系列、Arm64 四核、512 MB RAM、16 GB eMMC，带 GD32 协处理器、2.8 英寸 240×320 电阻触控屏、Home/A/B、光敏、六轴、麦克风、蓝色 L 灯、蜂鸣器和外接 I/O。没有 HDMI 显示输出；Type-C 供电与 USB 网络连接，另有 USB-A、microSD 和扩展接口。产品镜像运行定制 Home 菜单，不要假设有常规 Debian 桌面。详见[官方规格与引脚图](https://www.unihiker.com.cn/wiki/m10/jianjie)。

## 查看版本

使用 `status`（[工具用法](commands.md)），分别看：

- `image_version`：产品镜像 `/opt/unihiker/Version`；实测 `v0.4.2`。文件没有或布局异常时，核对板型和镜像，亦可用 Home → 查看系统信息。对照[官方更新日志](https://www.unihiker.com.cn/wiki/m10/ReleaseLogs)。
- `linux`：`/etc/os-release`、内核、架构、glibc；它们都不是 M10 镜像版本。产品镜像 v0.4.2 实测 Debian 10/aarch64/glibc 2.28。官方 BSP 文档描述的是另一条 Debian 12/console-only 路线。
- `active_python` / `system_python` / `pyenv`：当前 SSH 解释器、系统解释器、pyenv 的可选版本。不要把它们混作一个版本，也不要用 Python 版本反推出镜像版本。
- 实板设备树可能显示 `Radxa ROCK Pi S`；使用用户对实体板的确认加上镜像布局和握手，不靠设备树字符串或主机名猜板型。

## 产品镜像 `/opt/unihiker`：只读

| 路径 | 用途 |
|---|---|
| `/opt/unihiker/Version` | M10 产品镜像版本。 |
| `/opt/unihiker/pyboardUI/config.cfg` | v0.4.2 实测为 JSON，含 `language`、`AutoStart`、`file`/`path`、热点配置 `ap*`、`Jupyter`、`SIoT`/`siotVersion`、`FileShare`、`ScreenShare` 等。字段随镜像变化。标准探测只返回语言、开关与 SIoT 版本；不回传热点密码和上次运行路径。 |
| `/opt/unihiker/examples/` | Home 内置示例；先读文件再决定是否运行，不在原目录编辑。 |

`AutoStart` 是板载菜单的启动设置，不能等同于一次 SSH 运行。通过 Home 菜单查看和管理板载配置，不通过编辑、删除配置或重启来试探行为。需要传项目时，使用用户目录下单独的新目录。
