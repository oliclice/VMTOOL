"""配置管理模块"""
import json
import os
import logging
from typing import Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)
from app.core.theme_constants import (
    DEFAULT_THEME_MODE, DEFAULT_THEME_NAME, DEFAULT_THEME_COLOR,
    THEME_MODE_DARK, THEME_MODE_LIGHT, THEME_MODE_AUTO,
    THEME_NAME_CLASSIC, THEME_COLOR_BLUE
)


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
            "theme": THEME_MODE_AUTO,  # 向后兼容旧版本
            "theme_mode": DEFAULT_THEME_MODE,
            "theme_name": DEFAULT_THEME_NAME,
            "theme_color": DEFAULT_THEME_COLOR,
            "window_size": [1000, 700],
            "window_position": [100, 100],
            "config_dir": self.config_dir,
            "database_path": os.path.join(self.config_dir, "vm_tool.db")
        }
        self.config = self.load_config()

    def _migrate_theme_config(self, config: Dict[str, Any]) -> None:
        """迁移旧版主题配置到新版"""
        if "theme" in config and "theme_mode" not in config:
            old_theme = config["theme"]
            if old_theme == THEME_MODE_DARK:
                config["theme_mode"] = THEME_MODE_DARK
            elif old_theme == THEME_MODE_LIGHT:
                config["theme_mode"] = THEME_MODE_LIGHT
            else:
                config["theme_mode"] = THEME_MODE_AUTO

            # 设置默认主题名称和颜色
            if "theme_name" not in config:
                config["theme_name"] = DEFAULT_THEME_NAME
            if "theme_color" not in config:
                config["theme_color"] = DEFAULT_THEME_COLOR

            # 可以保留旧键以保持兼容性，也可以删除
            # del config["theme"]

    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # 迁移旧版主题配置
                self._migrate_theme_config(config)

                # 合并默认配置
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                return self.default_config
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return self.default_config
    
    def save_config(self) -> bool:
        """保存配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
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