![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)

# Feishu Meeting Agent - 飞书会议智能助手

> 不依赖飞书自带 AI 总结的独立会议 Agent，支持机器人真实入会、实时监听转写、自主增量总结、会中对话。

## 功能特性

- **机器人真实入会** - 通过 lark-cli 让应用机器人加入飞书会议
- **实时事件监听** - 轮询获取会议转写、聊天消息、参会人变化
- **自主增量总结** - 接入 OpenAI/Anthropic/DeepSeek，不依赖飞书自带AI
- **话题追踪** - 实时识别当前讨论主题，记录话题变迁
- **待办提取** - 从对话中自动识别待办事项和负责人
- **会中消息** - 发送文本总结、待办列表、表情反馈

## 项目结构

```
feishu-meeting-agent/
├── meeting_agent/
│   ├── __init__.py          # 包入口，导出所有公共类
│   ├── config.py            # 配置管理
│   ├── lark_cli.py          # lark-cli 封装
│   ├── main.py              # 主入口（MeetingAgent 类）
│   ├── agent.py             # 简易启动脚本
│   ├── meeting/             # 会议模块
│   │   ├── manager.py       # 入会/离会/发现会议
│   │   ├── listener.py      # 事件监听
│   │   └── messenger.py     # 会中消息发送
│   └── summary/             # 总结模块
│       ├── engine.py        # 增量总结引擎（LLM驱动）
│       ├── topics.py        # 话题追踪
│       └── todos.py         # 待办提取
├── docs/                    # 文档
├── examples/                # 示例代码
├── pyproject.toml           # 包配置
└── requirements.txt         # 依赖
```

## 前置要求

- Python 3.10+
- lark-cli 已安装并认证（需开通 VC Agent 内测权限）
- LLM API Key（OpenAI / Anthropic / DeepSeek 任选其一）

## 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/feishu-meeting-agent.git
cd feishu-meeting-agent

# 安装依赖（选择你使用的LLM提供商）
pip install -e ".[openai]"      # OpenAI
pip install -e ".[anthropic]"   # Anthropic
pip install -e ".[deepseek]"    # DeepSeek
```

## 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，填入你的 API Key
# OPENAI_API_KEY=sk-xxx
# 或 ANTHROPIC_API_KEY=sk-xxx
# 或 DEEPSEEK_API_KEY=sk-xxx
```

## 使用

### 方式1 - CLI

```bash
python -m meeting_agent.main 123456789 --provider openai --model gpt-4o-mini
```

### 方式2 - Python API

```python
import asyncio
from meeting_agent import Config, MeetingAgent

async def main():
    config = Config.from_env()
    agent = MeetingAgent(config)
    agent.join("123456789")
    await agent.start()

asyncio.run(main())
```

### CLI参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| meeting_number | (必填) | 9位会议号 |
| --provider | openai | LLM提供商 |
| --model | gpt-4o-mini | LLM模型名 |
| --poll-interval | 10 | 事件轮询间隔(秒) |
| --summary-interval | 30 | 总结更新间隔(秒) |
| --log-level | INFO | 日志级别 |

## 工作原理

1. **入会** → `lark-cli vc +meeting-join`
2. **监听** → 定时轮询 `lark-cli vc +meeting-events`
3. **总结** → 转写文本送入LLM增量生成总结
4. **对话** → 通过 `lark-cli vc +meeting-message-send` 发送消息
5. **离会** → 用户退出时 `lark-cli vc +meeting-leave`

## 注意事项

- 需要飞书 VC Agent 内测权限，如遇 `error code 20017` 需加入早鸟群
- `meeting_id` 来源身份必须与后续操作身份一致
- 会议号必须是9位纯数字

## 文档

- [架构设计](docs/ARCHITECTURE.md)
- [使用指南](docs/USAGE.md)
- [API文档](docs/API.md)
- [贡献指南](CONTRIBUTING.md)
- [更新日志](CHANGELOG.md)

## License

MIT
