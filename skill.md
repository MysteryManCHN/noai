# Feishu Meeting Agent - 飞书会议智能助手 Skill

## Skill 基本信息

- **名称**: 飞书会议智能助手 (feishu-meeting-agent)
- **版本**: 1.0.0
- **分类**: 办公效率 / 会议协作
- **描述**: 不依赖飞书自带AI总结的独立会议Agent，支持机器人真实入会、实时监听转写、自主增量总结、会中对话。

## 触发场景

当用户提到以下内容时可触发本 Skill：

- "帮我加入会议总结一下"
- "会议记录/会议纪要"
- "实时总结会议内容"
- "机器人入会"
- "会议待办提取"
- "不想要飞书自带的AI总结"

## 能力清单

### 1. 机器人入会
- 通过 lark-cli 让应用机器人加入飞书会议
- 支持通过9位会议号入会
- 自动发送入会通知

### 2. 实时会议监听
- 定时轮询会议事件（转写、聊天、参会人变化）
- 事件去重，避免重复处理
- 支持自定义轮询间隔（默认10秒）

### 3. 自主增量总结
- 接入 OpenAI / Anthropic / DeepSeek 等大模型
- 不依赖飞书自带AI，完全自主生成总结
- 支持自定义总结Prompt和输出格式
- 默认30秒更新一次总结

### 4. 话题追踪
- 实时识别当前讨论主题
- 记录话题变迁历史
- 支持关键词匹配 + LLM智能识别双模式

### 5. 待办提取
- 从对话中自动识别待办事项
- 提取负责人和时间信息
- 支持规则匹配 + LLM提取双模式

### 6. 会中消息发送
- 发送文本总结到会议聊天
- 发送待办事项列表
- 支持表情反馈

## 使用方式

### 方式1 - CLI 命令行

```bash
# 基本使用
feishu-agent 123456789

# 指定LLM提供商和模型
feishu-agent 123456789 --provider openai --model gpt-4o-mini

# 自定义轮询和总结间隔
feishu-agent 123456789 --poll-interval 5 --summary-interval 60
```

### 方式2 - Python API

```python
import asyncio
from meeting_agent import Config, MeetingAgent

async def main():
    config = Config.from_env()
    agent = MeetingAgent(config)

    # 加入会议
    if not agent.join("123456789"):
        print("入会失败")
        return

    # 启动监听和总结
    try:
        await agent.start()
    except KeyboardInterrupt:
        pass
    finally:
        await agent.stop()
        agent.leave()

asyncio.run(main())
```

## 前置要求

| 依赖 | 说明 |
|------|------|
| Python | >= 3.10 |
| lark-cli | 已安装并完成认证 |
| VC Agent 权限 | 需开通飞书 VC Agent 内测权限 |
| LLM API Key | OpenAI / Anthropic / DeepSeek 任选其一 |

## 配置参数

### LLM 配置

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|--------|------|
| 提供商 | `LLM_PROVIDER` | `openai` | openai / anthropic / deepseek |
| API Key | `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `DEEPSEEK_API_KEY` | - | 对应提供商的API密钥 |
| 模型 | `LLM_MODEL` | `gpt-4o-mini` | LLM模型名称 |
| 温度 | `LLM_TEMPERATURE` | `0.7` | 生成温度 (0-1) |

### 会议配置

| 参数 | 环境变量 | 默认值 | 说明 |
|------|---------|--------|------|
| 轮询间隔 | `POLL_INTERVAL` | `10` | 事件轮询间隔（秒） |
| 总结间隔 | `SUMMARY_INTERVAL` | `30` | 总结更新间隔（秒） |
| 自动回复 | `AUTO_RESPONSE` | `true` | 是否自动发送总结到会议 |
| lark-cli 路径 | `LARK_CLI_PATH` | 自动检测 | lark-cli 可执行文件路径 |
| 日志级别 | `LOG_LEVEL` | `INFO` | DEBUG / INFO / WARNING / ERROR |

## 工作流程

```
用户发起 → 加入会议 → 实时监听 → 增量总结 → 会中推送 → 离会结束
     ↑                                                    ↓
     └──────────────── 待办提取 / 话题追踪 ←──────────────┘
```

1. **入会阶段**：调用 `lark-cli vc +meeting-join` 让机器人加入会议
2. **监听阶段**：定时轮询 `lark-cli vc +meeting-events` 获取转写/聊天/参会人事件
3. **总结阶段**：将转写文本送入 LLM 增量生成总结
4. **推送阶段**：通过 `lark-cli vc +meeting-message-send` 发送总结到会议
5. **离会阶段**：用户退出时调用 `lark-cli vc +meeting-leave` 离会

## 输出示例

### 会议总结格式

```
📋 会议总结 (更新于 14:30:00)

🔹 当前话题：Q3 产品规划讨论

📝 关键要点：
• 确认Q3重点方向为AI功能迭代
• 预计8月中旬发布首个AI版本
• 需要额外2名前端开发支持

✅ 已达成决议：
• 同意增加AI功能开发预算
• 产品经理本周输出详细PRD

📌 待办事项：
• [张工] 输出AI功能PRD - 截止本周五
• [李经理] 协调前端人力 - 下周一前
• [王总] 审批预算申请 - 本周内
```

## 注意事项

- ⚠️ **VC Agent 内测权限**：需要飞书开放平台开通 VC Agent 内测权限。如遇 `error.code=20017`，需加入早鸟群确认权限。
- ⚠️ **身份一致性**：`meeting_id` 来源身份必须与后续操作身份一致（USER/BOT）。
- ⚠️ **会议号格式**：必须提供9位纯数字会议号，不是会议链接或 `meeting_id`。
- ⚠️ **LLM 费用**：使用 LLM 总结会产生 API 调用费用，请关注用量。

## 相关链接

- [项目仓库](https://github.com/MysteryManCHN/noai)
- [架构设计](docs/ARCHITECTURE.md)
- [使用指南](docs/USAGE.md)
- [API 文档](docs/API.md)
- [更新日志](CHANGELOG.md)

## License

MIT
