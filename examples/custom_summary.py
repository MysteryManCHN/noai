"""自定义总结 Prompt 示例 - 继承 SummaryEngine 调整总结风格

通过子类化 SummaryEngine 并覆盖 SUMMARY_SYSTEM_PROMPT，
可以在不改动核心代码的前提下自定义 LLM 的总结输出格式与风格。
然后在 agent.join() 之后、agent.start() 之前手动替换 summary_engine。
"""
import asyncio
from meeting_agent import Config, MeetingAgent
from meeting_agent.summary import SummaryEngine


# 1. 继承 SummaryEngine，覆盖总结 Prompt
class TechReviewSummaryEngine(SummaryEngine):
    """技术评审专用总结引擎。

    输出格式固定为：讨论要点 / 关键决策 / 待办事项，
    并要求语言简洁专业。
    """

    SUMMARY_SYSTEM_PROMPT = """你是一名资深技术评审会议纪要助手。
请基于会议转写文本，按以下格式输出中文总结：

## 讨论要点
- （不超过 3 条，每条一句话）

## 关键决策
- （列出会议上明确达成共识的决策；若无则写"无"）

## 待办事项
- （含负责人与截止时间，若无则写"无"）

要求：语言简洁、专业；只基于转写内容，不臆造信息。"""


async def main():
    config = Config.from_env()
    agent = MeetingAgent(config)

    # 加入会议（此时 listener 和 messenger 已初始化）
    if not agent.join("123456789"):
        print("入会失败")
        return

    # 手动创建自定义总结引擎，替换默认引擎
    if config.llm.api_key and agent.listener and agent.messenger:
        agent.summary_engine = TechReviewSummaryEngine(
            llm_config=config.llm,
            listener=agent.listener,
            messenger=agent.messenger,
            summary_interval=config.meeting.summary_interval
        )

    # 启动监听和总结
    try:
        await agent.start()
    except KeyboardInterrupt:
        pass
    finally:
        await agent.stop()
        agent.leave()


if __name__ == "__main__":
    asyncio.run(main())