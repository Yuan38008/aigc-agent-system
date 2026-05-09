# config.py - 系统配置
import os

class Config:
    # ========== LLM配置 ==========
    # 支持OpenAI兼容接口（可接入本地Ollama）
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
    
    # 云端模型配置（申请到Token后填入）
    CLOUD_API_KEY = os.getenv("CLOUD_API_KEY", "")
    CLOUD_BASE_URL = os.getenv("CLOUD_BASE_URL", "")
    CLOUD_MODEL = os.getenv("CLOUD_MODEL", "claude-3-5-sonnet-20241022")
    
    # ========== AIGC视频生成配置 ==========
    # 即梦API（字节）
    JIMENG_API_KEY = os.getenv("JIMENG_API_KEY", "")
    # 可灵API（快手）
    KLING_API_KEY = os.getenv("KLING_API_KEY", "")
    
    # ========== 系统配置 ==========
    MAX_TOPICS_PER_RUN = 5
    MAX_RETRY = 3
    OUTPUT_DIR = "./output"
    LOG_LEVEL = "INFO"
    
    # ========== 平台配置 ==========
    TARGET_PLATFORM = "douyin"  # douyin/xiaohongshu/bilibili
    ACCOUNT_STYLE = "生活教程类"
    
config = Config()
