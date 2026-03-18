#!/usr/bin/env python3
"""配置管理"""
import os
from dataclasses import dataclass
from typing import List


@dataclass
class FunctionConfig:
    """功能配置"""
    id: int
    name: str
    desc: str


class Config:
    """配置管理"""
    
    FUNCTIONS: List[FunctionConfig] = [
        FunctionConfig(0, "退出程序", "退出应用程序"),
        FunctionConfig(1, "过滤码表", "过滤toFilter文件夹中的词条"),
        FunctionConfig(2, "计算权重", "计算码表权重"),
        FunctionConfig(3, "码表补充", "补充addWords文件夹中的新词"),
        FunctionConfig(4, "写入码表", "生成输出文件并复制到目标位置"),
        FunctionConfig(5, "字表去重", "刷新字表"),
        FunctionConfig(6, "查字补码", "自动补码"),
        FunctionConfig(7, "高频统计", "统计高频词"),
    ]
    
    ENCODINGS = ['utf-8', 'utf-16', 'gbk']
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or self._get_project_root()
        self.main_dict = os.path.join(self.base_dir, 'dicts/main.txt')
        self.output_file = os.path.join(self.base_dir, 'output.txt')
        self.single_word_file = os.path.join(self.base_dir, 'singleWord/小鹤字库.txt')
        self.to_filter_dir = os.path.join(self.base_dir, 'toFilter')
        self.add_words_dir = os.path.join(self.base_dir, 'addWords')
        self.target_rime_path = '~/.config/ibus/rime/'
        
        self._ensure_directories()
    
    def _get_project_root(self) -> str:
        """获取项目根目录"""
        return os.path.dirname(os.path.abspath(__file__))
    
    def _ensure_directories(self):
        """确保必要目录存在"""
        for path in [self.to_filter_dir, self.add_words_dir]:
            os.makedirs(path, exist_ok=True)
