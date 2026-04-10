"""测试权重计算服务"""
import pytest
import random
import string
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.weight import WeightCalculator
from app.services.dict import DictService
from app.dal.database import SessionLocal
from app.dal.init_db import init_database

# 初始化数据库
init_database()

# 生成随机字符串
def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def test_calculate_weight():
    """测试计算权重"""
    db = SessionLocal()
    try:
        weight_calc = WeightCalculator(db)
        
        # 测试不同长度的词的权重
        test_words = ["你", "你好", "你好吗", "你好吗？", "你好吗？我很好"]
        
        for word in test_words:
            weight = weight_calc.calculate_weight(word)
            assert weight > 0
            assert weight <= 100
    finally:
        db.close()


def test_update_word_weight():
    """测试更新词条权重"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        weight_calc = WeightCalculator(db)
        
        # 生成随机测试数据
        test_word = f"测试_{random_string()}"
        test_code = f"cs_{random_string()}"
        
        # 先添加一个词条
        dict_service.add_word(test_word, test_code, 1.0)
        
        # 更新权重
        result = weight_calc.update_word_weight(test_word, 0.5)
        assert result["word"] == test_word
        # 使用近似比较，避免浮点数精度问题
        assert abs(result["new_weight"] - result["old_weight"]) > 0.01
        assert result["new_weight"] > result["old_weight"]
        
        # 尝试更新不存在的词条，应该失败
        with pytest.raises(Exception):
            weight_calc.update_word_weight(f"不存在的词_{random_string()}", 0.5)
        
        # 清理测试数据
        dict_service.delete_word(test_word)
    finally:
        db.close()


def test_set_weight_directly():
    """测试直接设置权重"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        weight_calc = WeightCalculator(db)
        
        # 生成随机测试数据
        test_word = f"测试_{random_string()}"
        test_code = f"cs_{random_string()}"
        
        # 先添加一个词条
        dict_service.add_word(test_word, test_code, 1.0)
        
        # 直接设置权重
        new_weight = 10.0
        result = weight_calc.set_weight_directly(test_word, new_weight)
        assert result["word"] == test_word
        assert result["new_weight"] == new_weight
        
        # 尝试设置无效的权重，应该失败
        with pytest.raises(Exception):
            weight_calc.set_weight_directly(test_word, 0.0)
        
        with pytest.raises(Exception):
            weight_calc.set_weight_directly(test_word, 101.0)
    finally:
        db.close()


def test_adjust_same_code_weights():
    """测试调整同码词权重"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        weight_calc = WeightCalculator(db)
        
        # 生成随机测试数据
        test_code = f"cs_{random_string()}"
        
        # 添加多个同码词
        dict_service.add_word(f"测试词1_{random_string()}", test_code, 5.0)
        dict_service.add_word(f"测试词2_{random_string()}", test_code, 5.0)
        dict_service.add_word(f"测试词3_{random_string()}", test_code, 5.0)
        
        # 调整同码词权重
        results = weight_calc.adjust_same_code_weights(test_code)
        assert len(results) >= 2  # 至少有两个词的权重被调整
        
        # 验证权重递减
        weights = [result["new_weight"] for result in results]
        assert all(weights[i] >= weights[i+1] for i in range(len(weights)-1))
    finally:
        db.close()


def test_get_weight_stats():
    """测试获取权重统计信息"""
    db = SessionLocal()
    try:
        weight_calc = WeightCalculator(db)
        
        # 获取权重统计
        stats = weight_calc.get_weight_stats()
        assert "total_words" in stats
        assert "average_weight" in stats
        assert "max_weight" in stats
        assert "min_weight" in stats
        
        # 验证统计信息的类型
        assert isinstance(stats["total_words"], int)
        assert isinstance(stats["average_weight"], float)
        assert isinstance(stats["max_weight"], float)
        assert isinstance(stats["min_weight"], float)
    finally:
        db.close()