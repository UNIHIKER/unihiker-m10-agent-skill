# 板载屏显示、截图、输入与触屏校准

板载屏为 240×320 竖屏，实际坐标用当前显示会话探测。产品镜像 v0.4.2 实测是 Xorg/LightDM 的 `:0`，显示定制 Home 界面。SSH 中没有 `DISPLAY` 很常见；先判断目标屏对应的本地会话和访问授权，再为该任务设置，不改 X11 权限、不用 `xhost +`。不要启动 Xvfb 冒充物理板载显示，也别把 RDP 建出来的新会话当成板载屏。另见 [GUI 官方文档](https://www.unihiker.com/wiki/LanguageReference/UNIHIKER_Library/)。

## 根据目标选择方案

| 目标 | 首选与条件 |
|---|---|
| 简单文本、按钮、课程示例、低频仪表 | `unihiker.GUI`，基于 Tk；有官方控件和 M10 坐标约定。 |
| 更细的窗口、布局和组件样式 | `tkinter`，可选已验证可用的 `ttkbootstrap`。验证目标 Python 的 Tk 和字体；不要在同一个应用混用多个 GUI 主循环。 |
| 游戏、连续画面 | `pygame`，根据已安装版本和 SDL 显示实际试跑；限帧、避免高分辨率资源。 |
| 更复杂的组件体系 | PyQt/PySide，先查 Arm64 包和 X11/Qt 插件依赖；内存和启动成本更高，不是默认。 |
| 用轻量 HTML 做板载 UI | `pywebview`，依赖 Linux 上实际可用的 GTK/WebKitGTK 或 Qt 后端及系统库；先核对架构和 [pywebview 安装文档](https://pywebview.flowrl.com/guide/installation.html)。真机未装，不默认在线安装。 |
| 手机/电脑浏览器访问板载服务 | **Flask** + HTML/CSS/JS（不是 Flash）。这是局域网服务，不等同于画在板载屏上；测试优先仅绑定回环，使用受控访问，不开启生产 debug 或对公网暴露。 |
| 无桌面、纯图片处理 | Pillow/OpenCV 离屏渲染或处理；生成图片不是板载显示也不是截图。需要真实本地显示但无会话时，报告不可用。 |

## 抓取板载屏

`screen shot --output NEW_PATH.png` 默认探测 `:0`，在板端通过 `xdpyinfo` 取尺寸、`ffmpeg x11grab` 抓一帧，经 SSH 回传 PNG，不留远端截图，不覆盖本地文件。实测 v0.4.2 `:0` 240×320，PNG 内容为板载 Home 网络页。输出路径和分辨率是证据；需要判断 UI 时还要真的打开 PNG。没有 X11、工具或授权就报错，备选是[官方 VNC/屏幕共享](https://www.unihiker.com.cn/wiki/m10/vnc)，确认看的确实是板载会话。截图可能含隐私，不默认上传或提交到项目。

## UI 调试和物理触控

- `screen pointer` 只读。`screen move X Y --confirm` 会移动并回读位置。`screen click X Y --confirm` 先用当前界面核实控件，工具验证移动坐标后才向 XTEST 发送一次左键按下/释放。`screen key a --confirm` 仅支持直接映射的单个 keysym，无键组合、字符流、密钥输入；人工确认焦点。窗口是否响应由截图或测试应用验证，不以 `event_sent` 代替。
- `calibration-guide` 只检查 `ts_calibrate` 是否存在并返回用户步骤，不远程触发。推荐 **Home → 校准触摸屏 → 按提示点校准点**，官方文档提示过程可能导致重启，先保存工作并由用户在板旁操作。不能拿 XTEST 鼠标点击当作电阻触摸屏的校准，也不直接运行裸 `ts_calibrate` 写入输入设备配置。
