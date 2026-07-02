"""实时总结引擎 - 增量生成会议总结"""
import asyncio
import logging
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from ..config import LLMConfig
from ..meeting.listener import MeetingListener
from ..meeting.messenger import MeetingMessenger

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    """总结结果"""
    summary: str  # 会议总结
    key_points: List[str] = field(default_factory=list)  # 关键要点
    current_topic: str = ""  # 当前讨论话题
    decisions: List[str] = field(default_factory=list)  # 决议
    todos: List[str] = field(default_factory=list)  # 待办
    timestamp: float = 0.0  # 生成时间


class LLMClient:
    """LLM客户端 - 支持OpenAI/Anthropic/DeepSeek"""

    def __init__(self, config: LLMConfig):
        self.config = config

        # 检查API Key
        if not config.api_key:
            raise ValueError(f"缺少API Key: {config.provider}")

        # 根据provider选择客户端
        self._client = None
        self._init_client()

    def _init_client(self):
        """初始化LLM客户端"""
        provider = self.config.provider.lower()

        if provider == "openai" or provider == "deepseek":
            # OpenAI兼容接口
            try:
                import openai

                self._client = openai.OpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url
                )
            except ImportError:
                raise ImportError("请安装openai: pip install openai")

        elif provider == "anthropic":
            try:
                import anthropic

                self._client = anthropic.Anthropic(
                    api_key=self.config.api_key
                )
            except ImportError:
                raise ImportError("请安装anthropic: pip install anthropic")

        else:
            raise ValueError(f"不支持的LLM提供商: {provider}")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        生成文本

        Args:
            prompt: 用户输入
            system_prompt: 系统提示（可选）

        Returns:
            str: 生成的文本
        """
        provider = self.config.provider.lower()

        try:
            if provider in ["openai", "deepseek"]:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )

                return response.choices[0].message.content

            elif provider == "anthropic":
                response = self._client.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    system=system_prompt or "",
                    messages=[{"role": "user", "content": prompt}]
                )

                return response.content[0].text

        except Exception as e:
            logger.error(f"LLM生成失败: {e}")
            raise RuntimeError(f"LLM调用失败: {e}")

    async def generate_async(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """异步生成"""
        # 在单独线程中执行，避免阻塞
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate(prompt, system_prompt)
        )


class SummaryEngine:
    """实时总结引擎"""

    # 总结系统提示
    SUMMARY_SYSTEM_PROMPT = """你是一个会议总结助手。你的任务是根据会议转写内容生成简洁、准确的总结。

要求：
1. 用简洁的语言总结讨论的主要内容和结论
2. 识别关键要点（最多5条）
3. 识别做出的决议或决策
4. 识别待办事项（如有）
5. 指出当前正在讨论的话题
6. 使用中文，保持专业、客观的语气

输出格式：
## 会议总结
[一句话概括会议主题和进展]

## 关键要点
- [要点1]
- [要点2]
...

## 当前话题
[正在讨论的主题]

## 决议
- [决议1]

## 待办
- [待办1] @负责人
"""

    # 增量总结用户提示
    SUMMARY_PROMPT_TEMPLATE = """以下是会议的转写记录，请生成总结：

{transcript}

请按要求的格式输出总结内容。"""

    # 快速话题识别提示
    TOPIC_PROMPT = """以下是最近的会议发言，请用一句话概括当前正在讨论的话题：

{recent_text}

只输出话题，不要其他内容。"""

    # 待办提取提示
    TODO_PROMPT = """从以下会议发言中提取待办事项（行动项）：

{text}

