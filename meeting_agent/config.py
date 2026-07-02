"""配置管理"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMConfig:
    """LLM配置（用于实时总结）"""
    provider: str = "openai"  # openai / anthropic / deepseek
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # 自定义API端点
    model: str = "gpt-4o-mini"  # 默认模型
    temperature: float = 0.3
    max_tokens: int = 2000

    def __post_init__(self):
        # 从环境变量读取API Key
        if not self.api_key:
            if self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif self.provider == "anthropic":
                self.api_key = os.getenv("ANTHROPIC_API_KEY")
            elif self.provider == "deepseek":
                self.api_key = os.getenv("DEEPSEEK_API_KEY")
                self.base_url = "https://api.deepseek.com/v1"


@dataclass
class MeetingConfig:
    """会议监听配置"""
    poll_interval: float = 10.0  # 事件轮询间隔（秒）
    summary_interval: float = 30.0  # 总结更新间隔（秒）
    transcript_buffer_size: int = 50  # 转写缓冲区大小（条数）
    enable_auto_response: bool = False  # 是否启用自动回应
    enable_topic_tracking: bool = True  # 是否启用话题追踪
    enable_todo_extraction: bool = True  # 是否提取待办


@dataclass
class Config:
    """全局配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    meeting: MeetingConfig = field(default_factory=MeetingConfig)
    lark_cli_path: str = ""  # 空则自动检测：优先LARK_CLI_PATH环境变量，再尝试常见路径
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置"""
        config = cls()

        # 自动检测 lark-cli 路径
        if not config.lark_cli_path:
            config.lark_cli_path = _detect_lark_cli()

        # LLM配置
        provider = os.getenv("LLM_PROVIDER", "openai")
        config.llm.provider = provider
        config.llm.model = os.getenv("LLM_MODEL", config.llm.model)
        config.llm.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))

        # Meeting配置
        config.meeting.poll_interval = float(os.getenv("POLL_INTERVAL", "10"))
        config.meeting.summary_interval = float(os.getenv("SUMMARY_INTERVAL", "30"))
        config.meeting.enable_auto_response = os.getenv("AUTO_RESPONSE", "false").lower() == "true"

        # 日志级别
        config.log_level = os.getenv("LOG_LEVEL", "INFO")

        return config


def _detect_lark_cli() -> str:
    """自动检测 lark-cli 路径"""
    import shutil
    import sys

    # 1. 环境变量
    env_path = os.getenv("LARK_CLI_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    # 2. PATH 中查找
    found = shutil.which("lark-cli")
    if found:
        return found

    # 3. 常见安装路径
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".trae-cn", "binaries", "node", "versions", "v24.14.0", "lark-cli"),
        os.path.join(home, ".qoderwork", "bin", "lark-cli.cmd"),
        "/usr/local/bin/lark-cli",
        "/usr/bin/lark-cli",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path

    # 默认返回命令名，让 subprocess 自行查找
    return "lark-cli"