"""待办提取 - 从会议对话中识别待办事项"""
import logging
import re
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TodoItem:
    """待办事项"""
    content: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None
    priority: str = "medium"  # high / medium / low
    source: str = ""  # 来源（说话人）
    context: str = ""  # 上下文


class TodoExtractor:
    """待办事项提取器"""

    # 待办关键词模式
    TODO_PATTERNS = [
        # 明确的行动词
        r"(需要|要|得|应该|必须)\s*(完成|做|处理|解决|跟进|确认|准备|整理|提交|撰写|编写|开发|修复)",
        # 时间相关
        r"(明天|下周|本周|月底|周[一二三四五六日])\s*(要|需要|得)\s*.+",
        # 分配任务
        r"(@\w+|\w+)\s*(负责|跟进|处理|完成|做)",
        # 待办标记
        r"(待办|todo|TODO|待处理|待确认|待跟进)[:\s]",
        # 决议类
        r"(决定|决议|确定)[:\s].+(由|交给|分配给)\s*\w+",
    ]

    # 负责人提取模式
    ASSIGNEE_PATTERNS = [
        r"@(\w+)",
        r"(由|交给|分配给|负责)\s*(\w+)",
        r"(\w+)\s*(负责|跟进|处理)",
    ]

    # 时间提取模式
    DEADLINE_PATTERNS = [
        r"(明天|后天)",
        r"(下周|本周|这周)",
        r"(周[一二三四五六日])",
        r"(月底|月底前)",
        r"(\d+月\d+[日号])",
        r"(before|by|before)\s+(\d+)",
    ]

    def __init__(self):
        self._todos: List[TodoItem] = []

    def extract_from_text(self, text: str, speaker: str = "") -> List[TodoItem]:
        """
        从文本中提取待办事项

        Args:
            text: 转写文本
            speaker: 说话人

        Returns:
            List[TodoItem]: 提取的待办事项
        """
        todos = []

        # 按句子分割
        sentences = re.split(r'[。！？;,;\n]', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 检查是否包含待办模式
            is_todo = False
            for pattern in self.TODO_PATTERNS:
                if re.search(pattern, sentence, re.IGNORECASE):
                    is_todo = True
                    break

            if is_todo:
                # 提取负责人
                assignee = self._extract_assignee(sentence)

                # 提取截止时间
                deadline = self._extract_deadline(sentence)

                # 创建待办项
                todo = TodoItem(
                    content=sentence,
                    assignee=assignee,
                    deadline=deadline,
                    source=speaker,
                    context=text[:200] if len(text) > 200 else text
                )

                todos.append(todo)
                logger.debug(f"提取待办: {sentence} @ {assignee or '待定'}")

        return todos

    def _extract_assignee(self, text: str) -> Optional[str]:
        """提取负责人"""
        for pattern in self.ASSIGNEE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                # 返回最后一个分组（负责人名称）
                groups = match.groups()
                return groups[-1] if groups else None
        return None

    def _extract_deadline(self, text: str) -> Optional[str]:
        """提取截止时间"""
        for pattern in self.DEADLINE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def add_todos(self, todos: List[TodoItem]):
        """添加待办事项"""
        # 简单去重：基于内容相似度
        for todo in todos:
            is_duplicate = False
            for existing in self._todos:
                if self._is_similar(todo.content, existing.content):
                    is_duplicate = True
                    break

            if not is_duplicate:
                self._todos.append(todo)

    def _is_similar(self, text1: str, text2: str) -> bool:
        """判断两个文本是否相似"""
        # 简单的文本相似度判断
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return False

        intersection = words1 & words2
        union = words1 | words2

        similarity = len(intersection) / len(union) if union else 0

        return similarity > 0.6  # 60%以上相似认为是重复

    def get_todos(self) -> List[TodoItem]:
        """获取所有待办事项"""
        return self._todos.copy()

    def get_todos_by_assignee(self, assignee: str) -> List[TodoItem]:
        """按负责人获取待办"""
        return [t for t in self._todos if t.assignee == assignee]

    def get_todos_text(self) -> str:
        """
        获取待办文本格式（用于报告）

        Returns:
            str: 格式化的待办列表
        """
        if not self._todos:
            return "暂无待办事项"

        lines = ["📝 待办事项:"]
        for i, todo in enumerate(self._todos, 1):
            assignee = f" @{todo.assignee}" if todo.assignee else ""
            deadline = f" [{todo.deadline}]" if todo.deadline else ""
            lines.append(f"{i}. {todo.content}{assignee}{deadline}")

        return "\n".join(lines)

    def clear(self):
        """清空待办列表"""
        self._todos = []

    def reset(self):
        """重置状态"""
        self.clear()