# Wi-Fi 与热点

不要把「板子连接路由器」与「板子作为热点」混为一谈。M10 官方使用 2.4 GHz Wi-Fi；热点启用后典型板端地址为 `192.168.123.1`，连接外部路由器后地址由其分配。先用 `wifi status` 或 Home → 查看网络信息识别连接。`wifi status` 只读 NetworkManager 设备状态和接口 IPv4 地址，不触发重新扫描，不显示 SSID 密码。

## 推荐：保留 USB，从官方 Web 页面配网

1. 先用 USB 独立访问 M10；确认要加入的 SSID 和用户许可。这条 USB 网络保持连接，避免无线切换后失联。
2. 浏览器打开 `http://BOARD_USB_IP/`，进「网络设置」，由用户输入密码。`/pc/network-setting` 在 v0.4.2 真机返回正常页面；其他版本优先从首页菜单进入，不把这个 URL 当成稳定 API。在隔离的 USB 连接上操作，不在共享网络上传出厂 Web 管理凭据。
3. 用 Home 网络信息或 `wifi status` 检查无线接口拿到新 IPv4。让控制电脑在同网段连接新地址，验证 SSH 与板子的主机身份；拿到 IP 不等于能从其他设备连通。失败优先排查 Wi-Fi 频段、AP 隔离、获址和路由，保留 USB 以便恢复。

## 明确要求才用 `nmcli`（条件性）

v0.4.2 实测存在 `nmcli`，查询可用；本 Skill 未实际提交 Wi-Fi 配置。确认 NetworkManager 管理的是实际 Wi-Fi 接口后，用交互式 SSH，让用户输入密码：

```sh
nmcli -t -f DEVICE,TYPE,STATE device status
nmcli device wifi list ifname WLAN_INTERFACE
nmcli --ask device wifi connect 'USER_SSID' ifname WLAN_INTERFACE
```

不在 `ssh run` 或非交互工具中传 `password ...`。不自动删除旧连接配置，不切换热点、加密或无线开关来「试试看」。若只能通过当前 Wi-Fi 控制设备，先由用户建立 USB 或实物恢复路径。`V0.5.0` 触屏直接输入 Wi-Fi 密码的功能未在公开日志或测试板核实；只有实板显示该入口时才按界面操作。官方说明见 [连接方式](https://www.unihiker.com.cn/wiki/m10/networking)、[Web 设置](https://www.unihiker.com.cn/wiki/m10/webmenu)、[Home 热点](https://www.unihiker.com.cn/wiki/m10/homemenu)。
