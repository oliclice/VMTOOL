"""测试过滤和导入服务"""
import pytest
import random
import string
import tempfile
import os
import json
import csv
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.filter import FilterService
from app.services.dict import DictService
from app.dal.database import SessionLocal
from app.dal.init_db import init_database

# 初始化数据库
init_database()

# 生成随机字符串
def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def test_filter_by_length():
    """测试根据词长过滤"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        filter_service = FilterService(db)
        
        # 生成测试数据
        test_words = [
            ("a", "a", 1.0),
            ("ab", "ab", 1.0),
            ("abc", "abc", 1.0),
            ("abcd", "abcd", 1.0),
            ("abcde", "abcde", 1.0)
        ]
        
        for word, code, weight in test_words:
            try:
                dict_service.add_word(word, code, weight)
            except Exception:
                pass  # 忽略已存在的词条
        
        # 测试过滤
        results = filter_service.filter_by_length(min_length=2, max_length=3)
        assert len(results) >= 2  # 至少有两个词
        
        for result in results:
            length = len(result["word"])
            assert 2 <= length <= 3
    finally:
        db.close()


def test_filter_by_weight():
    """测试根据权重过滤"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        filter_service = FilterService(db)
        
        # 生成测试数据
        test_words = [
            (f"test1_{random_string()}", "t1", 1.0),
            (f"test2_{random_string()}", "t2", 5.0),
            (f"test3_{random_string()}", "t3", 10.0)
        ]
        
        for word, code, weight in test_words:
            try:
                dict_service.add_word(word, code, weight)
            except Exception:
                pass  # 忽略已存在的词条
        
        # 测试过滤
        results = filter_service.filter_by_weight(min_weight=5.0)
        assert len(results) >= 2  # 至少有两个词
        
        for result in results:
            assert result["weight"] >= 5.0
    finally:
        db.close()


def test_filter_by_pattern():
    """测试根据模式过滤"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        filter_service = FilterService(db)
        
        # 生成测试数据
        prefix = f"test_{random_string()}"
        test_words = [
            (f"{prefix}1", "t1", 1.0),
            (f"{prefix}2", "t2", 1.0),
            (f"{prefix}3", "t3", 1.0)
        ]
        
        for word, code, weight in test_words:
            try:
                dict_service.add_word(word, code, weight)
            except Exception:
                pass  # 忽略已存在的词条
        
        # 测试过滤
        results = filter_service.filter_by_pattern(prefix)
        assert len(results) >= 3  # 至少有三个词
    finally:
        db.close()


def test_import_from_txt():
    """测试从TXT文件导入"""
    db = SessionLocal()
    try:
        filter_service = FilterService(db)
        dict_service = DictService(db)

        # 生成唯一的测试数据
        unique_suffix = random_string()

        # 创建临时TXT文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(f"测试1_{unique_suffix}\ttest1_{unique_suffix}\t1.0\n")
            f.write(f"测试2_{unique_suffix}\ttest2_{unique_suffix}\t2.0\n")
            f.write(f"测试3_{unique_suffix}\ttest3_{unique_suffix}\t3.0\n")
            temp_file = f.name

        try:
            # 导入文件
            result = filter_service.import_from_txt(temp_file)
            assert result["added"] >= 3  # 至少添加了三个词
            
            # 清理测试数据
            dict_service.delete_word(f"测试1_{unique_suffix}")
            dict_service.delete_word(f"测试2_{unique_suffix}")
            dict_service.delete_word(f"测试3_{unique_suffix}")
        finally:
            # 清理临时文件
            os.unlink(temp_file)
    finally:
        db.close()


def test_import_from_csv():
    """测试从CSV文件导入"""
    db = SessionLocal()
    try:
        filter_service = FilterService(db)
        dict_service = DictService(db)

        # 生成唯一的测试数据
        unique_suffix = random_string()

        # 创建临时CSV文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['word', 'code', 'weight'])
            writer.writerow([f'测试1_{unique_suffix}', f'test1_{unique_suffix}', '1.0'])
            writer.writerow([f'测试2_{unique_suffix}', f'test2_{unique_suffix}', '2.0'])
            writer.writerow([f'测试3_{unique_suffix}', f'test3_{unique_suffix}', '3.0'])
            temp_file = f.name

        try:
            # 导入文件
            result = filter_service.import_from_csv(temp_file)
            assert result["added"] >= 3  # 至少添加了三个词
            
            # 清理测试数据
            dict_service.delete_word(f"测试1_{unique_suffix}")
            dict_service.delete_word(f"测试2_{unique_suffix}")
            dict_service.delete_word(f"测试3_{unique_suffix}")
        finally:
            # 清理临时文件
            os.unlink(temp_file)
    finally:
        db.close()


def test_import_from_json():
    """测试从JSON文件导入"""
    db = SessionLocal()
    try:
        filter_service = FilterService(db)
        dict_service = DictService(db)

        # 生成唯一的测试数据
        unique_suffix = random_string()

        # 创建临时JSON文件
        test_data = [
            {"word": f"测试1_{unique_suffix}", "code": f"test1_{unique_suffix}", "weight": 1.0},
            {"word": f"测试2_{unique_suffix}", "code": f"test2_{unique_suffix}", "weight": 2.0},
            {"word": f"测试3_{unique_suffix}", "code": f"test3_{unique_suffix}", "weight": 3.0}
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name

        try:
            # 导入文件
            result = filter_service.import_from_json(temp_file)
            assert result["added"] >= 3  # 至少添加了三个词
            
            # 清理测试数据
            dict_service.delete_word(f"测试1_{unique_suffix}")
            dict_service.delete_word(f"测试2_{unique_suffix}")
            dict_service.delete_word(f"测试3_{unique_suffix}")
        finally:
            # 清理临时文件
            os.unlink(temp_file)
    finally:
        db.close()


def test_export_to_txt():
    """测试导出到TXT文件"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        filter_service = FilterService(db)
        
        # 添加测试数据
        test_word = f"测试_{random_string()}"
        dict_service.add_word(test_word, "test", 1.0)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_file = f.name
        
        try:
            # 导出文件
            count = filter_service.export_to_txt(temp_file)
            assert count >= 1  # 至少导出了一个词
            
            # 验证文件内容
            with open(temp_file, 'r') as f:
                content = f.read()
                assert test_word in content
        finally:
            os.unlink(temp_file)
    finally:
        db.close()


def test_export_to_csv():
    """测试导出到CSV文件"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        filter_service = FilterService(db)
        
        # 添加测试数据
        test_word = f"测试_{random_string()}"
        dict_service.add_word(test_word, "test", 1.0)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name
        
        try:
            # 导出文件
            count = filter_service.export_to_csv(temp_file)
            assert count >= 1  # 至少导出了一个词
            
            # 验证文件内容
            with open(temp_file, 'r') as f:
                content = f.read()
                assert test_word in content
        finally:
            os.unlink(temp_file)
    finally:
        db.close()


def test_export_to_json():
    """测试导出到JSON文件"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        filter_service = FilterService(db)
        
        # 添加测试数据
        test_word = f"测试_{random_string()}"
        dict_service.add_word(test_word, "test", 1.0)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # 导出文件
            count = filter_service.export_to_json(temp_file)
            assert count >= 1  # 至少导出了一个词
            
            # 验证文件内容
            with open(temp_file, 'r') as f:
                data = json.load(f)
                assert any(item["word"] == test_word for item in data)
        finally:
            os.unlink(temp_file)
    finally:
        db.close()