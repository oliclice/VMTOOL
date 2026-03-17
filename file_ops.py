#!/usr/bin/env python3
"""文件操作模块"""
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any


class FileReader:
    """文件读取器"""
    
    def __init__(self, encodings: List[str]):
        self.encodings = encodings
    
    def read_lines(self, file_path: str) -> List[List[str]]:
        """读取文件，支持多种编码"""
        for encoding in self.encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return [line.strip().split() for line in f if line.strip()]
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError(f"无法使用{self.encodings}读取文件")
    
    def to_dict(self, file_path: str) -> Dict[str, Dict[str, Any]]:
        """将文件内容转换为字典"""
        result = {}
        for line in self.read_lines(file_path):
            if line and line[0] != '#':
                result[line[0]] = {
                    "key": "?" if len(line) <= 1 else line[1],
                    "weight": 1 if len(line) <= 2 else int(line[2]),
                    "exsit": True
                }
        return result
    
    @staticmethod
    def scan_files(folder: str) -> List[str]:
        """扫描文件夹中的所有文件"""
        return [os.path.join(folder, f) for f in os.listdir(folder) 
                if os.path.isfile(os.path.join(folder, f))]


class FileWriter:
    """文件写入器"""
    
    @staticmethod
    def backup(file_path: str):
        """创建备份"""
        if os.path.isfile(file_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(file_path, f"{file_path}.{timestamp}.bak")
    
    @staticmethod
    def write_dict(data: Dict[str, Dict[str, Any]], output_path: str, startwith_path: str = None):
        """写入字典到文件"""
        FileWriter.backup(output_path)
        
        # 读取开头内容
        startwith_lines = []
        if startwith_path and os.path.exists(startwith_path):
            with open(startwith_path, 'r', encoding='utf-8') as f:
                startwith_lines = [line.rstrip() for line in f]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in startwith_lines:
                f.write(f"{line}\n")
            
            for word, info in sorted(data.items(), key=lambda x: x[1]['key']):
                if info['exsit']:
                    f.write(f"{word}\t{info['key']}\t{info['weight']}\n")
    
    @staticmethod
    def append_dict(data: Dict[str, Dict[str, Any]], output_path: str):
        """追加模式写入"""
        FileWriter.backup(output_path)
        
        with open(output_path, 'a', encoding='utf-8') as f:
            for word, info in sorted(data.items(), key=lambda x: x[1]['key']):
                if info['exsit']:
                    f.write(f"{word}\t{info['key']}\t{info['weight']}\n")
    
    @staticmethod
    def write_simple(data: Dict[str, str], output_path: str):
        """写入简单字典（字表）"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for word, key in sorted(data.items(), key=lambda x: x[1]):
                f.write(f"{word}\t{key}\n")
    
    @staticmethod
    def clear_files(file_paths: List[str]):
        """清空多个文件"""
        for path in file_paths:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("")
    
    @staticmethod
    def copy_file(source: str, target_dir: str, new_name: str):
        """复制文件到目标目录"""
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy2(source, os.path.join(target_dir, new_name))
