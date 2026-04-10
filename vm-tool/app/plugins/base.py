"""插件基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class PluginBase(ABC):
    """插件基类"""
    
    # 插件元数据
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    
    def __init__(self):
        """初始化插件"""
        self.enabled = False
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool:
        """初始化插件
        
        Args:
            context: 插件上下文，包含应用的核心服务
            
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """关闭插件
        
        Returns:
            bool: 关闭是否成功
        """
        pass
    
    def enable(self) -> bool:
        """启用插件"""
        self.enabled = True
        return True
    
    def disable(self) -> bool:
        """禁用插件"""
        self.enabled = False
        return True
    
    def is_enabled(self) -> bool:
        """检查插件是否启用"""
        return self.enabled
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取插件元数据"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "enabled": self.enabled
        }
    
    def on_event(self, event_name: str, **kwargs) -> Any:
        """处理事件
        
        Args:
            event_name: 事件名称
            **kwargs: 事件参数
            
        Returns:
            Any: 事件处理结果
        """
        pass
    
    def get_commands(self) -> Dict[str, Any]:
        """获取插件提供的命令
        
        Returns:
            Dict[str, Any]: 命令字典
        """
        return {}
    
    def get_api_endpoints(self) -> Dict[str, Any]:
        """获取插件提供的API端点
        
        Returns:
            Dict[str, Any]: API端点字典
        """
        return {}
