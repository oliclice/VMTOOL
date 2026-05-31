"""词频数据加载服务"""
import math
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# 模块级缓存，避免重复加载
_freq_cache: Optional[Dict[str, int]] = None
_data_dir: Optional[str] = None


def load_thuocl_data(data_dir: str) -> Dict[str, int]:
    """加载词频数据

    优先加载 xiandaihaiyuchangyongcibiao.txt（三列格式：词\t拼音\t词频），
    再加载 THUOCL_*.txt 文件（两列格式：词\t词频）作为补充。
    返回 {word: frequency} 字典。
    """
    global _freq_cache, _data_dir

    # 如果已加载且目录未变，直接返回缓存
    if _freq_cache is not None and _data_dir == data_dir:
        return _freq_cache

    freq_dict: Dict[str, int] = {}

    if not os.path.isdir(data_dir):
        logger.warning(f"词频数据目录不存在: {data_dir}")
        _freq_cache = freq_dict
        _data_dir = data_dir
        return freq_dict

    # 1. 优先加载 xiandaihaiyuchangyongcibiao.txt
    priority_file = os.path.join(data_dir, "xiandaihaiyuchangyongcibiao.txt")
    if os.path.isfile(priority_file):
        try:
            with open(priority_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        word = parts[0].strip()
                        try:
                            freq = int(parts[2].strip())
                            freq_dict[word] = freq
                        except ValueError:
                            continue
            logger.info(f"已加载 xiandaihaiyuchangyongcibiao.txt: {len(freq_dict)} 条")
        except Exception as e:
            logger.error(f"加载 xiandaihaiyuchangyongcibiao.txt 失败: {e}")

    # 2. 补充加载 THUOCL_*.txt 文件
    for filename in os.listdir(data_dir):
        if not filename.startswith("THUOCL_") or not filename.endswith(".txt"):
            continue
        filepath = os.path.join(data_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        word = parts[0].strip()
                        if word in freq_dict:
                            continue  # 已存在，跳过
                        try:
                            freq = int(parts[1].strip())
                            freq_dict[word] = freq
                        except ValueError:
                            continue
        except Exception as e:
            logger.error(f"加载 THUOCL 文件失败 {filename}: {e}")

    logger.info(f"已加载词频数据: {len(freq_dict)} 条")
    _freq_cache = freq_dict
    _data_dir = data_dir
    return freq_dict


def get_log_weight(word: str, freq_dict: Dict[str, int]) -> float:
    """获取词的对数权重: log10(词频)

    若词不在词频表中，返回 0.0（即 log10(1)）。
    """
    freq = freq_dict.get(word, 0)
    if freq <= 0:
        return 0.0
    return math.log10(freq)


def clear_cache():
    """清除缓存（用于测试或重新加载）"""
    global _freq_cache, _data_dir
    _freq_cache = None
    _data_dir = None
