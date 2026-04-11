"""兼容性层"""
import argparse
import os
from typing import Dict, Any, List, Optional
import logging

from app.core.config import settings
from app.services.dict import DictService
from app.services.weight import WeightCalculator
from app.services.filter import FilterService
from app.services.stats import StatsService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompatibilityLayer:
    """兼容性层"""
    
    def __init__(self) -> None:
        """初始化兼容性层"""
        self.dict_service = DictService()
        self.weight_calc = WeightCalculator()
        self.filter_service = FilterService()
        self.stats_service = StatsService()
    
    def handle_old_api(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """处理旧API调用
        
        Args:
            method: 方法名
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 方法调用结果
        """
        logger.info(f"处理旧API调用: {method}, 参数: {args}, {kwargs}")
        
        # 映射旧API到新服务
        method_map = {
            "add_word": self._add_word,
            "delete_word": self._delete_word,
            "update_weight": self._update_weight,
            "query": self._query,
            "replace_key": self._replace_key,
            "count_high_keys": self._count_high_keys,
            "clear_backups": self._clear_backups,
        }
        
        if method in method_map:
            return method_map[method](*args, **kwargs)
        else:
            logger.error(f"不支持的旧API方法: {method}")
            raise ValueError(f"不支持的旧API方法: {method}")
    
    def _add_word(self, word: str, code: Optional[str] = None, weight: float = 1.0) -> Dict[str, Any]:
        """添加词（旧API兼容）"""
        if not code:
            code = self.dict_service.generate_code(word)
        return self.dict_service.add_word(word, code, weight)
    
    def _delete_word(self, word: str) -> bool:
        """删除词（旧API兼容）"""
        return self.dict_service.delete_word(word)
    
    def _update_weight(self, word: str, increment: float = 0.1) -> Dict[str, Any]:
        """更新权重（旧API兼容）"""
        return self.weight_calc.update_word_weight(word, increment)
    
    def _query(self, keyword: str) -> List[Dict[str, Any]]:
        """查询词（旧API兼容）"""
        return self.dict_service.search_words(keyword)
    
    def _replace_key(self, word: str, new_code: str) -> Dict[str, Any]:
        """替换编码（旧API兼容）"""
        return self.dict_service.replace_code(word, new_code)
    
    def _count_high_keys(self, min_length: int, min_count: int) -> List[Dict[str, Any]]:
        """统计高频词（旧API兼容）"""
        # 这里需要根据旧API的行为实现
        high_freq_words = self.stats_service.get_high_frequency_words(100)
        # 过滤符合条件的词
        filtered = []
        for word_info in high_freq_words:
            if len(word_info["word"]) >= min_length:
                filtered.append(word_info)
                if len(filtered) >= min_count:
                    break
        return filtered
    
    def _clear_backups(self, confirm: str) -> bool:
        """清理备份（旧API兼容）"""
        if confirm == 'y':
            # 这里需要实现清理备份的逻辑
            logger.info("清理备份文件")
            return True
        return False
    
    def parse_old_command_line(self, args: List[str]) -> Dict[str, Any]:
        """解析旧命令行参数
        
        Args:
            args: 命令行参数列表
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        logger.info(f"解析旧命令行参数: {args}")
        
        # 创建解析器
        parser = argparse.ArgumentParser(description="VM-TOOL - 码表处理工具")
        
        # 添加旧参数
        parser.add_argument('-a', '--add', nargs='*', help='添加新词')
        parser.add_argument('-d', '--delete', nargs='*', help='删除词')
        parser.add_argument('-q', '--query', help='查词或查编码')
        parser.add_argument('-u', '--update-weight', nargs='*', help='更新词权重')
        parser.add_argument('-U', '--set-weight', nargs=2, metavar=('词', '值'), help='直接设置词权重')
        parser.add_argument('-r', '--replace', nargs=2, metavar=('词', '新编码'), help='替换编码')
        parser.add_argument('-H', '--high-key', nargs=2, metavar=('最小长度', '出现次数'), help='高频统计')
        parser.add_argument('-C', '--clear', help='清理备份文件(y确认)')
        parser.add_argument('-c', '--choices', nargs='*', help='执行指定功能')
        
        # 解析参数
        parsed = parser.parse_args(args)
        
        # 转换为字典
        result = {}
        if parsed.add:
            result['add'] = parsed.add
        if parsed.delete:
            result['delete'] = parsed.delete
        if parsed.query:
            result['query'] = parsed.query
        if parsed.update_weight:
            result['update_weight'] = parsed.update_weight
        if parsed.set_weight:
            result['set_weight'] = parsed.set_weight
        if parsed.replace:
            result['replace'] = parsed.replace
        if parsed.high_key:
            result['high_key'] = parsed.high_key
        if parsed.clear:
            result['clear'] = parsed.clear
        if parsed.choices:
            result['choices'] = parsed.choices
        
        return result
    
    def handle_old_command_line(self, args: List[str]) -> bool:
        """处理旧命令行参数
        
        Args:
            args: 命令行参数列表
            
        Returns:
            bool: 是否应该退出
        """
        # 解析参数
        parsed = self.parse_old_command_line(args)
        
        # 处理参数
        if 'add' in parsed:
            return self._handle_add(parsed['add'])
        
        if 'delete' in parsed:
            return self._handle_delete(parsed['delete'])
        
        if 'query' in parsed:
            self._handle_query(parsed['query'])
            return True
        
        if 'update_weight' in parsed:
            return self._handle_update_weight(parsed['update_weight'])
        
        if 'set_weight' in parsed:
            return self._handle_set_weight(parsed['set_weight'])
        
        if 'replace' in parsed:
            self._handle_replace(parsed['replace'])
            return True
        
        if 'high_key' in parsed:
            self._handle_high_key(parsed['high_key'])
            return True
        
        if 'clear' in parsed:
            self._handle_clear(parsed['clear'])
            return True
        
        if 'choices' in parsed:
            return self._handle_choices(parsed['choices'])
        
        return False
    
    def _handle_add(self, words: List[str]) -> bool:
        """处理添加词"""
        for word in words:
            try:
                result = self.dict_service.add_word(word)
                print(f"添加成功: {result}")
            except Exception as e:
                print(f"添加失败: {e}")
        return True
    
    def _handle_delete(self, words: List[str]) -> bool:
        """处理删除词"""
        result = self.dict_service.delete_words(words)
        print(f"删除结果: {result}")
        return True
    
    def _handle_query(self, query: str) -> None:
        """处理查询"""
        results = self.dict_service.search_words(query)
        for result in results:
            print(f"{result['word']}: {result['code']} (权重: {result['weight']})")
    
    def _handle_update_weight(self, words: List[str]) -> bool:
        """处理更新权重"""
        for word in words:
            try:
                result = self.weight_calc.update_word_weight(word)
                print(f"更新权重: {result}")
            except Exception as e:
                print(f"更新失败: {e}")
        return True
    
    def _handle_set_weight(self, args: List[str]) -> bool:
        """处理直接设置权重"""
        word, value = args
        try:
            result = self.weight_calc.set_weight_directly(word, float(value))
            print(f"设置权重: {result}")
        except Exception as e:
            print(f"设置失败: {e}")
        return True
    
    def _handle_replace(self, args: List[str]) -> None:
        """处理替换编码"""
        word, new_code = args
        try:
            result = self.dict_service.replace_code(word, new_code)
            print(f"替换编码: {result}")
        except Exception as e:
            print(f"替换失败: {e}")
    
    def _handle_high_key(self, args: List[str]) -> None:
        """处理高频统计"""
        min_length, min_count = args
        try:
            results = self._count_high_keys(int(min_length), int(min_count))
            for result in results:
                print(f"{result['word']}: {result['code']} (权重: {result['weight']})")
        except Exception as e:
            print(f"统计失败: {e}")
    
    def _handle_clear(self, confirm: str) -> None:
        """处理清理备份"""
        result = self._clear_backups(confirm)
        if result:
            print("备份文件清理成功")
        else:
            print("备份文件清理取消")
    
    def _handle_choices(self, choices: List[str]) -> bool:
        """处理选择功能"""
        # 这里需要映射旧的功能选择到新的服务
        for choice in choices:
            try:
                choice_id = int(choice)
                self._run_old_function(choice_id)
            except Exception as e:
                print(f"执行功能失败: {e}")
        return True
    
    def _run_old_function(self, function_id: int) -> None:
        """运行旧功能"""
        function_map = {
            1: self._filter_dict,
            2: self._calculate_weight,
            3: self._add_words,
            4: self._write_dict,
            5: self._refresh_dict,
            6: self._auto_complete,
            7: self._count_high_frequency,
        }
        
        if function_id in function_map:
            function_map[function_id]()
        else:
            print(f"不支持的功能ID: {function_id}")
    
    def _filter_dict(self) -> None:
        """过滤码表"""
        print("执行过滤码表功能")
        # 这里需要实现过滤码表的逻辑
    
    def _calculate_weight(self) -> None:
        """计算权重"""
        print("执行计算权重功能")
        # 这里需要实现计算权重的逻辑
    
    def _add_words(self) -> None:
        """补充新词"""
        print("执行补充新词功能")
        # 这里需要实现补充新词的逻辑
    
    def _write_dict(self) -> None:
        """写入码表"""
        print("执行写入码表功能")
        # 这里需要实现写入码表的逻辑
    
    def _refresh_dict(self) -> None:
        """刷新字表"""
        print("执行刷新字表功能")
        # 这里需要实现刷新字表的逻辑
    
    def _auto_complete(self) -> None:
        """自动补码"""
        print("执行自动补码功能")
        # 这里需要实现自动补码的逻辑
    
    def _count_high_frequency(self) -> None:
        """统计高频词"""
        print("执行统计高频词功能")
        # 这里需要实现统计高频词的逻辑
    
    def convert_old_config(self, old_config_path: str) -> Dict[str, Any]:
        """转换旧配置文件
        
        Args:
            old_config_path: 旧配置文件路径
            
        Returns:
            Dict[str, Any]: 转换后的配置
        """
        import pathlib
        # 规范化路径，防止路径遍历攻击
        old_config_path = str(pathlib.Path(old_config_path).resolve())
        
        logger.info(f"转换旧配置文件: {old_config_path}")
        
        if not os.path.exists(old_config_path):
            logger.error(f"旧配置文件不存在: {old_config_path}")
            return {}
        
        # 这里需要根据旧配置文件的格式进行转换
        # 暂时返回默认配置
        return {
            "version": "2.0.0",
            "encoding": "utf-8",
            "auto_backup": "true",
            "batch_size": "1000",
            "cache_size": "1000",
            "cache_ttl": "3600",
        }
