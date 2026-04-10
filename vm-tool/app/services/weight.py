"""权重计算服务"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import logging

from app.dal.repositories import WordRepository
from app.dal.database import get_db
from app.core.errors import WeightError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeightCalculator:
    """权重计算引擎"""
    
    def __init__(self, db: Session = None):
        if db:
            self.db = db
        else:
            self.db = next(get_db())
        self.repo = WordRepository(self.db)
    
    def calculate_weight(self, word: str, base_weight: float = 1.0) -> float:
        """计算单个词的权重"""
        try:
            # 基于词长的权重调整
            length_factor = 1.0
            if len(word) == 1:
                length_factor = 1.5  # 单字权重更高
            elif len(word) > 4:
                length_factor = 0.8  # 长词权重降低
            
            # 基于词频的权重调整（这里需要实际的词频数据）
            frequency_factor = 1.0
            
            # 基于使用频率的权重调整（这里需要实际的使用数据）
            usage_factor = 1.0
            
            # 计算最终权重
            weight = base_weight * length_factor * frequency_factor * usage_factor
            
            # 限制权重范围
            return max(0.1, min(weight, 100.0))
        except Exception as e:
            logger.error(f"计算权重失败: {e}")
            raise WeightError(f"计算权重失败: {e}")
    
    def update_word_weight(self, word: str, increment: float = 0.1) -> Dict[str, Any]:
        """更新单个词的权重"""
        try:
            db_word = self.repo.get_by_word(word)
            if not db_word:
                raise WeightError(f"词条 '{word}' 不存在")
            
            # 计算新权重
            new_weight = self.calculate_weight(word, db_word.weight + increment)
            
            # 更新权重
            updated = self.repo.update(db_word.id, weight=new_weight)
            return {
                "word": updated.word,
                "old_weight": db_word.weight,
                "new_weight": updated.weight
            }
        except WeightError:
            raise
        except Exception as e:
            logger.error(f"更新权重失败: {e}")
            raise WeightError(f"更新权重失败: {e}")
    
    def batch_update_weights(self, words: List[str], increment: float = 0.1) -> Dict[str, Any]:
        """批量更新权重"""
        try:
            updated = 0
            not_found = []
            
            for word in words:
                try:
                    self.update_word_weight(word, increment)
                    updated += 1
                except WeightError:
                    not_found.append(word)
            
            return {
                "updated": updated,
                "not_found": len(not_found),
                "not_found_words": not_found
            }
        except Exception as e:
            logger.error(f"批量更新权重失败: {e}")
            raise WeightError(f"批量更新权重失败: {e}")
    
    def adjust_same_code_weights(self, code: str) -> List[Dict[str, Any]]:
        """调整同码词的权重"""
        try:
            # 获取同码词
            words = self.repo.get_by_code(code)
            if len(words) <= 1:
                return []
            
            # 按当前权重排序
            words.sort(key=lambda x: x.weight, reverse=True)
            
            # 调整权重，确保权重递减
            adjusted = []
            base_weight = words[0].weight
            
            for i, word in enumerate(words):
                if i == 0:
                    # 第一个词保持权重不变
                    new_weight = base_weight
                else:
                    # 后续词权重递减
                    new_weight = base_weight * (0.8 ** i)
                
                # 更新权重
                if abs(word.weight - new_weight) > 0.01:  # 只有权重变化超过0.01才更新
                    updated = self.repo.update(word.id, weight=new_weight)
                    adjusted.append({
                        "word": updated.word,
                        "old_weight": word.weight,
                        "new_weight": updated.weight
                    })
            
            return adjusted
        except Exception as e:
            logger.error(f"调整同码词权重失败: {e}")
            raise WeightError(f"调整同码词权重失败: {e}")
    
    def set_weight_directly(self, word: str, weight: float) -> Dict[str, Any]:
        """直接设置权重"""
        try:
            db_word = self.repo.get_by_word(word)
            if not db_word:
                raise WeightError(f"词条 '{word}' 不存在")
            
            # 验证权重范围
            if weight < 0.1 or weight > 100.0:
                raise WeightError("权重必须在 0.1 到 100.0 之间")
            
            # 更新权重
            updated = self.repo.update(db_word.id, weight=weight)
            return {
                "word": updated.word,
                "old_weight": db_word.weight,
                "new_weight": updated.weight
            }
        except WeightError:
            raise
        except Exception as e:
            logger.error(f"直接设置权重失败: {e}")
            raise WeightError(f"直接设置权重失败: {e}")
    
    def get_weight_stats(self) -> Dict[str, Any]:
        """获取权重统计信息"""
        try:
            all_words = self.repo.get_all()
            if not all_words:
                return {
                    "total_words": 0,
                    "average_weight": 0.0,
                    "max_weight": 0.0,
                    "min_weight": 0.0
                }
            
            weights = [word.weight for word in all_words]
            return {
                "total_words": len(all_words),
                "average_weight": sum(weights) / len(weights),
                "max_weight": max(weights),
                "min_weight": min(weights)
            }
        except Exception as e:
            logger.error(f"获取权重统计失败: {e}")
            raise WeightError(f"获取权重统计失败: {e}")
