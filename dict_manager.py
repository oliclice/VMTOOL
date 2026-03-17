#!/usr/bin/env python3
"""字典管理模块"""
import os
import re
from typing import Dict, List, Any, Tuple
from config import Config
from file_ops import FileReader, FileWriter


class DictManager:
    """字典管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.reader = FileReader(config.ENCODINGS)
        self.writer = FileWriter()
        self.data = {}
        self.words_dict = {}
        self.bak_counter = 0
        self._load_data()
        self._count_backups()
    
    def _load_data(self):
        """加载数据"""
        self.data = self.reader.to_dict(self.config.main_dict)
        self.words_dict = self.reader.to_dict(self.config.single_word_file)
        print(f"码表总计: {len(self.data)}条")
    
    def _count_backups(self):
        """统计备份文件数量"""
        for f in os.listdir(self.config.base_dir):
            if 'output.txt' in f and '.bak' in f:
                self.bak_counter += 1
    
    def filter(self) -> int:
        """过滤码表"""
        filter_files = self.reader.scan_files(self.config.to_filter_dir)
        total = 0
        
        for file_path in filter_files:
            filter_dict = self.reader.to_dict(file_path)
            total += len(filter_dict)
            
            for word, info in filter_dict.items():
                if word in self.data and (info['key'] == '?' or info['key'] == self.data[word]['key']):
                    self.data.pop(word, None)
        
        self.writer.clear_files(filter_files)
        print(f"总计过滤: {total}条")
        return total
    
    def add_words(self, words_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """添加新词"""
        if not words_data:
            return {}
        
        new_data = {}
        original_count = len(self.data)
        
        for word, info in words_data.items():
            if word in self.data:
                print(f'{word} 已存在: {self.data[word]}')
                continue
            
            new_key = self._generate_key(word)
            new_data[word] = {"key": new_key, "weight": 1, "exsit": True}
            
            if new_key == '?':
                print(f'错误: 无法为"{word}"生成编码')
            else:
                print(f'{word}: {new_data[word]}')
        
        self.data.update(new_data)
        print(f"新增词数: {len(self.data) - original_count}")
        return new_data
    
    def scan_and_add(self) -> Dict[str, Dict[str, Any]]:
        """扫描并添加新词"""
        add_files = self.reader.scan_files(self.config.add_words_dir)
        if not add_files:
            print("没有找到新词文件")
            return {}
        
        new_words = {}
        for file_path in add_files:
            new_words.update(self.reader.to_dict(file_path))
        
        if not new_words:
            print("没有找到新词")
            return {}
        
        return self.add_words(new_words)
    
    def correct_codes(self) -> Tuple[int, List[str]]:
        """纠正编码"""
        errors = 0
        error_words = []
        
        for word, info in self.data.items():
            if '?' in info['key']:
                new_key = ''
                for char in word:
                    if char in self.words_dict:
                        new_key += self.words_dict[char]['key'][:2]
                    else:
                        new_key = '?'
                        error_words.append(word)
                        break
                info['key'] = new_key
        
        if error_words:
            errors = len(error_words)
            print(f"补码失败: {error_words}")
        
        return errors, error_words
    
    def query(self, query_str: str):
        """查词或查编码"""
        if re.match(r'[a-z]+', query_str):
            # 查编码
            for word, info in self.data.items():
                if info['key'] == query_str:
                    print(f'{word}: {info}')
            for char, info in self.words_dict.items():
                if info['key'] == query_str:
                    print(f'{char}: {info}')
        else:
            # 查词
            if query_str in self.data:
                print(f'{query_str}: {self.data[query_str]}')
            if query_str in self.words_dict:
                print(f'{query_str}: {self.words_dict[query_str]}')
    
    def count_high_keys(self, min_len: int, min_count: int):
        """统计高频编码"""
        key_counts = {}
        for info in self.data.values():
            if len(info['key']) < min_len:
                continue
            key = info['key']
            key_counts[key] = key_counts.get(key, 0) + 1
        
        for key, count in key_counts.items():
            if count >= min_count:
                print(f'{key}: {count}')
    
    def replace_key(self, word: str, new_key: str):
        """替换编码"""
        if word in self.data:
            print(f'原编码: {word}\n{self.data[word]}')
            self.data[word]['key'] = new_key
        else:
            print(f'词"{word}"不存在')
    
    def clear_backups(self, confirm: str = ""):
        """清理备份文件"""
        if confirm != 'y':
            return
        
        count = 0
        for f in os.listdir(self.config.base_dir):
            if 'output.txt' in f and '.bak' in f:
                path = os.path.join(self.config.base_dir, f)
                os.remove(path)
                count += 1
        
        print(f'清除冗余文件: {count}个')
        self.bak_counter = 0
    
    def add_to_filter(self, word: str):
        """添加词到过滤列表"""
        filter_file = os.path.join(self.config.to_filter_dir, 'cs.txt')
        with open(filter_file, 'a', encoding='utf-8') as f:
            f.write(f'{word}\n')
        self.filter()
    
    def remove_words(self, words: List[str]):
        """删除指定词语"""
        removed = 0
        for word in words:
            if word in self.data:
                self.data.pop(word, None)
                removed += 1
        print(f"总计过滤: {removed}条")
    
    def refresh_words_dict(self):
        """刷新字表"""
        new_words = self.reader.read_lines(self.config.single_word_file)
        new_dict = {}
        dup_words = []
        dup_count = 0
        
        for item in new_words:
            word, key = item[0], item[1]
            
            if word not in new_dict:
                new_dict[word] = key
            else:
                dup_count += 1
                min_len = min(len(key), len(new_dict[word]))
                if key[:min_len] == new_dict[word][:min_len] and len(key) > len(new_dict[word]):
                    new_dict[word] = key
                else:
                    dup_words.append(item)
        
        print(f'重复词数: {dup_count}')
        self.writer.write_simple(new_dict, '/home/wtuj/tools/words.txt')
        if dup_words:
            with open('/home/wtuj/tools/mbDictTool/dupWords.txt', 'a', encoding='utf-8') as f:
                for item in dup_words:
                    f.write(f'{item[0]}\t{item[1]}\n')
    
    def _generate_key(self, word: str) -> str:
        """生成编码"""
        key = ''
        for char in word:
            if char in self.words_dict:
                key += self.words_dict[char]['key'][:2]
            else:
                return '?'
        return key
