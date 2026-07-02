"""事件监听 - 实时获取会议转写、聊天、参会人变化"""
import asyncio
import logging
import time
from typing import Optional, Callable, List, AsyncGenerator
from collections import deque
from ..lark_cli import LarkCLI, Identity, Event
from ..config import MeetingConfig

logger = logging.getLogger(__name__)


class MeetingListener:
    """会议事件监听器"""

    def __init__(
        self,
        lark_cli: LarkCLI,
        meeting_id: str,
        config: MeetingConfig,
        identity: Identity = Identity.BOT
    ):
        self.lark = lark_cli
        self.meeting_id = meeting_id
        self.config = config
        self.identity = identity

        # 状态
        self._running = False
        self._page_token: Optional[str] = None
        self._last_poll_time: float = 0

        # 事件缓冲区
        self._transcript_buffer: deque = deque(maxlen=config.transcript_buffer_size)
        self._all_events: List[Event] = []

        # 回调函数
        self._on_transcript: Optional[Callable] = None
        self._on_chat: Optional[Callable] = None
        self._on_participant_change: Optional[Callable] = None

    def set_callbacks(
        self,
        on_transcript: Optional[Callable] = None,
        on_chat: Optional[Callable] = None,
        on_participant_change: Optional[Callable] = None
    ):
        """设置事件回调"""
        self._on_transcript = on_transcript
        self._on_chat = on_chat
        self._on_participant_change = on_participant_change

    async def start(self):
        """启动监听"""
        self._running = True
        logger.info(f"开始监听会议 {self.meeting_id}")

        # 先拉取一次当前所有可见事件
        await self._poll_events(initial=True)

    async def stop(self):
        """停止监听"""
        self._running = False
        logger.info(f"停止监听会议 {self.meeting_id}")

    async def _poll_events(self, initial: bool = False) -> List[Event]:
        """
        轮询会议事件

        Args:
            initial: 是否是首次拉取（拉取全部当前可见事件）

        Returns:
            List[Event]: 新获取的事件
        """
        if not self._running:
            return []

        try:
            # 使用page_token增量拉取，避免重复获取
            events, next_token = self.lark.get_meeting_events(
                self.meeting_id,
                self.identity,
                page_token=self._page_token if not initial else None,
                page_all=initial  # 首次拉取全部
            )

            # 更新page_token
            self._page_token = next_token
            self._last_poll_time = time.time()

            # 处理新事件
            new_events = self._process_events(events)

            return new_events

        except Exception as e:
            logger.error(f"获取事件失败: {e}")
            return []

    def _process_events(self, events: List[Event]) -> List[Event]:
        """
        处理事件，分类存储并触发回调

        Returns:
            List[Event]: 实际新增的事件（去重后）
        """
        # 简单去重：基于timestamp + sender_id + event_type
        new_events = []
        seen_keys = set()

        for event in self._all_events:
            key = f"{event.timestamp}|{event.sender_id}|{event.event_type}"
            seen_keys.add(key)

        for event in events:
            key = f"{event.timestamp}|{event.sender_id}|{event.event_type}"
            if key not in seen_keys:
                new_events.append(event)
                self._all_events.append(event)
                seen_keys.add(key)

                # 分类处理
                if event.event_type == "transcript":
                    self._transcript_buffer.append(event)
                    if self._on_transcript:
                        asyncio.create_task(self._on_transcript(event))

                elif event.event_type == "chat":
                    if self._on_chat:
                        asyncio.create_task(self._on_chat(event))

                elif "participant" in event.event_type:
                    if self._on_participant_change:
                        asyncio.create_task(self._on_participant_change(event))

        if new_events:
            logger.debug(f"收到 {len(new_events)} 个新事件")

        return new_events

    async def listen_loop(self) -> AsyncGenerator[List[Event], None]:
        """
        持续监听循环

        Yields:
            List[Event]: 每次轮询获取的新事件
        """
        await self.start()

        while self._running:
            # 等待轮询间隔
            await asyncio.sleep(self.config.poll_interval)

            # 获取新事件
            new_events = await self._poll_events()

            if new_events:
                yield new_events

    def get_transcripts(self, limit: Optional[int] = None) -> List[Event]:
        """
        获取转写记录

        Args:
            limit: 最大条数，None表示全部

        Returns:
            List[Event]: 写事件列表
        """
        transcripts = list(self._transcript_buffer)
        if limit:
            return transcripts[-limit:]
        return transcripts

    def get_all_events(self) -> List[Event]:
        """获取所有事件"""
        return self._all_events.copy()

    def get_transcript_text(self, include_speaker: bool = True) -> str:
        """
        获取转写文本（用于总结）

        Args:
            include_speaker: 是否包含说话人

        Returns:
            str: 格式化的转写文本
        """
        lines = []
        for event in self._transcript_buffer:
            if event.content:
                if include_speaker and event.sender_name:
                    lines.append(f"{event.sender_name}: {event.content}")
                else:
                    lines.append(event.content)
        return "\n".join(lines)

    @property
    def is_running(self) -> bool:
        """是否正在监听"""
        return self._running