"""
飞书会议Agent - 简易启动脚本
"""
import asyncio
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meeting_agent.config import Config
from meeting_agent.main import MeetingAgent, setup_logging


def quick_start(meeting_number: str, llm_provider: str = "openai"):
    """
    快速启动Agent

    Args:
        meeting_number: 9位会议号
        llm_provider: LLM提供商 (openai/anthropic/deepseek)
    """
    # 配置日志
    setup_logging("INFO")

    # 加载配置
    config = Config.from_env()
    config.llm.provider = llm_provider

    # 检查API Key
    if not config.llm.api_key:
        print(f"警告: 未配置 {llm_provider} API Key")
        print(f"请设置环境变量: {llm_provider.upper()}_API_KEY")
        print("Agent将只监听会议，不生成总结")

    # 创建Agent
    agent = MeetingAgent(config)

    # 加入会议
    print(f"正在加入会议: {meeting_number}")
    if not agent.join(meeting_number):
        print("入会失败，请检查会议号和权限")
        return

    print("已成功入会，开始监听会议...")
    print("按 Ctrl+C 退出")

    # 异步运行
    async def run():
        try:
            await agent.start()
        except KeyboardInterrupt:
            await agent.stop()
            agent.leave()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n正在退出会议...")
        asyncio.run(agent.stop())
        agent.leave()
        print("已离开会议")


if __name__ == "__main__":
    # 示例：直接运行
    # python agent.py 123456789

    if len(sys.argv) < 2:
        print("用法: python agent.py <9位会议号> [llm_provider]")
        print("示例: python agent.py 123456789 openai")
        sys.exit(1)

    meeting_number = sys.argv[1]
    provider = sys.argv[2] if len(sys.argv) > 2 else "openai"

    quick_start(meeting_number, provider)