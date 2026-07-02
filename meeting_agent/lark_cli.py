"""lark-cli 封装 - 统一的飞书会议API调用接口"""
import subprocess
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Identity(Enum):
    """身份类型"""
    USER = "user"
    BOT = "bot"


@dataclass
class MeetingInfo:
    """会议信息"""
    meeting_id: str
    meeting_no: str  # 9位会议号
    title: str
    status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None


@dataclass
class Event:
    """会议事件"""
    event_type: str  # transcript / chat / participant_join / participant_leave / share_start / share_end
    timestamp: str
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    content: Optional[str] = None
    raw_data: Dict[str, Any] = None


class LarkCLI:
    """lark-cli 命令封装"""

    def __init__(self, cli_path: str):
        self.cli_path = cli_path
        self._check_cli()

    def _check_cli(self):
        """检查CLI是否可用"""
        try:
            result = self._run_command(["--version"])
            logger.info(f"lark-cli version: {result.strip() if result else 'unknown'}")
        except Exception as e:
            logger.warning(f"Cannot get lark-cli version: {e}")

    def _run_command(self, args: List[str], capture_json: bool = False) -> Optional[str]:
        """执行lark-cli命令"""
        cmd = [self.cli_path] + args
        logger.debug(f"Running: {cmd}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode != 0:
                logger.error(f"Command failed: {result.stderr}")
                raise RuntimeError(f"lark-cli error: {result.stderr}")

            output = result.stdout.strip()
            if capture_json and output:
                # 尝试解析JSON
                try:
                    return json.loads(output)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON: {output[:200]}")
                    return output
            return output

        except subprocess.TimeoutExpired:
            logger.error("Command timeout")
            raise RuntimeError("lark-cli command timeout")
        except Exception as e:
            logger.error(f"Command error: {e}")
            raise

    # ========== 会议管理 ==========

    def join_meeting(self, meeting_number: str, identity: Identity = Identity.BOT) -> MeetingInfo:
        """
        加入会议（9位会议号）

        Args:
            meeting_number: 9位纯数字会议号
            identity: BOT身份入会（应用机器人真实入会）

        Returns:
            MeetingInfo: 会议信息，包含meeting_id（后续操作必需）
        """
        args = [
            "vc", "+meeting-join",
            "--as", identity.value,
            "--meeting-number", meeting_number,
            "--format", "json"
        ]

        result = self._run_command(args, capture_json=True)
        if result and isinstance(result, dict):
            data = result.get("data", {}).get("meeting", {})
            return MeetingInfo(
                meeting_id=str(data.get("id", "")),
                meeting_no=str(data.get("meeting_no", "")),
                title=data.get("topic", ""),
                status=data.get("status", "")
            )
        raise RuntimeError("Failed to join meeting")

    def leave_meeting(self, meeting_id: str, identity: Identity = Identity.BOT) -> bool:
        """
        离开会议

        Args:
            meeting_id: 长数字会议ID（来自join返回）
            identity: BOT身份离会
        """
        args = [
            "vc", "+meeting-leave",
            "--as", identity.value,
            "--meeting-id", meeting_id
        ]

        self._run_command(args)
        logger.info(f"Left meeting: {meeting_id}")
        return True

    def list_active_meetings(
        self,
        identity: Identity = Identity.USER,
        user_id: Optional[str] = None
    ) -> List[MeetingInfo]:
        """
        获取当前进行中的会议

        Args:
            identity: USER查当前登录用户的会；BOT查目标用户且bot也在会中的会议
            user_id: BOT身份时必需，目标用户open_id (ou_...)

        Returns:
            List[MeetingInfo]: 当前进行中的会议列表
        """
        args = [
            "vc", "+meeting-list-active",
            "--as", identity.value,
            "--format", "json"
        ]

        if identity == Identity.BOT and user_id:
            args.extend(["--user-id", user_id])

        result = self._run_command(args, capture_json=True)
        meetings = []

        if result and isinstance(result, dict):
            data = result.get("data", {})
            items = data if isinstance(data, list) else data.get("meetings", [])

            for item in items:
                meetings.append(MeetingInfo(
                    meeting_id=str(item.get("meeting_id", "")),
                    meeting_no=str(item.get("meeting_no", "")),
                    title=item.get("meeting_title", ""),
                    status="active"
                ))

        return meetings

    # ========== 事件监听 ==========

    def get_meeting_events(
        self,
        meeting_id: str,
        identity: Identity = Identity.BOT,
        page_token: Optional[str] = None,
        page_all: bool = True
    ) -> tuple[List[Event], Optional[str]]:
        """
        获取会议事件（转写、聊天、参会人变化等）

        Args:
            meeting_id: 长数字会议ID
            identity: 与meeting_id来源一致的身份
            page_token: 分页token，用于增量拉取
            page_all: 是否拉取全部当前可见事件

        Returns:
            (events, next_page_token): 事件列表和下次拉取的token
        """
        args = [
            "vc", "+meeting-events",
            "--as", identity.value,
            "--meeting-id", meeting_id,
            "--format", "json"
        ]

        if page_all:
            args.append("--page-all")

        if page_token:
            args.extend(["--page-token", page_token])

        result = self._run_command(args, capture_json=True)
        events = []
        next_token = None

        if result and isinstance(result, dict):
            data = result.get("data", {})
            items = data.get("events", [])

            for item in items:
                event_type = item.get("event_type", "")
                events.append(Event(
                    event_type=event_type,
                    timestamp=item.get("event_time", ""),
                    sender_id=item.get("sender", {}).get("id"),
                    sender_name=item.get("sender", {}).get("name"),
                    content=self._extract_content(item, event_type),
                    raw_data=item
                ))

            next_token = data.get("page_token")

        return events, next_token

    def _extract_content(self, item: Dict, event_type: str) -> Optional[str]:
        """提取事件内容"""
        if event_type == "transcript":
            # 转写事件
            return item.get("transcript", {}).get("text")
        elif event_type == "chat":
            # 聊天事件
            return item.get("chat", {}).get("content")
        elif "participant" in event_type:
            # 参会人事件
            name = item.get("participant", {}).get("name", "")
            action = "加入" if "join" in event_type else "离开"
            return f"{name} {action}会议"
        elif "share" in event_type:
            # 共享事件
            sharer = item.get("share", {}).get("sharer_name", "")
            action = "开始" if "start" in event_type else "结束"
            return f"{sharer} {action}共享"
        return None

    # ========== 会中消息 ==========

    def send_meeting_message(
        self,
        meeting_id: str,
        text: str,
        identity: Identity = Identity.BOT
    ) -> bool:
        """
        发送会中文本消息

        Args:
            meeting_id: 长数字会议ID
            text: 消息内容
            identity: 与meeting_id来源一致
        """
        args = [
            "vc", "+meeting-message-send",
            "--as", identity.value,
            "--meeting-id", meeting_id,
            "--msg-type", "text",
            "--text", text
        ]

        self._run_command(args)
        logger.info(f"Sent message: {text[:50]}...")
        return True

    def send_meeting_reaction(
        self,
        meeting_id: str,
        emoji_type: str,
        identity: Identity = Identity.BOT
    ) -> bool:
        """
        发送会中表情/反馈

        Args:
            meeting_id: 长数字会议ID
            emoji_type: 表情类型，如 LOVE / THUMBSUP / VC_NoSound / VC_CanNotSee 等
            identity: 与meeting_id来源一致
        """
        args = [
            "vc", "+meeting-message-send",
            "--as", identity.value,
            "--meeting-id", meeting_id,
            "--msg-type", "reaction",
            "--emoji-type", emoji_type
        ]

        self._run_command(args)
        logger.info(f"Sent reaction: {emoji_type}")
        return True