只输出待办事项列表，每条格式为："待办内容 @负责人"（如果负责人不明确则写"待定")
如果没有待办事项，输出"无"。"""

    def __init__(
        self,
        llm_config: LLMConfig,
        listener: MeetingListener,
        messenger: Optional[MeetingMessenger] = None,
        summary_interval: float = 30.0
    ):
        self.llm = LLMClient(llm_config)
        self.listener = listener
        self.messenger = messenger
        self.summary_interval = summary_interval

        # 状态
        self._running = False
        self._last_summary: Optional[SummaryResult] = None
        self._last_summary_time: float = 0
        self._processed_transcript_count: int = 0

    async def start(self):
        """启动总结引擎"""
        self._running = True
        logger.info("总结引擎已启动")

        # 启动总结循环
        await self._summary_loop()

    async def stop(self):
        """停止总结引擎"""
        self._running = False
        logger.info("总结引擎已停止")

        # 生成最终总结
        if self._last_summary:
            logger.info(f"最终总结:\n{self._last_summary.summary}")
            if self.messenger:
                self.messenger.report_summary(self._last_summary.summary)

    async def _summary_loop(self):
        """总结更新循环"""
        while self._running:
            # 等待更新间隔
            await asyncio.sleep(self.summary_interval)

            # 检查是否有新的转写内容
            transcripts = self.listener.get_transcripts()
            current_count = len(transcripts)

            if current_count > self._processed_transcript_count:
                # 有新内容，更新总结
                await self._update_summary()
                self._processed_transcript_count = current_count

    async def _update_summary(self):
        """更新总结"""
        # 获取转写文本
        transcript_text = self.listener.get_transcript_text()

        if not transcript_text:
            return

        logger.debug(f"生成总结，转写长度: {len(transcript_text)}")

        try:
            # 调用LLM生成总结
            prompt = self.SUMMARY_PROMPT_TEMPLATE.format(transcript=transcript_text)
            result_text = await self.llm.generate_async(prompt, self.SUMMARY_SYSTEM_PROMPT)

            # 解析结果
            summary = self._parse_summary_result(result_text)

            self._last_summary = summary
            self._last_summary_time = time.time()

            logger.info(f"总结已更新:\n{summary.summary}")

            # 发送到会议（如果配置了messenger）
            if self.messenger and summary.key_points:
                # 只发送关键要点（避免消息过长）
                points_text = "关键要点:\n" + "\n".join(f"- {p}" for p in summary.key_points[:3])
                self.messenger.send_text(points_text)

        except Exception as e:
            logger.error(f"总结生成失败: {e}")

    def _parse_summary_result(self, text: str) -> SummaryResult:
        """解析LLM返回的总结文本"""
        # 简单解析：按标题分割
        sections = {}
        current_section = "summary"
        current_content = []

        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("##"):
                # 新section
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line.replace("##", "").strip().lower()
                current_content = []
            else:
                current_content.append(line)

        # 最后一个section
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()

        # 构建SummaryResult
        return SummaryResult(
            summary=sections.get("会议总结", ""),
            key_points=self._parse_list_items(sections.get("关键要点", "")),
            current_topic=sections.get("当前话题", ""),
            decisions=self._parse_list_items(sections.get("决议", "")),
            todos=self._parse_list_items(sections.get("待办", "")),
            timestamp=time.time()
        )

    def _parse_list_items(self, text: str) -> List[str]:
        """解析列表项"""
        items = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                items.append(line.lstrip("-*").strip())
            elif line and not line.startswith("#"):
                items.append(line)
        return items

    async def get_current_topic(self) -> str:
        """快速获取当前话题"""
        # 获取最近的几条转写
        recent = self.listener.get_transcripts(limit=5)
        if not recent:
            return ""

        recent_text = "\n".join(
            f"{e.sender_name}: {e.content}" for e in recent if e.content
        )

        try:
            topic = await self.llm.generate_async(
                self.TOPIC_PROMPT.format(recent_text=recent_text)
            )
            return topic.strip()
        except Exception as e:
            logger.error(f"话题识别失败: {e}")
            return ""

    async def extract_todos(self) -> List[str]:
        """提取待办事项"""
        transcript_text = self.listener.get_transcript_text()

        if not transcript_text:
            return []

        try:
            result = await self.llm.generate_async(
                self.TODO_PROMPT.format(text=transcript_text)
            )

            if result.strip() == "无":
                return []

            # 解析待办列表
            todos = []
            for line in result.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    todos.append(line.lstrip("-*").strip())
                elif line:
                    todos.append(line)

            return todos

        except Exception as e:
            logger.error(f"待办提取失败: {e}")
            return []

    def get_last_summary(self) -> Optional[SummaryResult]:
        """获取最近的总结"""
        return self._last_summary

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running