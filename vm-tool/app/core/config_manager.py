"""配置管理模块"""
import json
import os
from typing import Dict, Any

from app.core.config import settings


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        # 配置文件保存在 ~/.config/vm-tool/ 目录下
        try:
            self.config_dir = os.path.expanduser("~/.config/vm-tool")
            os.makedirs(self.config_dir, exist_ok=True)
        except OSError:
            # 如果无法创建目录，使用当前目录作为默认目录
            self.config_dir = os.getcwd()
        
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.default_config = {
            "theme": "auto",
            "window_size": [1000, 700],
            "window_position": [100, 100],
            "config_dir": self.config_dir,
            "database_path": os.path.join(self.config_dir, "vm_tool.db")
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                # 合并默认配置
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                return self.default_config
        except Exception as e:
            print(f"加载配置失败: {e}")
            return self.default_config
    
    def save_config(self) -> bool:
        """保存配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置值"""
        self.config[key] = value
        return self.save_config()


# 创建全局配置管理器实例
config_manager = ConfigManager()