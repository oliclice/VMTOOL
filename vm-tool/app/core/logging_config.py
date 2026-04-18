"""统一日志配置模块"""
import logging


def setup_logging(level: str = "INFO") -> None:
    """统一日志配置
    
    Args:
        level: 日志级别，默认为 INFO
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('vmtool.log')
        ]
    )
