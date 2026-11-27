# 板载 I/O、PinPong 和真实 API

M10 的主 CPU 管 Linux、屏和音频，协处理器及 Linux 外设接口负责多数板载元件与外接 I/O。[M10 PinPong 官方指南](https://www.unihiker.com.cn/wiki/m10/pinpong_python_lib)优先于通用 PinPong 教程。`unihiker.Audio` 才是屏侧麦克风/USB 音频所用的库，不把麦克风当成 PinPong 模拟引脚，也不默认录音。

1. `status` 查看目标解释器的 PinPong 版本；`hw api MODEL_OR_SYMBOL --version 3.12.7` 对板上当前包的 `board.py`、`extension/`、`libs/` 和 `examples/` 做静态查找，返回候选模块、源码行、签名和随包示例。无匹配就明确说明，必要时打开安装包实际文件；不运行搜索到的示例来反查 API。
2. 查正确的设备和板型。比如 `hw api light` 也可能返回其他板型的 `light` 或 LCD 背光；M10 的板载传感器在 `pinpong.extension.unihiker`。`DHT11` 实测定义在 `pinpong.board`，但查到类不代表板子自带 DHT11 或了解外接脚位。
3. `hw read light|button-a|button-b --confirm`、`hw blink --count 1 --confirm` 用于板上没有其他 PinPong 程序占用且用户确认的任务。灯是官方 P25 的板载 L 灯，1–5 个周期，清理时写灭。报告命令执行与物理观察是两回事。光敏是 0–4095 的原始值，不是 lux；A/B 返回按下状态，Home 是系统导航键。

## 为什么不自动初始化或升级

官方[PinPong 介绍](https://www.unihiker.com/wiki/LanguageReference/PinPong_Library/pinpong_library_introduction/)提示某些旧版本或路径可能在初始化时烧录。对实测 PinPong `0.6.2`，查看 `Board.begin` 的 UNIHIKER 分支确认 `firmware=0` 不走 `firmware=1` 刷写路径。自动硬件命令只有匹配已审阅的源码指纹才允许初始化；不匹配使用 `hw api` 调研，不为了通过检测而升级或篡改指纹。该限制不声称验证了系统每个组件，也不替代目标确认。锁只协调本 Skill 的调用，不能探测所有第三方程序；先让用户停掉确已占用的应用。

外接模块必须知道型号、官方引脚图、3.3 V I/O 电平和独立供电需求后再选 GPIO/I²C/PWM。禁止盲探引脚，禁止用 GPIO 给电机/继电器直接供电；出错后优先停止本次动作并恢复安全状态。遇到初始化超时、全零或缺设备节点，看 [故障排查](troubleshooting.md)，不要自动调用 `Board().begin(1)` 或重刷。
