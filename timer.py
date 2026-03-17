#!/usr/bin/env python3
"""计时器模块"""
import time
from typing import Callable


class Timer:
    """计时器"""
    
    @staticmethod
    def time_execution(name: str, *funcs: Callable):
        """计时执行函数"""
        start = time.time()
        for func in funcs:
            func()
        elapsed = time.time() - start
        print(f"{name}耗时: {elapsed:.3f}秒")
