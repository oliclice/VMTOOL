"""统计和分析服务"""
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
from sqlalchemy.orm import Session
import logging

from app.dal.repositories import WordRepository
from app.dal.database import get_db
from app.core.errors import DictError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StatsService:
    """统计和分析服务"""
    
    def __init__(self, db: Optional[Session] = None):
        if db:
            self.db = db
        else:
            self.db = next(get_db())
        self.repo = WordRepository(self.db)
    
    def get_word_length_stats(self) -> Dict[str, Any]:
        """获取词长统计"""
        try:
            all_words = self.repo.get_all()
            length_counter: Counter[int] = Counter()
            
            for word in all_words:
                length = len(word.word)
                length_counter[length] += 1
            
            return {
                "total_words": len(all_words),
                "length_distribution": dict(length_counter),
                "average_length": sum(len(word.word) for word in all_words) / len(all_words) if all_words else 0
            }
        except Exception as e:
            logger.error(f"获取词长统计失败: {e}")
            raise DictError(f"获取词长统计失败: {e}")
    
    def get_code_stats(self) -> Dict[str, Any]:
        """获取编码统计"""
        try:
            all_words = self.repo.get_all()
            code_length_counter: Counter[int] = Counter()
            code_counter: Counter[str] = Counter()
            
            for word in all_words:
                code_length = len(word.code)
                code_length_counter[code_length] += 1
                code_counter[word.code] += 1
            
            # 计算编码冲突
            conflicts = {code: count for code, count in code_counter.items() if count > 1}
            
            return {
                "total_codes": len(code_counter),
                "code_length_distribution": dict(code_length_counter),
                "conflicts": conflicts,
                "conflict_count": len(conflicts),
                "code_frequency": dict(code_counter)
            }
        except Exception as e:
            logger.error(f"获取编码统计失败: {e}")
            raise DictError(f"获取编码统计失败: {e}")
    
    def detect_code_conflicts(self) -> List[Dict[str, Any]]:
        """检测编码冲突"""
        try:
            all_words = self.repo.get_all()
            code_to_words = defaultdict(list)
            
            for word in all_words:
                code_to_words[word.code].append({
                    "word": word.word,
                    "weight": word.weight
                })
            
            conflicts = []
            for code, words in code_to_words.items():
                if len(words) > 1:
                    # 按权重排序
                    words.sort(key=lambda x: x["weight"], reverse=True)
                    conflicts.append({
                        "code": code,
                        "words": words,
                        "count": len(words)
                    })
            
            return conflicts
        except Exception as e:
            logger.error(f"检测编码冲突失败: {e}")
            raise DictError(f"检测编码冲突失败: {e}")
    
    def get_weight_stats(self) -> Dict[str, Any]:
        """获取权重统计"""
        try:
            all_words = self.repo.get_all()
            if not all_words:
                return {
                    "total_words": 0,
                    "average_weight": 0.0,
                    "max_weight": 0.0,
                    "min_weight": 0.0,
                    "weight_distribution": {}
                }
            
            weights = [word.weight for word in all_words]
            weight_ranges = {
                "0-10": 0,
                "10-20": 0,
                "20-30": 0,
                "30-40": 0,
                "40-50": 0,
                "50+": 0
            }
            
            for weight in weights:
                if weight < 10:
                    weight_ranges["0-10"] += 1
                elif weight < 20:
                    weight_ranges["10-20"] += 1
                elif weight < 30:
                    weight_ranges["20-30"] += 1
                elif weight < 40:
                    weight_ranges["30-40"] += 1
                elif weight < 50:
                    weight_ranges["40-50"] += 1
                else:
                    weight_ranges["50+"] += 1
            
            return {
                "total_words": len(all_words),
                "average_weight": sum(weights) / len(weights),
                "max_weight": float(max(weights)),
                "min_weight": float(min(weights)),
                "weight_distribution": weight_ranges
            }
        except Exception as e:
            logger.error(f"获取权重统计失败: {e}")
            raise DictError(f"获取权重统计失败: {e}")
    
    def get_high_frequency_words(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取高频词（按权重排序）"""
        try:
            all_words = self.repo.get_all()
            # 按权重排序
            sorted_words = sorted(all_words, key=lambda x: float(x.weight), reverse=True)
            
            return [{
                "word": word.word,
                "code": word.code,
                "weight": word.weight
            } for word in sorted_words[:limit]]
        except Exception as e:
            logger.error(f"获取高频词失败: {e}")
            raise DictError(f"获取高频词失败: {e}")
    
    def analyze_usage_patterns(self) -> Dict[str, Any]:
        """分析使用模式"""
        try:
            all_words = self.repo.get_all()
            
            # 词长分析
            length_stats = self.get_word_length_stats()
            
            # 编码分析
            code_stats = self.get_code_stats()
            
            # 权重分析
            weight_stats = self.get_weight_stats()
            
            # 计算平均编码长度
            avg_code_length = sum(len(word.code) for word in all_words) / len(all_words) if all_words else 0
            
            return {
                "total_words": len(all_words),
                "average_word_length": length_stats.get("average_length", 0),
                "average_code_length": avg_code_length,
                "code_conflict_rate": code_stats.get("conflict_count", 0) / code_stats.get("total_codes", 1) if code_stats.get("total_codes", 0) > 0 else 0,
                "weight_distribution": weight_stats.get("weight_distribution", {}),
                "length_distribution": length_stats.get("length_distribution", {})
            }
        except Exception as e:
            logger.error(f"分析使用模式失败: {e}")
            raise DictError(f"分析使用模式失败: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """生成综合报告"""
        try:
            # 获取所有词条
            all_words_data = []
            all_words = self.repo.get_all()
            for word in all_words:
                all_words_data.append({
                    "word": word.word,
                    "code": word.code,
                    "weight": word.weight
                })
            
            report = {
                "word_length_stats": self.get_word_length_stats(),
                "code_stats": self.get_code_stats(),
                "weight_stats": self.get_weight_stats(),
                "high_frequency_words": self.get_high_frequency_words(20),
                "code_conflicts": self.detect_code_conflicts(),
                "usage_patterns": self.analyze_usage_patterns(),
                "all_words": all_words_data
            }
            
            return report
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            raise DictError(f"生成报告失败: {e}")
