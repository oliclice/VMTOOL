"""示例插件"""
from app.plugins.base import PluginBase
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ExamplePlugin(PluginBase):
    """示例插件"""
    
    name = "示例插件"
    description = "这是一个示例插件"
    version = "1.0.0"
    author = "Claude"
    
    def initialize(self, context: Dict[str, Any]) -> bool:
        """初始化插件"""
        logger.info(f"初始化示例插件，上下文: {list(context.keys())}")
        self.context = context
        return True
    
    def shutdown(self) -> bool:
        """关闭插件"""
        logger.info("关闭示例插件")
        return True
    
    def on_event(self, event_name: str, **kwargs) -> Any:
        """处理事件"""
        logger.info(f"示例插件处理事件: {event_name}, 参数: {kwargs}")
        if event_name == "word_added":
            word = kwargs.get("word")
            if word:
                logger.info(f"新添加的词: {word}")
        return f"示例插件处理了事件: {event_name}"
    
    def get_commands(self) -> Dict[str, Any]:
        """获取插件提供的命令"""
        return {
            "example_command": {
                "description": "示例命令",
                "callback": self.example_command
            }
        }
    
    def example_command(self, **kwargs) -> str:
        """示例命令回调"""
        return "示例命令执行成功"
