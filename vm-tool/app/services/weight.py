"""权重计算服务"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging

from app.dal.repositories import WordRepository
from app.dal.database import get_db
from app.core.errors import WeightError
from app.services.thuocl import load_thuocl_data, get_log_weight

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
        """计算单个词的权重

        使用词频数据: weight = base_weight * (1 + log10(词频))
        不在词频表中的词，log 部分为 0，权重等于 base_weight。
        """
        try:
            # 加载词频数据
            # __file__ = vm-tool/app/services/weight.py，向上两级到 vm-tool/
            import os
            data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
            data_dir = os.path.abspath(data_dir)
            freq_dict = load_thuocl_data(data_dir)

            # 获取对数权重
            log_freq = get_log_weight(word, freq_dict)

            # 计算最终权重
            weight = base_weight * (1 + log_freq)

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

    def recalculate_all_weights(self, progress_callback=None) -> Dict[str, Any]:
        """重新计算所有词条的权重

        使用 base_weight=1.0，基于词频对数重新计算。
        只计算词表（is_character=False, is_special=False），不计算字表和特殊表。
        每 1000 条批量提交一次事务。
        """
        try:
            import os
            data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
            data_dir = os.path.abspath(data_dir)
            freq_dict = load_thuocl_data(data_dir)  # 预加载缓存

            # 只获取词表（非单字、非特殊字符）
            all_words = self.repo.get_all_by_type("words")
            total = len(all_words)
            updated = 0
            batch_size = 1000

            for i, db_word in enumerate(all_words):
                log_freq = get_log_weight(db_word.word, freq_dict)
                new_weight = 1.0 * (1 + log_freq)
                new_weight = max(0.1, min(new_weight, 100.0))

                if abs(db_word.weight - new_weight) > 0.01:
                    db_word.weight = new_weight
                    updated += 1

                # 每 batch_size 条提交一次
                if (i + 1) % batch_size == 0 or (i + 1) == total:
                    self.db.commit()

                if progress_callback and total > 0:
                    pct = int((i + 1) / total * 100)
                    progress_callback(pct, f"计算权重: {i + 1}/{total}")

            return {
                "total": total,
                "updated": updated
            }
        except Exception as e:
            logger.error(f"重新计算权重失败: {e}")
            raise WeightError(f"重新计算权重失败: {e}")

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
            
            # 保存旧权重（在更新之前）
            old_weight = db_word.weight
            
            # 更新权重
            updated = self.repo.update(db_word.id, weight=weight)
            return {
                "word": updated.word,
                "old_weight": old_weight,
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
