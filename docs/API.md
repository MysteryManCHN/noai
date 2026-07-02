# API 文档

本文档列出 meeting-agent 对外暴露的所有公共类与方法。所有类均可从顶层包 `meeting_agent` 直接导入。

## MeetingAgent

主类，协调所有模块（Meeting / Summary / LarkCLI），管理整体生命周期。

### 方法

- `__init__(config: Config)`：根据 `Config` 实例化 agent，内部构建 `LarkCLI`、`MeetingManager`、`MeetingListener`、`MeetingMessenger`、`SummaryEngine` 等模块。
- `join(meeting_number: str) -> bool`：同步入会。传入 9 位会议号，成功返回 `True` 并记录 `meeting_id` 与所用身份；失败返回 `False`。
- `async start() -> None`：异步启动监听与总结。会启动 `MeetingListener.listen_loop` 与（若配置了 LLM）`SummaryEngine` 的定时总结循环，阻塞直到调用 `stop` 或被取消。
- `async stop() -> None`：异步停止监听与总结，清理后台任务。通常在 `start` 之后通过 `try/finally` 调用。
- `leave() -> bool`：同步离会，使用与入会相同的身份调用 `LarkCLI.leave_meeting`。返回是否成功。
- `get_status() -> dict`：返回当前状态快照，包含是否已入会、`meeting_id`、当前话题、最近一次总结、待办数量等。

## Config

配置类，聚合 LLM、Meeting 等子配置。

### 类方法

- `Config.from_env() -> Config`：从环境变量读取所有配置项并构造 `Config` 实例。未设置的项使用默认值。

### 属性

- `llm: LLMConfig`：LLM 相关配置。
- `meeting: MeetingConfig`：会议相关运行参数。
- `lark_cli_path: str`：`lark-cli` 可执行文件路径，默认 `lark-cli`。
- `log_level: str`：日志级别，默认 `INFO`。

## LLMConfig

LLM 提供商相关配置。

### 属性

- `provider: str`：提供商，可选 `openai` / `anthropic` / `deepseek`。
- `api_key: str`：API Key。
- `base_url: str`：自定义接口地址（用于代理或自部署模型）。
- `model: str`：模型名称。
- `temperature: float`：生成温度。
- `max_tokens: int`：单次输出最大 token 数。

## MeetingConfig

会议运行参数。

### 属性

- `poll_interval: int`：事件轮询间隔（秒）。
- `summary_interval: int`：总结触发间隔（秒）。
- `transcript_buffer_size: int`：转写缓冲区最大事件数。
- `enable_auto_response: bool`：是否启用自动回复。
- `enable_topic_tracking: bool`：是否启用话题追踪。
- `enable_todo_extraction: bool`：是否启用待办抽取。

## LarkCLI

封装 `lark-cli` 子进程调用的底层类，提供类型安全的 Python 接口。所有方法均为同步阻塞调用。

### 方法

- `join_meeting(meeting_number: str, identity: str) -> MeetingInfo`：以指定身份加入会议，返回 `MeetingInfo`（含 `meeting_id` 等）。
- `leave_meeting(meeting_id: str, identity: str) -> bool`：以指定身份离开会议。
- `list_active_meetings(identity: str, user_id: str) -> List[MeetingInfo]`：以 USER 身份查询当前用户正在进行中的会议列表。
- `get_meeting_events(meeting_id: str, identity: str, page_token: str = "", page_all: bool = False) -> tuple[List[Event], str]`：拉取会议事件，返回 `(事件列表, 下一页 token)`。
- `send_meeting_message(meeting_id: str, text: str, identity: str) -> bool`：向会议发送文本消息。
- `send_meeting_reaction(meeting_id: str, emoji_type: str, identity: str) -> bool`：向会议发送表情回应。

> 注：`identity` 取值为 `"user"` 或 `"bot"`，且必须与获取 `meeting_id` 时所用身份一致。

## MeetingManager

会议生命周期管理。

### 方法

- `join(meeting_number: str) -> MeetingInfo`：BOT 身份入会，返回会议信息。
- `leave() -> bool`：使用入会时记录的 `meeting_id` 与身份离会。
- `discover_active_meetings(user_id: str, meeting_number: str = "") -> List[MeetingInfo]`：以 USER 身份查询当前用户正在进行中的会议；可传入会议号过滤。

## MeetingListener

会议事件轮询与缓冲。

### 方法

- `set_callbacks(on_transcript=None, on_chat=None, on_participant_change=None)`：注册事件回调，回调签名均为 `async def callback(event: Event) -> None`。
- `async start() -> None`：启动后台 `listen_loop` 任务。
- `async stop() -> None`：停止轮询并清理任务。
- `async listen_loop() -> AsyncGenerator`：事件轮询主循环，持续拉取事件、去重、写缓冲区并触发回调。
- `get_transcripts(limit: int = 0) -> List[Event]`：返回缓冲区中的转写事件，`limit=0` 表示全部。
- `get_transcript_text(include_speaker: bool = True) -> str`：将缓冲区转写事件拼接为纯文本，可选项包含发言人。

## MeetingMessenger

会议消息发送。

### 方法

- `send_text(text: str) -> bool`：发送文本消息。
- `send_reaction(emoji_type: str) -> bool`：发送表情回应。
- `notify_join() -> bool`：发送"已加入会议"通知。
- `notify_leave() -> bool`：发送"即将离开会议"通知。
- `report_summary(summary: str) -> bool`：将总结以文本消息形式发回会议。
- `report_todo(todos: list) -> bool`：将待办事项列表发回会议。

## SummaryEngine

基于 LLM 的增量总结引擎。

### 方法

- `async start() -> None`：启动定时总结循环。
- `async stop() -> None`：停止总结循环。
- `async get_current_topic() -> str`：返回当前话题（若开启话题追踪），否则返回空字符串。
- `async extract_todos() -> List[str]`：从最近转写文本中抽取待办事项列表。
- `get_last_summary() -> Optional[SummaryResult]`：返回最近一次总结结果，无则返回 `None`。

## TopicTracker

话题检测与追踪。

### 方法

- `detect_topic(text: str) -> Optional[str]`：基于关键词检测文本所属话题，命中返回话题名，否则返回 `None`。
- `update(new_text: str) -> Optional[Topic]`：用新文本更新话题状态；若发生话题切换则返回新的 `Topic`，否则返回 `None`。
- `get_current_topic() -> Optional[Topic]`：返回当前话题对象。
- `get_topic_history() -> List[Topic]`：返回话题切换历史。
- `get_topic_summary() -> str`：返回所有话题的概要文本。

## TodoExtractor

待办事项抽取。

### 方法

- `extract_from_text(text: str, speaker: str = "") -> List[TodoItem]`：从文本中抽取待办事项，`speaker` 用于记录提出人。
- `add_todos(todos: List[TodoItem])`：追加待办事项到内部列表。
- `get_todos() -> List[TodoItem]`：返回全部待办事项。
- `get_todos_text() -> str`：将待办事项格式化为纯文本，便于发送到会议。
