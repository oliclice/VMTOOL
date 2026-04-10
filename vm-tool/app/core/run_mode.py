from enum import Enum
from typing import Optional, Dict, Any


class RunMode(Enum):
    """运行模式枚举"""
    CLI = "cli"
    WEB = "web"
    GUI = "gui"
    API = "api"


class RunModeManager:
    """运行模式管理器"""
    
    def __init__(self):
        self._current_mode: Optional[RunMode] = None
        self._mode_configs: Dict[RunMode, Dict[str, Any]] = {
            RunMode.CLI: {
                "name": "命令行模式",
                "description": "通过命令行交互操作码表工具",
                "enabled": True
            },
            RunMode.WEB: {
                "name": "Web模式",
                "description": "通过Web界面操作码表工具",
                "enabled": True
            },
            RunMode.GUI: {
                "name": "GUI模式",
                "description": "通过图形界面操作码表工具",
                "enabled": True
            },
            RunMode.API: {
                "name": "API模式",
                "description": "通过API接口操作码表工具",
                "enabled": True
            }
        }
    
    def set_mode(self, mode: RunMode) -> None:
        """设置当前运行模式"""
        if mode not in self._mode_configs:
            raise ValueError(f"不支持的运行模式: {mode}")
        
        if not self._mode_configs[mode]["enabled"]:
            raise ValueError(f"运行模式 {mode.value} 已被禁用")
        
        self._current_mode = mode
    
    def get_mode(self) -> Optional[RunMode]:
        """获取当前运行模式"""
        return self._current_mode
    
    def get_mode_config(self, mode: RunMode) -> Dict[str, Any]:
        """获取指定模式的配置"""
        if mode not in self._mode_configs:
            raise ValueError(f"不支持的运行模式: {mode}")
        return self._mode_configs[mode]
    
    def is_mode_enabled(self, mode: RunMode) -> bool:
        """检查模式是否启用"""
        return self._mode_configs.get(mode, {}).get("enabled", False)
    
    def disable_mode(self, mode: RunMode) -> None:
        """禁用指定模式"""
        if mode in self._mode_configs:
            self._mode_configs[mode]["enabled"] = False
    
    def enable_mode(self, mode: RunMode) -> None:
        """启用指定模式"""
        if mode in self._mode_configs:
            self._mode_configs[mode]["enabled"] = True


# 创建全局运行模式管理器实例
run_mode_manager = RunModeManager()
