"""测试统计和分析服务"""
import pytest
import random
import string
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.stats import StatsService
from app.services.dict import DictService
from app.dal.database import SessionLocal
from app.dal.init_db import init_database

# 初始化数据库
init_database()

# 生成随机字符串
def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def test_get_word_length_stats():
    """测试获取词长统计"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        stats_service = StatsService(db)
        
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
        
        # 获取词长统计
        stats = stats_service.get_word_length_stats()
        assert "total_words" in stats
        assert "length_distribution" in stats
        assert "average_length" in stats
        
        # 验证统计信息
        assert stats["total_words"] >= 5
        assert 1 in stats["length_distribution"]
        assert 2 in stats["length_distribution"]
        assert 3 in stats["length_distribution"]
        assert 4 in stats["length_distribution"]
        assert 5 in stats["length_distribution"]
    finally:
        db.close()


def test_get_code_stats():
    """测试获取编码统计"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        stats_service = StatsService(db)
        
        # 生成测试数据
        test_words = [
            (f"test1_{random_string()}", "test", 1.0),
            (f"test2_{random_string()}", "test", 1.0),  # 同码词
            (f"test3_{random_string()}", "test3", 1.0)
        ]
        
        for word, code, weight in test_words:
            try:
                dict_service.add_word(word, code, weight)
            except Exception:
                pass  # 忽略已存在的词条
        
        # 获取编码统计
        stats = stats_service.get_code_stats()
        assert "total_codes" in stats
        assert "code_length_distribution" in stats
        assert "conflicts" in stats
        assert "conflict_count" in stats
        
        # 验证统计信息
        assert stats["total_codes"] >= 2
        assert stats["conflict_count"] >= 1  # 至少有一个编码冲突
    finally:
        db.close()


def test_detect_code_conflicts():
    """测试检测编码冲突"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        stats_service = StatsService(db)
        
        # 生成测试数据
        test_code = f"test_{random_string()}"
        test_words = [
            (f"test1_{random_string()}", test_code, 1.0),
            (f"test2_{random_string()}", test_code, 1.0),
            (f"test3_{random_string()}", test_code, 1.0)
        ]
        
        for word, code, weight in test_words:
            try:
                dict_service.add_word(word, code, weight)
            except Exception:
                pass  # 忽略已存在的词条
        
        # 检测编码冲突
        conflicts = stats_service.detect_code_conflicts()
        assert len(conflicts) >= 1  # 至少有一个编码冲突
        
        # 验证冲突信息
        conflict_found = False
        for conflict in conflicts:
            if conflict["code"] == test_code:
                conflict_found = True
                assert conflict["count"] >= 3
                assert len(conflict["words"]) >= 3
                break
        assert conflict_found
    finally:
        db.close()


def test_get_weight_stats():
    """测试获取权重统计"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        stats_service = StatsService(db)
        
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
        
        # 获取权重统计
        stats = stats_service.get_weight_stats()
        assert "total_words" in stats
        assert "average_weight" in stats
        assert "max_weight" in stats
        assert "min_weight" in stats
        assert "weight_distribution" in stats
        
        # 验证统计信息
        assert stats["total_words"] >= 3
        assert stats["max_weight"] >= 10.0
        assert stats["min_weight"] <= 1.0
    finally:
        db.close()


def test_get_high_frequency_words():
    """测试获取高频词"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        stats_service = StatsService(db)
        
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
        
        # 获取高频词
        high_freq_words = stats_service.get_high_frequency_words(limit=2)
        assert len(high_freq_words) >= 2  # 至少返回两个词
        
        # 验证高频词按权重排序
        assert high_freq_words[0]["weight"] >= high_freq_words[1]["weight"]
    finally:
        db.close()


def test_analyze_usage_patterns():
    """测试分析使用模式"""
    db = SessionLocal()
    try:
        dict_service = DictService(db)
        stats_service = StatsService(db)
        
        # 生成测试数据
        test_words = [
            ("a", "a", 1.0),
            ("ab", "ab", 1.0),
            ("abc", "abc", 1.0)
        ]
        
        for word, code, weight in test_words:
            try:
                dict_service.add_word(word, code, weight)
            except Exception:
                pass  # 忽略已存在的词条
        
        # 分析使用模式
        patterns = stats_service.analyze_usage_patterns()
        assert "total_words" in patterns
        assert "average_word_length" in patterns
        assert "average_code_length" in patterns
        assert "code_conflict_rate" in patterns
        assert "weight_distribution" in patterns
        assert "length_distribution" in patterns
        
        # 验证分析结果
        assert patterns["total_words"] >= 3
        assert patterns["average_word_length"] >= 1.0
        assert patterns["average_code_length"] >= 1.0
    finally:
        db.close()


def test_generate_report():
    """测试生成综合报告"""
    db = SessionLocal()
    try:
        stats_service = StatsService(db)
        
        # 生成报告
        report = stats_service.generate_report()
        assert "word_length_stats" in report
        assert "code_stats" in report
        assert "weight_stats" in report
        assert "high_frequency_words" in report
        assert "code_conflicts" in report
        assert "usage_patterns" in report
        
        # 验证报告内容
        assert isinstance(report["word_length_stats"], dict)
        assert isinstance(report["code_stats"], dict)
        assert isinstance(report["weight_stats"], dict)
        assert isinstance(report["high_frequency_words"], list)
        assert isinstance(report["code_conflicts"], list)
        assert isinstance(report["usage_patterns"], dict)
    finally:
        db.close()