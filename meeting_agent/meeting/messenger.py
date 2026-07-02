"""会中消息 - 发送文本、表情反馈"""
import logging
from typing import Optional, List
from ..lark_cli import LarkCLI, Identity

logger = logging.getLogger(__name__)


# 可用的会中表情类型
VALID_EMOJI_TYPES = [
    # 普通表情
    "LOVE",       # ❤️
    "SMILE",      # 😊
    "THUMBSUP",   # 👍
    "THUMBSDOWN", # 👎
    "CLAP",       # 👏
    "LAUGH",      # 😂
    "OK",         # 👌

    # 会议反馈专用
    "VC_NoSound",      # 听不到声音
    "VC_CanNotSee",    # 看不到画面
    "VC_SoundsClear",  # 声音清晰
    "VC_LooksGood",    # 效果不错
]


class MeetingMessenger:
    """会中消息发送器"""

    def __init__(
        self,
        lark_cli: LarkCLI,
        meeting_id: str,
        identity: Identity = Identity.BOT
    ):
        self.lark = lark_cli
        self.meeting_id = meeting_id
        self.identity = identity

    def send_text(self, text: str) -> bool:
        """
        发送文本消息

        Args:
            text: 消息内容

        Returns:
            bool: 是否成功
        """
        if not text or not text.strip():
            logger.warning("消息内容为空")
            return False

        try:
            self.lark.send_meeting_message(self.meeting_id, text, self.identity)
            logger.info(f"发送消息: {text[:30]}...")
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False

    def send_reaction(self, emoji_type: str) -> bool:
        """
        发送表情/反馈

        Args:
            emoji_type: 表情类型，必须来自VALID_EMOJI_TYPES

        Returns:
            bool: 是否成功
        """
        if emoji_type not in VALID_EMOJI_TYPES:
            logger.warning(f"无效的表情类型: {emoji_type}")
            logger.info(f"可用类型: {VALID_EMOJI_TYPES}")
            return False

        try:
            self.lark.send_meeting_reaction(self.meeting_id, emoji_type, self.identity)
            logger.info(f"发送表情: {emoji_type}")
            return True
        except Exception as e:
            logger.error(f"发送表情失败: {e}")
            return False

    # ========== 预设消息 ==========

    def notify_join(self) -> bool:
        """通知机器人已入会"""
        return self.send_text("🤖 会议助手已加入，开始记录会议内容")

    def notify_leave(self) -> bool:
        """通知机器人即将离会"""
        return self.send_text("🤖 会议助手即将离开，会议记录已完成")

    def report_summary(self, summary: str) -> bool:
        """
        发送总结报告

        Args:
            summary: 总结内容
        """
        # 截断过长的总结
        if len(summary) > 500:
            summary = summary[:500] + "..."

        message = f"📋 会议总结:\n{summary}"
        return self.send_text(message)

    def report_todo(self, todos: List[str]) -> bool:
        """
        发送待办事项

        Args:
            todos: 待办列表
        """
        if not todos:
            return False

        lines = ["📝 待办事项:"]
        for i, todo in enumerate(todos, 1):
            lines.append(f"{i}. {todo}")

        message = "\n".join(lines)
        return self.send_text(message)

    def feedback_sound_issue(self) -> bool:
        """反馈声音问题"""
        return self.send_reaction("VC_NoSound")

    def feedback_video_issue(self) -> bool:
        """反馈画面问题"""
        return self.send_reaction("VC_CanNotSee")

    def feedback_good(self) -> bool:
        """反馈效果好"""
        return self.send_reaction("VC_LooksGood")

    def thumbs_up(self) -> bool:
        """发送点赞"""
        return self.send_reaction("THUMBSUP")

    @staticmethod
    def get_valid_emoji_types() -> List[str]:
        """获取所有可用的表情类型"""
        return VALID_EMOJI_TYPES.copy()