from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """应用配置设置"""
    # 项目基本配置
    PROJECT_NAME: str = "VM-TOOL"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./vm_tool.db"
    
    # 应用配置
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 码表相关路径
    MAIN_DICT: str = os.path.join(BASE_DIR, "dicts/main.txt")
    OUTPUT_FILE: str = os.path.join(BASE_DIR, "output.txt")
    SINGLE_WORD_FILE: str = os.path.join(BASE_DIR, "singleWord/小鹤字库.txt")
    TO_FILTER_DIR: str = os.path.join(BASE_DIR, "toFilter")
    ADD_WORDS_DIR: str = os.path.join(BASE_DIR, "addWords")
    TARGET_RIME_PATH: str = os.path.join(os.path.expanduser("~"), ".config", "ibus", "rime")
    
    # 功能配置
    ENCODINGS: List[str] = ["utf-8", "utf-16", "gbk"]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
