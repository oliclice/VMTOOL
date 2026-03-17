#!/usr/bin/env python3
"""权重计算模块"""
from typing import Dict


class WeightCalculator:
    """权重计算器"""
    
    def calculate_all(self, data: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, int]]:
        """计算所有词的权重"""
        for word in data:
            data[word]['weight'] = max(data[word]['weight'], 1)
        return data
    
    def update_word_weight(self, data: Dict[str, Dict[str, int]], word: str) -> Dict[str, Dict[str, int]]:
        """更新指定词的权重"""
        if word not in data:
            print(f'{word} 不在数据中')
            return data
        
        aim_key = data[word]['key']
        same_key_words = {w: data[w] for w in data if data[w]['key'] == aim_key}
        
        # 提升目标词权重
        same_key_words[word]['weight'] += 1.5
        
        # 重新分配权重（阶梯化）
        weights = sorted(info['weight'] for info in same_key_words.values())
        for w in same_key_words:
            old_weight = same_key_words[w]['weight']
            new_weight = weights.index(old_weight) + 1
            weights[weights.index(old_weight)] = 0
            same_key_words[w]['weight'] = new_weight
            data[w]['weight'] = new_weight
        
        # 输出结果
        for w in sorted(same_key_words, key=lambda x: -same_key_words[x]['weight']):
            print(f'{w}: {same_key_words[w]}')
        
        return data
    
    def set_weight_directly(self, data: Dict[str, Dict[str, int]], word: str, value: str) -> Dict[str, Dict[str, int]]:
        """直接设置权重值"""
        if word not in data:
            print(f'词 "{word}" 不在数据中')
            return data
        
        try:
            new_weight = float(value)
        except ValueError:
            print(f'错误: 权重值必须是数字，输入值为 "{value}"')
            return data
        
        old_weight = data[word]['weight']
        
        # 找到所有同码词
        aim_key = data[word]['key']
        same_key_words = {w: data[w].copy() for w in data if data[w]['key'] == aim_key}
        
        # 处理增量或直接设置
        if isinstance(value, str) and value.startswith(('-', '+')):
            same_key_words[word]['weight'] = float(value)
            
            all_weights = sorted(info['weight'] for info in same_key_words.values())
            for w in same_key_words:
                old = same_key_words[w]['weight']
                new_weight = all_weights.index(old) + 1
                all_weights[all_weights.index(old)] = 0
                same_key_words[w]['weight'] = new_weight
                data[w]['weight'] = new_weight
        else:
            data[word]['weight'] = int(new_weight)
            print(f'{word}: 权重从 {old_weight} 更新为 {int(new_weight)}')
        
        for w in sorted(same_key_words, key=lambda x: -same_key_words[x]['weight']):
            print(f'{w}: {same_key_words[w]}')
        
        return data
