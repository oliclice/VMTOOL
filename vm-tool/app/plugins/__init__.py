"""插件系统"""
from app.plugins.base import PluginBase
from app.plugins.manager import PluginManager

__all__ = ["PluginManager", "PluginBase"]
