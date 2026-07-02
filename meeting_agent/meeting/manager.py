"""会议管理 - 入会、离会、发现进行中会议"""
import logging
from typing import Optional, List
from ..lark_cli import LarkCLI, Identity, MeetingInfo

logger = logging.getLogger(__name__)


class MeetingManager:
    """会议生命周期管理"""

    def __init__(self, lark_cli: LarkCLI):
        self.lark = lark_cli
        self.current_meeting: Optional[MeetingInfo] = None
        self.identity = Identity.BOT  # 默认使用应用机器人身份

    def join(self, meeting_number: str) -> MeetingInfo:
        """
        加入会议

        Args:
            meeting_number: 9位纯数字会议号

        Returns:
            MeetingInfo: 会议信息，包含meeting_id

        Raises:
            ValueError: 会议号格式错误
            RuntimeError: 入会失败
        """
        # 验证会议号格式
        if not meeting_number or len(meeting_number) != 9 or not meeting_number.isdigit():
            raise ValueError("会议号必须是9位纯数字")

        logger.info(f"正在加入会议: {meeting_number}")

        try:
            meeting = self.lark.join_meeting(meeting_number, self.identity)
            self.current_meeting = meeting
            logger.info(f"成功加入会议: {meeting.title} (ID: {meeting.meeting_id})")
            return meeting
        except Exception as e:
            logger.error(f"入会失败: {e}")
            raise RuntimeError(f"无法加入会议 {meeting_number}: {e}")

    def leave(self) -> bool:
        """
        离开当前会议

        Returns:
            bool: 是否成功离会
        """
        if not self.current_meeting:
            logger.warning("当前没有在会议中")
            return False

        meeting_id = self.current_meeting.meeting_id
        logger.info(f"正在离开会议: {meeting_id}")

        try:
            self.lark.leave_meeting(meeting_id, self.identity)
            self.current_meeting = None
            logger.info("已离开会议")
            return True
        except Exception as e:
            logger.error(f"离会失败: {e}")
            return False

    def discover_active_meetings(
        self,
        user_id: Optional[str] = None,
        meeting_number: Optional[str] = None
    ) -> List[MeetingInfo]:
        """
        发现当前进行中的会议

        Args:
            user_id: 目标用户open_id (ou_...)，用于BOT身份查询
            meeting_number: 如果提供，会尝试匹配这个9位会议号

        Returns:
            List[MeetingInfo]: 进行中的会议列表
        """
        # 用户身份查当前登录用户的会议
        meetings = self.lark.list_active_meetings(Identity.USER)

        # 如果没找到，尝试用应用身份查（需要user_id）
        if not meetings and user_id:
            meetings = self.lark.list_active_meetings(Identity.BOT, user_id)

        # 按会议号过滤
        if meeting_number and meetings:
            meetings = [m for m in meetings if m.meeting_no == meeting_number]

        logger.info(f"发现 {len(meetings)} 个进行中的会议")
        return meetings

    def get_current_meeting(self) -> Optional[MeetingInfo]:
        """获取当前会议信息"""
        return self.current_meeting

    def set_identity(self, identity: Identity):
        """设置身份类型"""
        self.identity = identity
        logger.info(f"切换身份: {identity.value}")