"""缓存和性能优化"""
import time
import functools
from typing import Dict, Any, Optional, Callable
import gc
import psutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Cache:
    """简单的内存缓存实现"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """初始化缓存
        
        Args:
            max_size: 缓存最大容量
            ttl: 缓存过期时间（秒）
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def _get_key(self, func: Callable, *args, **kwargs) -> str:
        """生成缓存键"""
        key = f"{func.__module__}.{func.__name__}:{args}:{sorted(kwargs.items())}"
        return key
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self.cache:
            item = self.cache[key]
            # 检查是否过期
            if time.time() - item["timestamp"] < self.ttl:
                return item["value"]
            else:
                # 删除过期缓存
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        # 如果缓存已满，删除最旧的项
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
        
        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)
    
    def decorator(self):
        """缓存装饰器"""
        def wrapper(func):
            @functools.wraps(func)
            def inner(*args, **kwargs):
                key = self._get_key(func, *args, **kwargs)
                # 尝试从缓存获取
                cached_value = self.get(key)
                if cached_value is not None:
                    return cached_value
                # 执行函数
                result = func(*args, **kwargs)
                # 缓存结果
                self.set(key, result)
                return result
            return inner
        return wrapper


# 创建全局缓存实例
cache = Cache()


def monitor_memory_usage() -> Dict[str, Any]:
    """监控内存使用情况"""
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        "rss": memory_info.rss / 1024 / 1024,  # 常驻集大小（MB）
        "vms": memory_info.vms / 1024 / 1024,  # 虚拟内存大小（MB）
        "percent": process.memory_percent(),  # 内存使用百分比
        "gc_collections": gc.get_count(),  # GC收集次数
        "cache_size": cache.size()  # 缓存大小
    }


def optimize_batch_operation(batch_size: int = 1000):
    """批量操作优化装饰器"""
    def wrapper(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            # 检查是否是实例方法
            if len(args) > 0 and hasattr(args[0], '__class__'):
                # 实例方法，第一个参数是 self
                self = args[0]
                items = args[1]
                other_args = args[2:]
            else:
                # 普通函数，第一个参数是 items
                items = args[0]
                other_args = args[1:]
            
            if not items:
                # 检查函数名，返回适当的空值
                if func.__name__ == 'add_words':
                    return {"added": 0, "existing": 0, "existing_pairs": []}
                return []
            
            # 特殊处理 add_words 方法
            if func.__name__ == 'add_words':
                if len(args) > 0 and hasattr(args[0], '__class__'):
                    # 实例方法调用
                    return func(self, items, *other_args, **kwargs)
                else:
                    # 普通函数调用
                    return func(items, *other_args, **kwargs)
            
            # 其他批量操作
            results = []
            # 分批处理
            for i in range(0, len(items), batch_size):
                batch = items[i:i+batch_size]
                if len(args) > 0 and hasattr(args[0], '__class__'):
                    # 实例方法调用
                    batch_result = func(self, batch, *other_args, **kwargs)
                else:
                    # 普通函数调用
                    batch_result = func(batch, *other_args, **kwargs)
                results.extend(batch_result)
                
                # 每处理一批后进行一次GC
                if i % (batch_size * 5) == 0:
                    gc.collect()
            
            return results
        return inner
    return wrapper


def performance_monitor(func):
    """性能监控装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = monitor_memory_usage()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = monitor_memory_usage()
        
        execution_time = end_time - start_time
        memory_increase = end_memory["rss"] - start_memory["rss"]
        
        logger.info(f"函数 {func.__name__} 执行时间: {execution_time:.4f} 秒")
        logger.info(f"内存变化: {memory_increase:.2f} MB")
        
        return result
    return wrapper
