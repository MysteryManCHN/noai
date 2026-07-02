# 架构设计

本文档描述 meeting-agent 的整体架构、模块划分、数据流、身份模型、并发模型以及扩展点。

## 整体架构

meeting-agent 采用分层架构，自上而下依次为：CLI/API 入口层、协调器层、业务模块层、底层封装层、外部依赖层。

```
┌─────────────────────────────────────────────┐
│                  CLI / API                   │
│              main.py / agent.py              │
├─────────────────────────────────────────────┤
│                MeetingAgent                  │
│         (协调器: 串联所有模块)                 │
├──────────┬──────────┬───────────┬───────────┤
│  Meeting │ Summary  │  Dialogue │   Lark    │
│  Module  │  Module  │           │   CLI     │
├──────────┼──────────┼───────────┼───────────┤
│ Manager  │ Engine   │ Messenger │ lark_cli  │
│ Listener │ Topics   │           │  .py      │
│ Messenger│ Todos    │           │           │
├──────────┴──────────┴───────────┴───────────┤
│              lark-cli (飞书API)               │
├─────────────────────────────────────────────┤
│         OpenAI / Anthropic / DeepSeek        │
└─────────────────────────────────────────────┘
```

最上层是用户接入入口（命令行 `main.py` 或 Python API `agent.py`），中间由 `MeetingAgent` 作为协调器串联所有业务模块，业务模块通过 `LarkCLI` 封装层调用 `lark-cli` 子进程，`lark-cli` 再与飞书服务端通信；总结相关模块在需要时调用 LLM 服务（OpenAI / Anthropic / DeepSeek 等）生成增量总结。

## 模块说明

各模块职责如下：

- **LarkCLI 封装层** (`lark_cli.py`)：封装 `lark-cli` 子进程调用，屏蔽命令行细节，对外提供类型安全的 Python 接口。所有与飞书服务端的交互（入会、离会、拉取事件、发消息、发表情）都经由本层完成，统一处理 JSON 解析、错误码、超时与重试。
- **Meeting 模块**：负责会议生命周期管理与会中事件处理。
  - `Manager`：负责入会 (`join`) / 离会 (`leave`) / 进行中会议发现 (`discover_active_meetings`)。
  - `Listener`：负责按 `poll_interval` 轮询 `lark-cli vc +meeting-events`，对事件去重后写入缓冲区，并通过回调通知上层。
  - `Messenger`：负责向会议发送文本消息和表情，以及加入/离开通知、总结和待办上报。
- **Summary 模块**：负责基于转写文本的智能总结与结构化信息抽取。
  - `Engine`：调用 LLM 对缓冲区中的转写文本进行增量总结，按 `summary_interval` 触发，并将结果交回 `Messenger` 发送。
  - `Topics`：基于关键词与上下文进行话题检测与切换追踪，输出话题历史与摘要。
  - `Todos`：基于 `TODO_PATTERNS` 正则规则从转写文本中抽取待办事项（含负责人、时间等）。
- **MeetingAgent 协调器** (`agent.py`)：串联上述模块，管理整体生命周期（初始化、入会、启动监听、启动总结、停止、离会），并对外暴露统一的 `join / start / stop / leave / get_status` 接口。

## 数据流

事件从飞书会议到总结输出的完整数据流如下：

1. `lark-cli vc +meeting-events` 以 JSON 形式返回会议事件流（转写、聊天、参会人变更等）。
2. `LarkCLI.get_meeting_events` 解析 JSON，构造强类型的 `Event` 对象列表。
3. `MeetingListener.listen_loop` 持续轮询事件，按 `event_id` 去重后写入内部缓冲区。
4. 缓冲区写入后触发回调：`_on_transcript` 处理转写事件，`_on_chat` 处理聊天消息，`_on_participant_change` 处理参会人变更。
5. `SummaryEngine` 定时（每 `summary_interval` 秒）从缓冲区取出未总结的转写文本，通过 `run_in_executor` 调用 LLM 生成增量总结。
6. `MeetingMessenger` 将生成的总结发回会议（文本消息）或上报待办事项。

整个链路单向流动，模块间通过回调与缓冲区解耦，便于独立测试与替换。

## 身份模型

`lark-cli` 支持两种身份：`USER`（用户身份）与 `BOT`（应用身份）。两种身份的使用场景与约束如下：

- **BOT 身份**：用于所有写操作，包括入会 (`join_meeting`)、离会 (`leave_meeting`)、会中消息发送 (`send_meeting_message`)、表情发送 (`send_meeting_reaction`)。BOT 需要应用具备 VC Agent 内测权限。
- **USER 身份**：用于只读查询，例如查询当前用户正在进行中的会议 (`list_active_meetings`)，以便在用户已经在会中时让 BOT 复用同一个 `meeting_id` 入会。
- **硬规则**：`meeting_id` 从哪种身份获取，后续对该 `meeting_id` 的操作必须使用相同身份。即如果 `meeting_id` 是 BOT 入会得到的，则后续发消息、拉事件、离会也必须用 BOT 身份；反之若 `meeting_id` 是从 USER 身份查询得到的，则后续操作也必须用 USER 身份。混用身份会导致鉴权失败。

## 并发模型

meeting-agent 基于 `asyncio` 实现单线程并发：

- `listen_loop` 是主事件循环，由 `MeetingListener.start` 创建为长期运行的 `asyncio.Task`，负责持续轮询事件。
- 事件回调（`_on_transcript` 等）通过 `asyncio.create_task` 异步执行，避免阻塞主轮询循环。
- LLM 调用通常是同步阻塞的 HTTP 请求，通过 `loop.run_in_executor(None, fn)` 投放到线程池执行，避免阻塞事件循环。
- `SummaryEngine` 的定时触发同样基于 `asyncio.sleep`，与 `listen_loop` 在同一事件循环内协同调度。

这种设计保证在单进程内既能持续接收事件，又能并发进行 LLM 总结，而无需引入多线程锁。

## 扩展点

meeting-agent 在多个层面预留了扩展点，便于定制化：

- **自定义 LLM**：实现 `LLMClient` 接口的 `generate(prompt: str) -> str` 方法，即可接入任意 LLM 提供商（自部署模型、内部网关等）。在 `Config.llm` 中指定 provider 后，`SummaryEngine` 会自动使用对应的 client。
- **自定义话题检测**：继承 `TopicTracker` 并重写 `detect_topic(text) -> Optional[str]`，可以替换默认的关键词匹配逻辑，例如接入语义相似度模型或基于规则引擎的话题分类。
- **自定义待办规则**：修改 `TodoExtractor` 的 `TODO_PATTERNS` 列表（正则 + 元信息），即可适配不同团队的待办表达习惯；也可重写 `extract_from_text` 实现更复杂的抽取逻辑（如基于 NER 模型）。
- **自定义消息格式**：重写 `MeetingMessenger` 的 `report_summary` / `report_todo` 等方法，可以调整输出到会议的文本格式（如 Markdown 卡片、富文本等）。
