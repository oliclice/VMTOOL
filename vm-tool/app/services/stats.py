"""统计和分析服务"""
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from sqlalchemy.orm import Session
import logging

from app.dal.repositories import WordRepository
from app.dal.database import get_db
from app.core.errors import DictError
from app.core.config_manager import config_manager

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
            # 只统计词表数据，不包括字符和特殊字符
            word_list = [word for word in all_words if not word.is_character and not word.is_special]
            length_counter: Counter[int] = Counter()
            total_chars = 0
            total_special = 0

            for word in word_list:
                length = len(word.word)
                length_counter[length] += 1
                total_chars += length
                if word.is_special:
                    total_special += 1

            return {
                "total_words": len(word_list),
                "total_chars": total_chars,
                "total_special": total_special,
                "length_distribution": dict(length_counter),
                "average_length": sum(len(word.word) for word in word_list) / len(word_list) if word_list else 0
            }
        except Exception as e:
            logger.error(f"获取词长统计失败: {e}")
            raise DictError(f"获取词长统计失败: {e}")

    def get_code_stats(self) -> Dict[str, Any]:
        """获取编码统计"""
        try:
            all_words = self.repo.get_all()
            # 只统计词表数据，不包括字符和特殊字符
            word_list = [word for word in all_words if not word.is_character and not word.is_special]
            code_length_counter: Counter[int] = Counter()
            code_counter: Counter[str] = Counter()
            code_to_words: Dict[str, List[str]] = {}

            for word in word_list:
                code_length = len(word.code)
                code_length_counter[code_length] += 1
                code_counter[word.code] += 1

                # 记录编码到词条的映射
                if word.code not in code_to_words:
                    code_to_words[word.code] = []
                # 从配置中获取词条示例上限，默认为20
                example_limit = config_manager.get("stats_example_limit", 20)
                if len(code_to_words[word.code]) < example_limit:  # 只保存前 N 个示例
                    code_to_words[word.code].append(word.word)

            # 计算编码冲突
            conflicts = {code: count for code, count in code_counter.items() if count > 1}

            return {
                "total_codes": len(code_counter),
                "code_length_distribution": dict(code_length_counter),
                "conflicts": conflicts,
                "conflict_count": len(conflicts),
                "code_frequency": dict(code_counter),
                "code_to_words": code_to_words
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

    def get_stats(self) -> Dict[str, Any]:
        """获取所有统计数据"""
        try:
            return {
                "word_length_stats": self.get_word_length_stats(),
                "code_stats": self.get_code_stats(),
                "weight_stats": self.get_weight_stats()
            }
        except Exception as e:
            logger.error(f"获取统计数据失败: {e}")
            raise DictError(f"获取统计数据失败: {e}")

    def get_weight_stats(self) -> Dict[str, Any]:
        """获取权重统计"""
        try:
            all_words = self.repo.get_all()
            # 只统计词表数据，不包括字符和特殊字符
            word_list = [
                word for word in all_words
                if not word.is_character and not word.is_special
            ]
            if not word_list:
                return {
                    "total_words": 0,
                    "average_weight": 0.0,
                    "max_weight": 0.0,
                    "min_weight": 0.0,
                    "weight_distribution": {}
                }

            weights = [word.weight for word in word_list]

            # 智能划分区间：使用 Freedman-Diaconis 规则
            weight_ranges = self._compute_smart_bins(weights)

            return {
                "total_words": len(word_list),
                "average_weight": sum(weights) / len(weights),
                "max_weight": max(weights),
                "min_weight": min(weights),
                "weight_distribution": weight_ranges
            }
        except Exception as e:
            logger.error(f"获取权重统计失败: {e}")
            raise DictError(f"获取权重统计失败: {e}")

    @staticmethod
    def _compute_smart_bins(
        weights: List[float], max_bins: int = 10
    ) -> Dict[str, int]:
        """智能划分权重区间

        使用 Freedman-Diaconis 规则自动确定最优 bin 宽度，
        根据数据分布动态调整区间数量和边界。
        """
        import math

        n = len(weights)
        if n == 0:
            return {}

        w_min = min(weights)
        w_max = max(weights)

        # 数据全部相同
        if w_min == w_max:
            return {f"{w_min:.0f}": n}

        data_range = w_max - w_min

        # 使用 Freedman-Diaconis 规则计算 bin 宽度
        # IQR = Q3 - Q1
        sorted_w = sorted(weights)
        q1_idx = n // 4
        q3_idx = (3 * n) // 4
        q1 = sorted_w[q1_idx]
        q3 = sorted_w[q3_idx]
        iqr = q3 - q1

        if iqr > 0:
            # Freedman-Diaconis: bin_width = 2 * IQR * n^(-1/3)
            bin_width = 2.0 * iqr * (n ** (-1.0 / 3.0))
        else:
            # IQR=0（数据集中），退化为 Sturges 规则
            bin_width = data_range / max(
                1, math.ceil(math.log2(n) + 1)
            )

        # 确保 bin_width 合理
        if bin_width <= 0:
            bin_width = data_range / max_bins

        num_bins = max(
            2, min(max_bins, math.ceil(data_range / bin_width))
        )
        bin_width = data_range / num_bins

        # 构建区间
        ranges: Dict[str, int] = {}
        for i in range(num_bins):
            lo = w_min + i * bin_width
            hi = w_min + (i + 1) * bin_width
            # 格式化区间标签
            if bin_width >= 1:
                label = f"{lo:.0f}-{hi:.0f}"
            else:
                label = f"{lo:.1f}-{hi:.1f}"
            ranges[label] = 0

        # 填充计数
        for w in weights:
            idx = int((w - w_min) / bin_width)
            # 边界修正：最大值归入最后一个 bin
            if idx >= num_bins:
                idx = num_bins - 1
            key = list(ranges.keys())[idx]
            ranges[key] += 1

        # 移除空区间（前后连续的保留，中间的保留以维持连续性）
        keys = list(ranges.keys())
        first_nonzero = next(
            (i for i, k in enumerate(keys) if ranges[k] > 0), 0
        )
        last_nonzero = next(
            (i for i in range(len(keys) - 1, -1, -1)
             if ranges[keys[i]] > 0),
            len(keys) - 1,
        )

        trimmed = {
            k: ranges[k]
            for k in keys[first_nonzero:last_nonzero + 1]
        }
        return trimmed if trimmed else ranges

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
