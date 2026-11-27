# 板端助手

`probe.py`：Linux Python 3.7+ 可解析，提供版本和网络查询、X11 截图与输入、PinPong 静态查询和受版本限制的板载 I/O。由主机工具通过 SSH stdin 执行，通常不需要复制或直接调用。只在已明确授权的 M10 上运行。

X11 相关动作需要当前会话授权；截图需要 `xdpyinfo` 和支持 `x11grab` 的 `ffmpeg`，点击和按键需要 `libX11` / `libXtst`。硬件动作的 PinPong 审阅条件见 [硬件参考](../../references/hardware.md)。
