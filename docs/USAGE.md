# 使用指南

本文档介绍 meeting-agent 的前置准备、快速开始、配置项、典型场景、自定义总结 Prompt、轮询参数调优以及常见问题排查。

## 前置准备

在运行 meeting-agent 之前，需要完成以下准备工作：

### 1. lark-cli 安装和认证

- 安装 `lark-cli`（飞书命令行工具），并确保其在系统 `PATH` 中可被调用。
- 执行认证流程，分别完成 BOT 身份与 USER 身份的登录：
  - BOT 身份用于入会、离会、会中消息等写操作。
  - USER 身份用于查询当前用户正在进行中的会议。
- 验证安装：执行 `lark-cli --version` 应能正常输出版本号。

### 2. VC Agent 内测权限说明

- BOT 所在的飞书应用需要开通 **VC Agent（会议智能体）内测权限**，否则入会操作会被拒绝。
- 申请权限通常需要联系飞书开放平台对应接口人，并在应用后台开启相关 scope。
- 权限生效后，BOT 才能以"应用机器人"身份真实加入会议并读取会中事件。

### 3. LLM API Key 配置

- 至少准备一个 LLM 提供商的 API Key（OpenAI / Anthropic / DeepSeek 任选其一）。
- 将 Key 写入环境变量（见下方"配置详解"），或通过 `.env` 文件加载。
- 若仅需监听会议事件而不需要总结，可不配置 LLM（见"场景3"）。

## 快速开始

### CLI 方式

```bash
# 设置 LLM Key（以 DeepSeek 为例）
export LLM_PROVIDER=deepseek
export LLM_API_KEY=sk-xxxxxxxx
export LLM_MODEL=deepseek-chat

# 加入会议并自动总结
python -m meeting_agent.main join --meeting-number 123456789
```

### Python API 方式

```python
"""快速开始：加入会议并自动总结"""
import asyncio
from meeting_agent import Config, MeetingAgent


async def main():
    config = Config.from_env()
    agent = MeetingAgent(config)

    # 加入会议
    if not agent.join("123456789"):
        print("入会失败")
        return

    # 启动监听与总结
    try:
        await agent.start()
    except KeyboardInterrupt:
        pass
    finally:
        await agent.stop()
        agent.leave()


asyncio.run(main())
```

## 配置详解

meeting-agent 通过环境变量读取配置，`Config.from_env()` 会自动加载。所有环境变量如下：

| 环境变量 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `LLM_PROVIDER` | 否 | `deepseek` | LLM 提供商，可选 `openai` / `anthropic` / `deepseek` |
| `LLM_API_KEY` | 否（不总结时） | - | LLM API Key |
| `LLM_BASE_URL` | 否 | 各 provider 默认 | 自定义 LLM 接口地址（用于代理或自部署模型） |
| `LLM_MODEL` | 否 | 各 provider 默认 | 模型名称，如 `gpt-4o` / `claude-3-5-sonnet` / `deepseek-chat` |
| `LLM_TEMPERATURE` | 否 | `0.3` | 生成温度，越低越稳定 |
| `LLM_MAX_TOKENS` | 否 | `1024` | 单次总结最大输出 token 数 |
| `MEETING_POLL_INTERVAL` | 否 | `5` | 事件轮询间隔（秒），越小实时性越好但 API 压力越大 |
| `MEETING_SUMMARY_INTERVAL` | 否 | `120` | 总结触发间隔（秒） |
| `MEETING_TRANSCRIPT_BUFFER_SIZE` | 否 | `500` | 转写缓冲区最大事件数 |
| `MEETING_ENABLE_AUTO_RESPONSE` | 否 | `false` | 是否启用自动回复（话题切换/待办提醒时主动发消息） |
| `MEETING_ENABLE_TOPIC_TRACKING` | 否 | `true` | 是否启用话题追踪 |
| `MEETING_ENABLE_TODO_EXTRACTION` | 否 | `true` | 是否启用待办抽取 |
| `LARK_CLI_PATH` | 否 | `lark-cli` | `lark-cli` 可执行文件路径，未在 PATH 中时可显式指定 |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别，可选 `DEBUG` / `INFO` / `WARNING` / `ERROR` |

## 场景示例

### 场景1：日常会议记录

