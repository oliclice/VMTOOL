#!/usr/bin/env python3
"""临时数据库初始化脚本"""
import sys
import os

# 添加vm-tool目录到Python路径
sys.path.insert(0, os.path.abspath('vm-tool'))

from app.dal.init_db import init_database

if __name__ == "__main__":
    init_database()
