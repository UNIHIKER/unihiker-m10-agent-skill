# 官方资料与证据分级

首次核对：2026-11-27（控制电脑日期）。不镜像整站，也不把不适用于 M10 的 Mind+ 操作、其他板型示例或第三方图片打包到 Skill。

| 用于 | 上游资料 |
|---|---|
| 产品定位、芯片、板载器件和引脚 | [中文产品页](https://www.unihiker.com.cn/products/m10)、[英文产品页](https://www.unihiker.com/products/m10)、[中文硬件介绍](https://www.unihiker.com.cn/wiki/m10/jianjie)、[英文规格](https://www.unihiker.com/wiki/HardwareReference/hardware_reference_specification/) |
| 入门、操作流程、示例 | [中文 M10 Wiki](https://www.unihiker.com.cn/wiki/m10)、[英文 Wiki](https://www.unihiker.com/wiki/)、[英文 Wiki 源码](https://github.com/UNIHIKER/unihiker-docs)、[英文示例](https://www.unihiker.com/wiki/Examples/PythonCodingExamples/) |
| 产品镜像、变更历史、系统和 Python | [镜像/烧录](https://www.unihiker.com.cn/wiki/m10/burner)、[更新日志](https://www.unihiker.com.cn/wiki/m10/ReleaseLogs)、[Home 菜单](https://www.unihiker.com.cn/wiki/m10/homemenu)、[pyenv 指南](https://www.unihiker.com.cn/wiki/m10/pyenv) |
| 独立的 Debian 12 最小环境 | [M10 BSP 源码库](https://github.com/UNIHIKER/unihikerM10-bsp)：不能当成带 Home/桌面的产品镜像。 |
| SSH、无线、远程桌面 | [SSH](https://www.unihiker.com.cn/wiki/m10/ssh)、[连接方式](https://www.unihiker.com.cn/wiki/m10/networking)、[本地 Web](https://www.unihiker.com.cn/wiki/m10/webmenu)、[屏幕共享](https://www.unihiker.com.cn/wiki/m10/vnc) |
| GUI 和音频 | [UNIHIKER Library](https://www.unihiker.com/wiki/LanguageReference/UNIHIKER_Library/)、[官方 Python 源码](https://github.com/UNIHIKER/unihiker-pypi-lib) |
| PinPong | [M10 中文 PinPong](https://www.unihiker.com.cn/wiki/m10/pinpong_python_lib)、[英文 M10 参考](https://www.unihiker.com/wiki/LanguageReference/PinPong_Library/)、[DFRobot 通用资料](https://wiki.dfrobot.com/software-1/)、[PinPong 文档](https://pinpong.readthedocs.io/zh-cn/latest/) |
| 故障排查 | [中文 M10 FAQ](https://www.unihiker.com.cn/wiki/m10/FAQ)、[英文 Troubleshooting](https://www.unihiker.com/wiki/Troubleshooting/) |

## 证据怎么读、怎么更新

- **官方**：链接明确发布的行为，不等于所有版本都一样。核对相关型号、适用固件、注意事项和校验提示。
- **实测**：用户提供的经验用来找检查点，再以[实板记录](../tests/board-acceptance.md)确证。控制器当时通过用户明确指定的自定义 USB 地址联机；它不是新出厂默认值。公开日志中观察到的产品镜像为 `V0.4.2`，未用该日志确认 V0.5.0 的系统或触屏配网行为。板载 Web 的路由、Home 配置字段和 X11 截图都按实测版本标注。
- **条件性**：桌面库、未复验系统及私有固件功能只给检测办法，不承诺存在。截图脚本参考用户提供的本地 `capture-unihiker-screen` Skill 的 `xdpyinfo` / `ffmpeg` 方法；这里重写为 SSH 内直接回传 PNG，未复制其认证实现。

新镜像发布或包更新时，逐项核对 `ReleaseLogs`、相关官方页和当前板端源文件；重跑对应验收，记录板型、镜像、库/工具版本和差异。不自动刷机同步，也不根据页面 HTTP 成功就声称步骤仍可用。引脚图优先链接到官方页面；需要离线分发第三方资源时先核对许可和来源。
