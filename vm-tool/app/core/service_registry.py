from typing import Dict, Type, Any, Optional


class ServiceRegistry:
    """服务注册中心"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._service_classes: Dict[str, Type] = {}
    
    def register_service(self, name: str, service: Any) -> None:
        """注册服务实例"""
        self._services[name] = service
    
    def register_service_class(self, name: str, service_class: Type) -> None:
        """注册服务类"""
        self._service_classes[name] = service_class
    
    def get_service(self, name: str) -> Optional[Any]:
        """获取服务实例"""
        return self._services.get(name)
    
    def get_service_class(self, name: str) -> Optional[Type]:
        """获取服务类"""
        return self._service_classes.get(name)
    
    def has_service(self, name: str) -> bool:
        """检查服务是否存在"""
        return name in self._services
    
    def has_service_class(self, name: str) -> bool:
        """检查服务类是否存在"""
        return name in self._service_classes
    
    def unregister_service(self, name: str) -> None:
        """注销服务"""
        if name in self._services:
            del self._services[name]
    
    def unregister_service_class(self, name: str) -> None:
        """注销服务类"""
        if name in self._service_classes:
            del self._service_classes[name]
    
    def list_services(self) -> list:
        """列出所有注册的服务"""
        return list(self._services.keys())
    
    def list_service_classes(self) -> list:
        """列出所有注册的服务类"""
        return list(self._service_classes.keys())


# 创建全局服务注册中心实例
service_registry = ServiceRegistry()
