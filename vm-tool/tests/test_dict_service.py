"""测试词条服务"""
import pytest
import random
import string
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.dict import DictService
from app.dal.database import SessionLocal
from app.dal.init_db import init_database

# 初始化数据库
init_database()

# 生成随机字符串
def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def test_add_word():
    """测试添加词条"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        
        # 生成随机测试数据
        test_word = f"测试_{random_string()}"
        test_code = f"cs_{random_string()}"
        
        # 添加一个新词条
        result = dict_service.add_word(test_word, test_code, 1.0)
        assert result["word"] == test_word
        assert result["code"] == test_code
        assert result["weight"] == 1.0
        
        # 尝试添加相同的词条，应该失败
        with pytest.raises(Exception):
            dict_service.add_word(test_word, test_code, 1.0)
    finally:
        db.close()


def test_get_word():
    """测试获取词条"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        
        # 生成随机测试数据
        test_word = f"测试_{random_string()}"
        test_code = f"cs_{random_string()}"
        
        # 先添加一个词条
        dict_service.add_word(test_word, test_code, 1.0)
        
        # 获取词条
        result = dict_service.get_word(test_word)
        assert result["word"] == test_word
        assert result["code"] == test_code
        assert result["weight"] == 1.0
        
        # 获取不存在的词条，应该返回None
        result = dict_service.get_word(f"不存在的词_{random_string()}")
        assert result is None
    finally:
        db.close()


def test_update_word():
    """测试更新词条"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        
        # 生成随机测试数据
        test_word = f"测试_{random_string()}"
        test_code = f"cs_{random_string()}"
        new_code = f"cs_{random_string()}"
        
        # 先添加一个词条
        dict_service.add_word(test_word, test_code, 1.0)
        
        # 更新词条
        result = dict_service.update_word(test_word, code=new_code, weight=1.5)
        assert result["word"] == test_word
        assert result["code"] == new_code
        assert result["weight"] == 1.5
        
        # 尝试更新不存在的词条，应该失败
        with pytest.raises(Exception):
            dict_service.update_word(f"不存在的词_{random_string()}", code="cs", weight=1.0)
    finally:
        db.close()


def test_delete_word():
    """测试删除词条"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        
        # 生成随机测试数据
        test_word = f"测试_{random_string()}"
        test_code = f"cs_{random_string()}"
        
        # 先添加一个词条
        dict_service.add_word(test_word, test_code, 1.0)
        
        # 删除词条
        result = dict_service.delete_word(test_word)
        assert result is True
        
        # 尝试删除不存在的词条，应该抛出异常
        with pytest.raises(Exception):
            dict_service.delete_word(f"不存在的词_{random_string()}")
    finally:
        db.close()


def test_search_words():
    """测试搜索词条"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        
        # 生成随机测试数据
        prefix = f"测试_{random_string()}"
        
        # 先添加一些词条
        dict_service.add_word(f"{prefix}5", "cs5", 1.0)
        dict_service.add_word(f"{prefix}6", "cs6", 1.0)
        dict_service.add_word(f"{prefix}7", "cs7", 1.0)
        
        # 搜索词条
        results = dict_service.search_words(prefix)
        assert len(results) >= 3
        
        # 搜索不存在的词条，应该返回空列表
        results = dict_service.search_words(f"不存在的词_{random_string()}")
        assert len(results) == 0
    finally:
        db.close()
