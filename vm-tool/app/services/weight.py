"""权重计算服务"""
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import cache
from app.core.errors import WeightError
from app.dal.database import get_db
from app.dal.repositories import WordRepository
from app.services.thuocl import get_log_weight, load_thuocl_data

logger = logging.getLogger(__name__)


class WeightCalculator:
    """权重计算引擎

    会话所有权：``db=None`` 时自建会话并持有，调用方需调 :meth:`close` 释放
    （也可作上下文管理器）；``db=<外部会话>`` 时由注入方负责关闭。
    """

    def __init__(self, db: Session = None):
        # 显式创建会话（不再对生成器取一次 next：close 时机取决于 GC）
        self._owns_db = db is None
        self.db = db if db is not None else get_db()
        self.repo = WordRepository(self.db)

    def close(self) -> None:
        """释放本服务自建的会话（幂等）；外部注入的会话由注入方关闭。"""
        if not self._owns_db:
            return
        db, self.db = self.db, None
        if db is not None:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"关闭数据库会话失败: {e}")

    def __enter__(self) -> "WeightCalculator":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _invalidate_cache(self) -> None:
        """写成功后使查询缓存失效（与 DictService._notify_data_changed 同一写法/位置）。

        `DictService.get_word()` 等读路径挂在模块级全局 cache 上（app/core/cache.py），
        权重写入同样必须让这些缓存失效；否则长驻实例在 ttl 内会读到写前的旧权重
        （T7 实测：get_word 读到 1.0 → set_weight_directly(5.0) → 同一实例再读仍是
        1.0，而全新实例已读到 5.0）。本服务没有数据变更回调，故只做失效。
        """
        cache.clear()

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
            raise WeightError(f"计算权重失败: {e}") from e

    def update_word_weight(self, word: str, increment: float = 0.1) -> dict[str, Any]:
        """更新单个词的权重"""
        try:
            db_word = self.repo.get_by_word(word)
            if not db_word:
                raise WeightError(f"词条 '{word}' 不存在")

            # 计算新权重
            new_weight = self.calculate_weight(word, db_word.weight + increment)

            # 更新权重
            updated = self.repo.update(db_word.id, weight=new_weight)
            self._invalidate_cache()
            return {
                "word": updated.word,
                "old_weight": db_word.weight,
                "new_weight": updated.weight,
            }
        except WeightError:
            raise
        except Exception as e:
            logger.error(f"更新权重失败: {e}")
            raise WeightError(f"更新权重失败: {e}") from e

    def batch_update_weights(
        self, words: list[str], increment: float = 0.1
    ) -> dict[str, Any]:
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
                "not_found_words": not_found,
            }
        except Exception as e:
            logger.error(f"批量更新权重失败: {e}")
            raise WeightError(f"批量更新权重失败: {e}") from e

    def recalculate_all_weights(self, progress_callback=None) -> dict[str, Any]:
        """重新计算所有词条的权重

        使用 base_weight=1.0，基于词频对数重新计算。
        根据配置选择要计算的码表范围（词表、字表、特殊表）。
        跳过手动设置的词条（manual=True）。
        每 1000 条批量提交一次事务。
        """
        try:
            import os

            from app.core.config_manager import config_manager

            data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
            data_dir = os.path.abspath(data_dir)
            freq_dict = load_thuocl_data(data_dir)  # 预加载缓存

            # 根据配置获取要计算的码表类型
            calc_words = config_manager.get("weight_calc_words", True)
            calc_chars = config_manager.get("weight_calc_chars", False)
            calc_special = config_manager.get("weight_calc_special", False)

            # 收集所有要计算的词条
            all_words = []
            if calc_words:
                all_words.extend(self.repo.get_all_by_type("words"))
            if calc_chars:
                all_words.extend(self.repo.get_all_by_type("chars"))
            if calc_special:
                all_words.extend(self.repo.get_all_by_type("special"))

            total = len(all_words)
            updated = 0
            batch_size = 1000

            for i, db_word in enumerate(all_words):
                # 跳过手动设置的词条
                if db_word.manual:
                    continue

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

            self._invalidate_cache()
            return {"total": total, "updated": updated}
        except Exception as e:
            logger.error(f"重新计算权重失败: {e}")
            raise WeightError(f"重新计算权重失败: {e}") from e

    def calculate_weights_for_words(
        self, word_list: list[dict[str, Any]], progress_callback=None
    ) -> dict[str, Any]:
        """计算指定词条列表的权重

        用于导入后只计算导入词条的权重，而不是重新计算所有词条。
        使用 base_weight=1.0，基于词频对数重新计算。
        跳过手动设置的词条（manual=True）。

        Args:
            word_list: 词条列表，每个词条包含 'word' 字段
            progress_callback: 进度回调函数
        """
        try:
            import os

            data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
            data_dir = os.path.abspath(data_dir)
            freq_dict = load_thuocl_data(data_dir)  # 预加载缓存

            # 从数据库中获取这些词条的最新状态
            word_names = [w.get("word") for w in word_list if w.get("word")]
            if not word_names:
                return {"total": 0, "updated": 0}

            # 批量查询数据库中的词条
            db_words = self.repo.get_by_words(word_names)

            total = len(db_words)
            updated = 0
            batch_size = 1000

            for i, db_word in enumerate(db_words):
                # 跳过手动设置的词条
                if db_word.manual:
                    continue

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

            self._invalidate_cache()
            return {"total": total, "updated": updated}
        except Exception as e:
            logger.error(f"计算指定词条权重失败: {e}")
            raise WeightError(f"计算指定词条权重失败: {e}") from e

    def adjust_same_code_weights(self, code: str) -> list[dict[str, Any]]:
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
                    new_weight = base_weight * (0.8**i)

                # 更新权重
                if abs(word.weight - new_weight) > 0.01:  # 只有权重变化超过0.01才更新
                    updated = self.repo.update(word.id, weight=new_weight)
                    adjusted.append(
                        {
                            "word": updated.word,
                            "old_weight": word.weight,
                            "new_weight": updated.weight,
                        }
                    )

            self._invalidate_cache()
            return adjusted
        except Exception as e:
            logger.error(f"调整同码词权重失败: {e}")
            raise WeightError(f"调整同码词权重失败: {e}") from e

    def set_weight_directly(self, word: str, weight: float) -> dict[str, Any]:
        """直接设置权重

        手动设置权重会将manual标记为True，这样在重新计算权重时会被跳过。
        """
        try:
            db_word = self.repo.get_by_word(word)
            if not db_word:
                raise WeightError(f"词条 '{word}' 不存在")

            # 验证权重范围
            if weight < 0.1 or weight > 100.0:
                raise WeightError("权重必须在 0.1 到 100.0 之间")

            # 保存旧权重（在更新之前）
            old_weight = db_word.weight

            # 更新权重，同时设置manual为True
            updated = self.repo.update(db_word.id, weight=weight, manual=True)
            self._invalidate_cache()
            return {
                "word": updated.word,
                "old_weight": old_weight,
                "new_weight": updated.weight,
            }
        except WeightError:
            raise
        except Exception as e:
            logger.error(f"直接设置权重失败: {e}")
            raise WeightError(f"直接设置权重失败: {e}") from e

    def get_weight_stats(self) -> dict[str, Any]:
        """获取权重统计信息"""
        try:
            all_words = self.repo.get_all()
            if not all_words:
                return {
                    "total_words": 0,
                    "average_weight": 0.0,
                    "max_weight": 0.0,
                    "min_weight": 0.0,
                }

            weights = [word.weight for word in all_words]
            return {
                "total_words": len(all_words),
                "average_weight": sum(weights) / len(weights),
                "max_weight": max(weights),
                "min_weight": min(weights),
            }
        except Exception as e:
            logger.error(f"获取权重统计失败: {e}")
            raise WeightError(f"获取权重统计失败: {e}") from e
