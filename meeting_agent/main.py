"""
飞书会议Agent - 主入口
实时参会、监听转写、自主总结、会中对话
"""
import asyncio
import argparse
import logging
import signal
import sys
from typing import Optional

from .config import Config
from .lark_cli import LarkCLI, Identity
from .meeting import MeetingManager, MeetingListener, MeetingMessenger
from .summary import SummaryEngine, TopicTracker, TodoExtractor

logger = logging.getLogger(__name__)


# 配置日志
def setup_logging(level: str = "INFO"):
    """配置日志输出"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


class MeetingAgent:
    """飞书会议智能助手"""

    def __init__(self, config: Config):
        self.config = config

        # 初始化组件
        self.lark = LarkCLI(config.lark_cli_path)
        self.manager = MeetingManager(self.lark)
        self.listener: Optional[MeetingListener] = None
        self.messenger: Optional[MeetingMessenger] = None
        self.summary_engine: Optional[SummaryEngine] = None
        self.topic_tracker = TopicTracker()
        self.todo_extractor = TodoExtractor()

        # 状态
        self._running = False

    def join(self, meeting_number: str) -> bool:
        """
        加入会议

        Args:
            meeting_number: 9位会议号

        Returns:
            bool: 是否成功
        """
        try:
            meeting = self.manager.join(meeting_number)

            # 初始化监听器和消息发送器
            self.listener = MeetingListener(
                self.lark,
                meeting.meeting_id,
                self.config.meeting,
                Identity.BOT
            )

            self.messenger = MeetingMessenger(
                self.lark,
                meeting.meeting_id,
                Identity.BOT
            )

            # 发送入会通知
            self.messenger.notify_join()

            logger.info(f"成功加入会议: {meeting.title}")
            return True

        except Exception as e:
            logger.error(f"入会失败: {e}")
            return False

    async def start(self):
        """启动Agent（监听+总结）"""
        if not self.listener:
            logger.error("请先加入会议")
            return

        self._running = True

        # 初始化总结引擎
        if self.config.llm.api_key:
            self.summary_engine = SummaryEngine(
                self.config.llm,
                self.listener,
                self.messenger,
                self.config.meeting.summary_interval
            )
        else:
            logger.warning("未配置LLM API Key，将不会生成总结")

        # 设置回调
        self.listener.set_callbacks(
            on_transcript=self._on_transcript,
            on_chat=self._on_chat,
            on_participant_change=self._on_participant_change
        )

        # 启动监听
        await self.listener.start()

        # 启动总结引擎（并行）
        if self.summary_engine:
            asyncio.create_task(self.summary_engine.start())

        logger.info("Agent已启动，开始监听会议")

        # 持续监听循环
        try:
            for events in self.listener.listen_loop():
                if not self._running:
                    break
                # 事件已在回调中处理
        except Exception as e:
            logger.error(f"监听异常: {e}")

    async def _on_transcript(self, event):
        """处理转写事件"""
        logger.info(f"[转写] {event.sender_name}: {event.content}")

        # 更新话题追踪
        if self.config.meeting.enable_topic_tracking and event.content:
            self.topic_tracker.update(event.content)

        # 提取待办
        if self.config.meeting.enable_todo_extraction and event.content:
            todos = self.todo_extractor.extract_from_text(
                event.content,
                event.sender_name or ""
            )
            if todos:
                self.todo_extractor.add_todos(todos)
                logger.info(f"提取到待办: {len(todos)} 条")

    async def _on_chat(self, event):
        """处理聊天事件"""
        logger.info(f"[聊天] {event.sender_name}: {event.content}")

    async def _on_participant_change(self, event):
        """处理参会人变化"""
        logger.info(f"[参会人] {event.content}")

    async def stop(self):
        """停止Agent"""
        self._running = False

        # 停止监听
        if self.listener:
            await self.listener.stop()

        # 停止总结引擎
        if self.summary_engine:
            await self.summary_engine.stop()

        # 发送最终总结和待办
        if self.messenger:
            summary = self.summary_engine.get_last_summary() if self.summary_engine else None
            if summary:
                self.messenger.report_summary(summary.summary)

            todos = self.todo_extractor.get_todos_text()
            if todos != "暂无待办事项":
                self.messenger.send_text(todos)

            self.messenger.notify_leave()

        logger.info("Agent已停止")

    def leave(self) -> bool:
        """离开会议"""
        return self.manager.leave()

    def get_status(self) -> dict:
        """获取当前状态"""
        meeting = self.manager.get_current_meeting()
        current_topic = self.topic_tracker.get_current_topic()

        return {
            "meeting": meeting.title if meeting else None,
            "meeting_id": meeting.meeting_id if meeting else None,
            "is_running": self._running,
            "transcript_count": len(self.listener.get_transcripts()) if self.listener else 0,
            "current_topic": current_topic.name if current_topic else None,
            "todo_count": len(self.todo_extractor.get_todos()),
            "summary": self.summary_engine.get_last_summary().summary if self.summary_engine and self.summary_engine.get_last_summary() else None
        }


async def run_agent(meeting_number: str, config: Config):
    """运行Agent"""
    agent = MeetingAgent(config)

    # 注册信号处理
    def signal_handler(sig, frame):
        logger.info("收到退出信号...")
        asyncio.create_task(agent.stop())
        asyncio.create_task(agent.leave())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 加入会议
    if not agent.join(meeting_number):
        logger.error("无法加入会议")
        return

    # 启动监听和总结
    await agent.start()


def main():
    """CLI入口"""
    parser = argparse.ArgumentParser(
        description="飞书会议智能助手 - 实时参会、监听、总结"
    )

    parser.add_argument(
        "meeting_number",
        help="9位会议号"
    )

    parser.add_argument(
        "--provider",
        default="openai",
        choices=["openai", "anthropic", "deepseek"],
        help="LLM提供商"
    )

    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="LLM模型名称"
    )

    parser.add_argument(
        "--poll-interval",
        type=float,
        default=10.0,
        help="事件轮询间隔（秒）"
    )

    parser.add_argument(
        "--summary-interval",
        type=float,
        default=30.0,
        help="总结更新间隔（秒）"
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别"
    )

    args = parser.parse_args()

    # 配置日志
    setup_logging(args.log_level)

    # 加载配置
    config = Config.from_env()
    config.llm.provider = args.provider
    config.llm.model = args.model
    config.meeting.poll_interval = args.poll_interval
    config.meeting.summary_interval = args.summary_interval
    config.log_level = args.log_level

    # 检查会议号
    if len(args.meeting_number) != 9 or not args.meeting_number.isdigit():
        logger.error("会议号必须是9位纯数字")
        sys.exit(1)

    # 运行Agent
    try:
        asyncio.run(run_agent(args.meeting_number, config))
    except KeyboardInterrupt:
        logger.info("用户中断")


if __name__ == "__main__":
    main()