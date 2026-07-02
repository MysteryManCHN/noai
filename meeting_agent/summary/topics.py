"""话题追踪 - 识别和跟踪会议讨论主题"""
import logging
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Topic:
    """讨论话题"""
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    keywords: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class TopicTracker:
    """话题追踪器"""

    # 关键词映射到话题的简单规则
    TOPIC_KEYWORDS = {
        "项目进度": ["进度", "里程碑", "完成", "进展", "deadline", "截止"],
        "技术方案": ["架构", "技术", "方案", "实现", "接口", "API", "数据库", "系统"],
        "产品设计": ["设计", "用户", "体验", "界面", "功能", "需求", "产品"],
        "团队协作": ["协作", "沟通", "流程", "规范", "团队", "分工"],
        "预算成本": ["预算", "成本", "费用", "资源", "投入"],
        "风险问题": ["风险", "问题", "难点", "挑战", "阻碍", "bug", "故障"],
    }

    def __init__(self):
        self._topics: List[Topic] = []
        self._current_topic: Optional[Topic] = None
        self._topic_history: List[str] = []

    def detect_topic(self, text: str) -> Optional[str]:
        """
        从文本中检测话题

        Args:
            text: 转写文本

        Returns:
            Optional[str]: 检测到的话题名称
        """
        # 基于关键词匹配
        best_match = None
        max_score = 0

        text_lower = text.lower()

        for topic_name, keywords in self.TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)

            if score > max_score:
                max_score = score
                best_match = topic_name

        # 至少匹配1个关键词才认为是有效话题
        if max_score >= 1:
            return best_match

        return None

    def update(self, new_text: str) -> Optional[Topic]:
        """
        更新话题追踪状态

        Args:
            new_text: 新的转写文本

        Returns:
            Optional[Topic]: 如果话题发生变化，返回新话题
        """
        detected = self.detect_topic(new_text)
        now = datetime.now()

        # 没有检测到明确话题
        if not detected:
            return None

        # 话题发生变化
        if self._current_topic and self._current_topic.name != detected:
            # 结束当前话题
            self._current_topic.end_time = now
            self._current_topic.duration_seconds = (
                now - self._current_topic.start_time
            ).total_seconds()

            self._topics.append(self._current_topic)
            self._topic_history.append(self._current_topic.name)

            logger.info(
                f"话题切换: {self._current_topic.name} -> {detected}"
            )

        # 开始新话题
        if not self._current_topic or self._current_topic.name != detected:
            self._current_topic = Topic(
                name=detected,
                start_time=now,
                keywords=self.TOPIC_KEYWORDS.get(detected, [])
            )
            return self._current_topic

        # 话题未变化
        return None

    def get_current_topic(self) -> Optional[Topic]:
        """获取当前话题"""
        return self._current_topic

    def get_topic_history(self) -> List[Topic]:
        """获取话题历史"""
        return self._topics.copy()

    def get_topic_summary(self) -> str:
        """
        获取话题变迁摘要

        Returns:
            str: 话题变迁的简要描述
        """
        if not self._topics and not self._current_topic:
            return "尚未识别到明确话题"

        lines = []

        # 历史话题
        for topic in self._topics:
            duration = f"({int(topic.duration_seconds)}秒)"
            lines.append(f"- {topic.name} {duration}")

        # 当前话题
        if self._current_topic:
            lines.append(f"- 当前: {self._current_topic.name}")

        return "\n".join(lines)

    def reset(self):
        """重置追踪状态"""
        self._topics = []
        self._current_topic = None
        self._topic_history = []