"""
飞书会议智能助手 (Feishu Meeting Agent)
=======================================
一个不依赖飞书自带AI总结的独立会议Agent，支持：
- 应用机器人真实入会
- 实时监听会议事件（转写、聊天、参会人变化）
- 自主增量总结（接入 OpenAI / Anthropic / DeepSeek）
- 会中智能对话与提醒
- 话题追踪与待办提取

快速开始::
    from meeting_agent import Config, MeetingAgent

    config = Config.from_env()
    agent = MeetingAgent(config)
    agent.join("123456789")
    await agent.start()
"""

__version__ = "1.0.0"
__author__ = "Feishu Meeting Agent Contributors"
__license__ = "MIT"

from .config import Config, LLMConfig, MeetingConfig
from .lark_cli import LarkCLI, Identity, MeetingInfo, Event
from .meeting import MeetingManager, MeetingListener, MeetingMessenger
from .summary import SummaryEngine, TopicTracker, TodoExtractor
from .main import MeetingAgent, setup_logging

__all__ = [
    "MeetingAgent",
    "Config",
    "LLMConfig",
    "MeetingConfig",
    "LarkCLI",
    "Identity",
    "MeetingInfo",
    "Event",
    "MeetingManager",
    "MeetingListener",
    "MeetingMessenger",
    "SummaryEngine",
    "TopicTracker",
    "TodoExtractor",
    "setup_logging",
    "__version__",
]