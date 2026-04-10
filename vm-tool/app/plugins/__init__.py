"""插件系统"""
from app.plugins.manager import PluginManager
from app.plugins.base import PluginBase

__all__ = [
    "PluginManager",
    "PluginBase"
]
