"""插件管理器"""
import os
import importlib
import pkgutil
from typing import Dict, List, Any, Optional
import logging

from app.plugins.base import PluginBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        """初始化插件管理器"""
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_dirs: List[str] = []
    
    def add_plugin_directory(self, directory: str) -> bool:
        """添加插件目录
        
        Args:
            directory: 插件目录路径
            
        Returns:
            bool: 添加是否成功
        """
        if os.path.exists(directory) and os.path.isdir(directory):
            self.plugin_dirs.append(directory)
            return True
        return False
    
    def discover_plugins(self) -> List[str]:
        """发现插件
        
        Returns:
            List[str]: 发现的插件名称列表
        """
        discovered = []
        
        # 扫描插件目录
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue
            
            # 遍历目录中的文件
            for filename in os.listdir(plugin_dir):
                file_path = os.path.join(plugin_dir, filename)
                if os.path.isdir(file_path) and os.path.exists(os.path.join(file_path, "__init__.py")):
                    # 是一个Python包
                    plugin_name = filename
                    discovered.append(plugin_name)
                elif filename.endswith(".py") and filename != "__init__.py":
                    # 是一个Python文件
                    plugin_name = filename[:-3]
                    discovered.append(plugin_name)
        
        return discovered
    
    def load_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """加载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[PluginBase]: 加载的插件实例
        """
        try:
            # 尝试从插件目录加载
            for plugin_dir in self.plugin_dirs:
                plugin_path = os.path.join(plugin_dir, plugin_name)
                
                if os.path.isdir(plugin_path):
                    # 从包加载
                    module_name = f"plugins.{plugin_name}"
                    module = importlib.import_module(module_name)
                elif os.path.exists(os.path.join(plugin_dir, f"{plugin_name}.py")):
                    # 从文件加载
                    module_name = f"plugins.{plugin_name}"
                    module = importlib.import_module(module_name)
                else:
                    continue
                
                # 查找插件类
                for name, obj in module.__dict__.items():
                    if isinstance(obj, type) and issubclass(obj, PluginBase) and obj != PluginBase:
                        # 创建插件实例
                        plugin = obj()
                        self.plugins[plugin_name] = plugin
                        logger.info(f"成功加载插件: {plugin_name} - {plugin.name}")
                        return plugin
        except Exception as e:
            logger.error(f"加载插件 {plugin_name} 失败: {e}")
        
        return None
    
    def load_all_plugins(self) -> Dict[str, PluginBase]:
        """加载所有插件
        
        Returns:
            Dict[str, PluginBase]: 加载的插件字典
        """
        plugins = {}
        for plugin_name in self.discover_plugins():
            plugin = self.load_plugin(plugin_name)
            if plugin:
                plugins[plugin_name] = plugin
        return plugins
    
    def initialize_plugins(self, context: Dict[str, Any]) -> Dict[str, bool]:
        """初始化所有插件
        
        Args:
            context: 插件上下文
            
        Returns:
            Dict[str, bool]: 插件初始化结果
        """
        results = {}
        for plugin_name, plugin in self.plugins.items():
            try:
                success = plugin.initialize(context)
                results[plugin_name] = success
                if success:
                    logger.info(f"成功初始化插件: {plugin_name}")
                else:
                    logger.warning(f"插件 {plugin_name} 初始化失败")
            except Exception as e:
                logger.error(f"插件 {plugin_name} 初始化异常: {e}")
                results[plugin_name] = False
        return results
    
    def shutdown_plugins(self) -> Dict[str, bool]:
        """关闭所有插件
        
        Returns:
            Dict[str, bool]: 插件关闭结果
        """
        results = {}
        for plugin_name, plugin in self.plugins.items():
            try:
                success = plugin.shutdown()
                results[plugin_name] = success
                if success:
                    logger.info(f"成功关闭插件: {plugin_name}")
                else:
                    logger.warning(f"插件 {plugin_name} 关闭失败")
            except Exception as e:
                logger.error(f"插件 {plugin_name} 关闭异常: {e}")
                results[plugin_name] = False
        return results
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """获取插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[PluginBase]: 插件实例
        """
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, PluginBase]:
        """获取所有插件
        
        Returns:
            Dict[str, PluginBase]: 插件字典
        """
        return self.plugins
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 启用是否成功
        """
        plugin = self.plugins.get(plugin_name)
        if plugin:
            return plugin.enable()
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 禁用是否成功
        """
        plugin = self.plugins.get(plugin_name)
        if plugin:
            return plugin.disable()
        return False
    
    def get_plugin_metadata(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件元数据
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[Dict[str, Any]]: 插件元数据
        """
        plugin = self.plugins.get(plugin_name)
        if plugin:
            return plugin.get_metadata()
        return None
    
    def get_all_plugin_metadata(self) -> Dict[str, Dict[str, Any]]:
        """获取所有插件元数据
        
        Returns:
            Dict[str, Dict[str, Any]]: 插件元数据字典
        """
        metadata = {}
        for plugin_name, plugin in self.plugins.items():
            metadata[plugin_name] = plugin.get_metadata()
        return metadata
    
    def dispatch_event(self, event_name: str, **kwargs) -> Dict[str, Any]:
        """分发事件
        
        Args:
            event_name: 事件名称
            **kwargs: 事件参数
            
        Returns:
            Dict[str, Any]: 事件处理结果
        """
        results = {}
        for plugin_name, plugin in self.plugins.items():
            if plugin.is_enabled():
                try:
                    result = plugin.on_event(event_name, **kwargs)
                    results[plugin_name] = result
                except Exception as e:
                    logger.error(f"插件 {plugin_name} 处理事件 {event_name} 异常: {e}")
                    results[plugin_name] = None
        return results