最常见用法：BOT 入会，全程自动总结，结束时离会。

```python
from meeting_agent import Config, MeetingAgent

config = Config.from_env()
agent = MeetingAgent(config)
agent.join("123456789")
await agent.start()
# 会议结束后
await agent.stop()
agent.leave()
```

### 场景2：技术评审会议

技术评审通常话题密集且待办较多，建议缩短总结间隔、开启话题追踪与待办抽取。

```bash
export MEETING_SUMMARY_INTERVAL=60
export MEETING_ENABLE_TOPIC_TRACKING=true
export MEETING_ENABLE_TODO_EXTRACTION=true
export LLM_TEMPERATURE=0.2
```

### 场景3：只监听不总结（不配 LLM）

不设置 `LLM_API_KEY` 时，`SummaryEngine` 不会启动，agent 仅监听事件并打印转写文本。

```python
from meeting_agent import Config, MeetingAgent

# 不设置 LLM 相关环境变量
config = Config.from_env()
agent = MeetingAgent(config)
agent.join("123456789")
await agent.start()  # 仅监听，不生成总结
```

## 自定义总结 Prompt

`SummaryEngine` 内置 `SUMMARY_SYSTEM_PROMPT` 常量，控制 LLM 的总结风格与格式。要自定义总结输出，可继承 `SummaryEngine` 并覆盖该常量：

```python
from meeting_agent.summary import SummaryEngine


class MySummaryEngine(SummaryEngine):
    SUMMARY_SYSTEM_PROMPT = """你是一名资深会议纪要助手。
请按以下格式输出：
1. 讨论要点（不超过3条）
2. 关键决策
3. 待办事项（含负责人）
语言要求：简洁、专业、中文。"""
```

然后将自定义类注入 `MeetingAgent`（或通过子类化 `MeetingAgent` 覆盖 `_build_summary_engine`）。这样无需改动核心代码即可调整总结风格。

## 调整轮询参数

两个关键参数需要权衡：

- `poll_interval`（事件轮询间隔）：
  - 越小实时性越好（转写、参会人变更更快被感知），但会增大 `lark-cli` 调用频率，可能触发限流。
  - 一般建议 `3~10` 秒；网络较差时可适当增大。
- `summary_interval`（总结触发间隔）：
  - 越小总结越频繁、越细粒度，但 LLM 调用次数与成本上升，且每次总结的文本量较少可能影响质量。
  - 一般建议 `60~300` 秒；短会议用小值，长会议用大值。

两者关系：`poll_interval` 决定事件刷新速度，`summary_interval` 决定总结刷新速度，二者独立可调。当 `summary_interval < poll_interval` 时没有意义（总结时缓冲区可能无新内容），建议保持 `summary_interval >= poll_interval * 5`。

## 常见问题

### 入会失败排查

- **现象**：`agent.join()` 返回 `False`，日志提示鉴权失败或权限不足。
- **排查**：
  1. 确认 BOT 已开通 VC Agent 内测权限。
  2. 确认 `lark-cli` 已完成 BOT 身份认证（`lark-cli auth status`）。
  3. 确认会议号正确且会议未结束。
  4. 若会议已设置"禁止机器人入会"，需由主持人手动放行或修改会议设置。

### 总结不生成

- **现象**：会议进行中但始终没有收到总结消息。
- **排查**：
  1. 确认已配置 `LLM_API_KEY` 且 provider 正确。
  2. 查看 `LOG_LEVEL=DEBUG` 日志，确认 `SummaryEngine` 是否启动、是否在调用 LLM。
  3. 确认转写缓冲区非空（参会人是否在发言、是否开启转写）。
  4. 确认 `summary_interval` 未设置过大。
  5. 若 LLM 调用报错，检查 API Key 余额、网络、`LLM_BASE_URL` 是否可达。

### 权限错误处理

- **现象**：调用 `list_active_meetings` 或发消息时返回 403 / 权限不足。
- **排查**：
  1. 区分 USER 与 BOT 身份：查询进行中会议用 USER 身份，入会与发消息用 BOT 身份，不可混用。
  2. 确认对应身份已开通所需 scope（如 `vc:meeting:read`、`vc:meeting:write`、`im:message:send` 等）。
  3. 重新执行 `lark-cli auth login` 刷新 token 后重试。
