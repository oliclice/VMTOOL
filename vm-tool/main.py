#!/usr/bin/env python3
"""
VM-TOOL - 码表处理工具主程序
支持命令行参数和交互式菜单
"""
import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.run_mode import run_mode_manager, RunMode
from app.core.service_registry import service_registry
from app.core.logging_config import setup_logging
from app.dal.init_db import init_database

# 初始化日志配置
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        logger.info(f"启动 {settings.PROJECT_NAME} v{settings.VERSION}")
        
        # 初始化数据库
        init_database()
        
        # 注册核心服务
        register_services()
        
        # 解析命令行参数
        if len(sys.argv) > 1:
            # 命令行模式
            run_mode_manager.set_mode(RunMode.CLI)
            handle_cli_args()
        else:
            # 交互式模式
            run_mode_manager.set_mode(RunMode.CLI)
            show_menu()
            
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        sys.exit(1)


def register_services():
    """注册服务"""
    logger.info("注册核心服务...")
    # 这里将在后续实现中注册各种服务
    pass


def handle_cli_args():
    """处理命令行参数"""
    logger.info(f"命令行参数: {sys.argv[1:]}")
    # 这里将在后续实现中处理命令行参数
    logger.info(f"命令行模式: {sys.argv[1:]}")


def show_menu():
    """显示菜单"""
    logger.info("显示交互式菜单")
    # 这里将在后续实现中显示交互式菜单
    logger.info("交互式菜单模式")


if __name__ == '__main__':
    main()
