"""基础使用示例 - 加入会议并自动总结"""
import asyncio
from meeting_agent import Config, MeetingAgent

async def main():
    config = Config.from_env()
    agent = MeetingAgent(config)
    
    # 加入会议
    if not agent.join("123456789"):
        print("入会失败")
        return
    
    # 启动监听和总结
    await agent.start()

asyncio.run(main())
