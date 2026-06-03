from typing import Dict, Any, Optional
import traceback
import logging

logger = logging.getLogger(__name__)


class VMToolError(Exception):
    """VM-TOOL基础异常类"""
    
    def __init__(self, message: str, code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(VMToolError):
    """配置错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=400, details=details)


class DatabaseError(VMToolError):
    """数据库错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=500, details=details)


class DictError(VMToolError):
    """码表操作错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=400, details=details)


class WeightError(VMToolError):
    """权重计算错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=400, details=details)


class FileError(VMToolError):
    """文件操作错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=400, details=details)


def handle_error(error: Exception) -> Dict[str, Any]:
    """处理错误并返回错误信息"""
    if isinstance(error, VMToolError):
        return {
            "error": error.__class__.__name__,
            "message": error.message,
            "code": error.code,
            "details": error.details
        }
    else:
        # 处理未预期的错误
        return {
            "error": "UnexpectedError",
            "message": str(error),
            "code": 500,
            "details": {
                "traceback": traceback.format_exc()
            }
        }


def safe_execute(func):
    """安全执行装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_info = handle_error(e)
            logger.error(f"错误: {error_info['message']}")
            if error_info.get('details', {}).get('traceback'):
                logger.debug(f"详细信息: {error_info['details']['traceback']}")
            return None
    return wrapper
