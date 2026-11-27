# 测试与验收

在 Skill 根目录运行 `python -B -m unittest discover -s tests -v`。默认测试不连接板、不安装依赖、不触发 GPIO。离线覆盖 SSH 指纹/错误分类、确认条件、PNG 与不覆盖、解释器选择、PinPong AST 查询、敏感配置过滤及未审阅库拦截。更新检查测试模拟 GitHub 返回，覆盖版本比较、新版提示、离线静默和超时，不访问网络。

- [实板验收和复测条件](board-acceptance.md)：只操作用户已确认的目标，实体改动要单独允许。默认不改网络、不执行物理校准、不重刷。
- [跨 Harness 的对话用例](agent-cases.md)：手工或未来评估脚本使用。要查看实际工具调用，不只评估 Agent 最后一段话。
