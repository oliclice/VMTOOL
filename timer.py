#!/usr/bin/env python3
"""计时器模块"""
import time
from typing import Callable, List, Tuple, Any
class Timer:
    def time_execution(name: str, *funcs: Callable[[], Any]) -> Tuple[List[Any], float]:
        """分别执行每个函数并返回结果列表和总耗时"""
        results = []
        start = time.perf_counter()
        for func in funcs:
            try:
                results.append(func())
            except Exception as e:
                # 可记录异常，但这里简单重新抛出
                raise RuntimeError(f"函数 {func.__name__} 执行失败") from e
        elapsed = time.perf_counter() - start
        print(f"{name}耗时: {elapsed:.5f}秒")
        return results, elapsed
