## 外婆家菜谱实现方案

项目简介及核心创意  
“野生菜谱数字卡片”用 3 个轻量级 Agent 完成“语音 → 文字 → 美观卡片”一站式生成，30 秒出图可发朋友圈。基础版纯 Web 分享，降低参赛门槛。

解决问题  
- 老人方言菜谱无文字记录  
- 传统存档没人看、难分享  
- 手动排版做图太麻烦

Agent 协作场景  
用户在小程/Studio 按住说话 → 录音 Agent 实时转写 → 整理 Agent 补全“适量→克”并生成 Markdown → 卡片 Agent 一键输出带二维码的 PNG 卡片；扫码即可查看完整网页版菜谱。

技术方案简述  
计划 3 个 Agent  
[×] 1. Recorder Agent：用户在小程/Studio 按住说话 → 录音 Agent 实时转写文件或者语音 URL → ASR 文本  
[ ] 2. Polisher Agent：文本 → 标准化 Markdown（食材、用量、步骤）  
[ ] 3. CardMaker Agent：Markdown → HTML → PNG 卡片（含二维码，扫码跳到 Web 展示页）

OpenAgents 协作  
- 事件总线：三级主题 `recipe.audio` → `recipe.md` → `recipe.card` 自动串行  
- Shared-Artifact Mod：持久化存放 Markdown、HTML、PNG，支持断点续跑  
- LLM-Logs Mod：记录 ASR 与图像生成 Token 消耗  
- 协议：WebSocket（实时）+ HTTP（下载卡片）双栈  
- Studio 集成：卡片完成后前端自动弹出“下载”按钮

预期实现的功能清单  
① Recorder Agent：监听语音上传事件，返回转写文本与置信度  
② Polisher Agent：订阅转写 → 补全用量单位 → 输出标准 Markdown  
③ CardMaker Agent：读取 Markdown → 渲染美观 HTML → 生成 PNG 卡片并写入 Shared-Artifact  
④ Shared-Artifact Mod：提供 `/download/recipe_card.png` 静态地址，Studio 一键下载  
⑤ LLM-Logs Mod：集中记录 ASR、图像生成耗时与费用，便于后期优化


### 快速复刻建议

可以直接复刻官方 demo  
`demos/04_grammar_check_forum`

理由 & 改法一览（按上面“3 个 Agent”方案对照）

1. 目录结构完全对齐  
   - 已有：Forum Agent（相当于 Recorder + Polisher 的骨架）  
   - 已有：grammar_checker.yaml（可原地换成 Polisher 提示词）  
   - 缺 CardMaker → 在 `agents/` 新建 `card_maker.py` 即可，其余事件、Mod、网络配置全部沿用。

2. 事件流直接复用  
   - 原论坛流程：用户发帖 → 触发 grammar 检查 → 回写评论  
   - 菜谱流程：用户语音帖 → 触发 Polisher → 触发 CardMaker → 回写“卡片下载链接”  
   → 把事件名 `forum.post.new` 改成 `recipe.audio.new` 即可，代码改动 <10 行。

3. 现成的 Shared-Artifact Mod  
   - 原 demo 用来存“帖子快照”，现在存 Markdown & PNG，路径不变，直接 `artifact.put(key=recipe_id, value=png_bytes)`。

4. Studio 交互零修改  
   - 原论坛页面就是聊天室形式；人类上传语音=发一条消息，Studio 自动显示“下载卡片”链接即可。

5. 启动命令一模一样  
   ```
   openagents network start demos/04_grammar_check_forum  
   openagents agent start demos/04_grammar_check_forum/agents/forum.yaml        # 改名 recorder.yaml  
   openagents agent start demos/04_grammar_check_forum/agents/grammar_checker.yaml  # 改名 polisher.yaml  
   python demos/04_grammar_check_forum/agents/card_maker.py   # 新增
   ```

总结：  
把 `04_grammar_check_forum` 拷贝一份 → 改事件名 → 换提示词 → 加 1 个 CardMaker Agent 即可在 30 分钟内跑通“野生菜谱数字卡片”基础任务，完全兼容官方代码与 Studio。