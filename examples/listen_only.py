"""只监听不总结示例 - 不配置 LLM 时仅监听会议事件

适用场景：只需要实时获取会议转写文本与事件流，
不需要 LLM 生成总结（例如自己接其他下游处理）。

要点：
1. 不设置 LLM_API_KEY 等环境变量，Config.llm.api_key 为空。
2. MeetingAgent 检测到未配置 LLM 时不会启动 SummaryEngine。
3. 在 agent.join() 之后通过 agent.listener 设置回调。
"""
import asyncio
from meeting_agent import Config, MeetingAgent


async def main():
    # 不设置 LLM 相关环境变量，仅依赖 lark-cli 认证
    config = Config.from_env()

    # 强制清空 API Key，确保不启动总结引擎
    config.llm.api_key = None

    agent = MeetingAgent(config)

    # 先加入会议（join 之后 listener 才被初始化）
    if not agent.join("123456789"):
        print("入会失败")
        return

    # 注册自定义转写回调
    async def on_transcript(event):
        # Event 对象字段: event_type, timestamp, sender_id, sender_name, content
        speaker = event.sender_name or "未知"
        text = event.content or ""
        print(f"[{speaker}] {text}")

    agent.listener.set_callbacks(on_transcript=on_transcript)

    try:
        # 启动监听；因未配置 LLM，不会触发总结
        await agent.start()
    except KeyboardInterrupt:
        pass
    finally:
        await agent.stop()
        agent.leave()


if __name__ == "__main__":
    asyncio.run(main())