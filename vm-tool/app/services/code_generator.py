"""编码生成服务"""
from typing import Optional, Dict, List
import logging

from app.dal.repositories import WordRepository
from app.dal.database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeGenerator:
    """编码生成器"""
    
    def __init__(self):
        """初始化编码生成器"""
        self.db = next(get_db())
        self.repo = WordRepository(self.db)
        self.config = {
            'rule': 'first_letter',  # first_letter, all_letters, custom
            'separator': '',  # 编码分隔符
            'max_length': 4  # 最大编码长度
        }
    
    def set_config(self, config: Dict[str, any]):
        """设置编码生成配置
        
        Args:
            config: 配置字典
        """
        self.config.update(config)
    
    def get_config(self) -> Dict[str, any]:
        """获取编码生成配置
        
        Returns:
            配置字典
        """
        return self.config
    
    def generate_code(self, word: str) -> str:
        """生成编码
        
        Args:
            word: 词条
            
        Returns:
            生成的编码
        """
        try:
            # 尝试根据字表中的字的编码计算
            code = self.generate_code_from_chars(word)
            if code:
                return code
            
            # 如果字表中没有对应的字，使用默认方法
            # 对于单个字符，生成多个字符的编码，避免编码长度为1
            if len(word) == 1:
                # 为单个字符生成更长的编码
                char = word[0]
                # 使用字符的ASCII码生成多个字符的编码
                code = "".join([chr((ord(char) + i) % 26 + 97) for i in range(self.config['max_length'])])
                return code
            else:
                # 对于词语，使用原方法
                return "".join([chr(ord(c) % 26 + 97) for c in word])[:self.config['max_length']]
        except Exception as e:
            logger.error(f"生成编码失败: {e}")
            return ""
    
    def generate_code_from_chars(self, word: str) -> str:
        """根据字表中的字的编码计算词的编码
        
        Args:
            word: 词条
            
        Returns:
            生成的编码
        """
        try:
            char_codes = []
            
            # 获取每个字的编码
            for char in word:
                char_word = self.repo.get_by_word(char)
                if char_word:
                    char_codes.append(char_word.code)
                else:
                    # 如果字表中没有这个字，返回空
                    return ""
            
            # 根据配置的规则生成编码
            if self.config['rule'] == 'first_letter':
                # 取每个字编码的第一个字符
                code = self.config['separator'].join([c[0] for c in char_codes])
            elif self.config['rule'] == 'all_letters':
                # 拼接所有字的编码
                code = self.config['separator'].join(char_codes)
            elif self.config['rule'] == 'custom':
                # 自定义规则
                code = self._execute_custom_rule(word, char_codes)
            else:
                # 默认规则
                code = self.config['separator'].join([c[0] for c in char_codes])
            
            # 限制编码长度
            return code[:self.config['max_length']]
        except Exception as e:
            logger.error(f"根据字表生成编码失败: {e}")
            return ""
    
    def _execute_custom_rule(self, word: str, char_codes: List[str]) -> str:
        """执行自定义编码规则
        
        Args:
            word: 词条
            char_codes: 每个字的编码列表
            
        Returns:
            生成的编码
        """
        try:
            # 读取自定义规则配置
            from app.core.config_manager import config_manager
            current_rule = config_manager.get("code_rule", "默认规则")
            custom_rules = config_manager.get("custom_rules", {})
            
            # 获取当前规则的内容
            custom_rule_content = custom_rules.get(current_rule, "")
            
            if not custom_rule_content:
                # 如果没有自定义规则，使用默认规则
                return self.config['separator'].join([c[0] for c in char_codes])
            
            word_length = len(word)
            
            # 解析规则
            rules = {}
            plus_rules = {}
            for line in custom_rule_content.strip().split('\n'):
                line = line.strip()
                if line and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 提取长度
                    if key.startswith('v[') and key.endswith(']'):
                        length_str = key[2:-1]
                        # 处理v[4+]格式的规则
                        if length_str.endswith('+'):
                            try:
                                min_length = int(length_str[:-1])
                                plus_rules[min_length] = value
                            except:
                                pass
                        else:
                            try:
                                length = int(length_str)
                                rules[length] = value
                            except:
                                pass
            
            # 找到匹配的规则
            rule = None
            if word_length in rules:
                rule = rules[word_length]
            else:
                # 检查是否匹配v[4+]格式的规则
                for min_length, rule_content in plus_rules.items():
                    if word_length >= min_length:
                        rule = rule_content
                        break
            
            if rule:
                # 替换s[i][j]为实际编码
                result = rule
                
                # 处理s[i][j]表示第i+1个字的第j个编码字符（Python风格索引）
                for i in range(word_length):
                    for j in range(len(char_codes[i])):
                        # Python风格索引（从0开始）
                        placeholder = f"s[{i}][{j+1}]"
                        if placeholder in result:
                            result = result.replace(placeholder, char_codes[i][j])
                        
                        # 兼容旧的1-based索引
                        old_placeholder = f"s[{i+1}][{j+1}]"
                        if old_placeholder in result:
                            result = result.replace(old_placeholder, char_codes[i][j])
                
                # 处理s[-1][j]表示最后一个字的编码
                if word_length > 0:
                    last_index = word_length - 1
                    for j in range(len(char_codes[last_index])):
                        placeholder = f"s[-1][{j+1}]"
                        if placeholder in result:
                            result = result.replace(placeholder, char_codes[last_index][j])
                
                # 处理连接符（移除+号）
                result = result.replace('+', '')
                # 移除所有空格
                result = result.replace(' ', '')
                
                # 确保所有占位符都被替换
                import re
                # 查找所有未被替换的s[i][j]格式的占位符
                placeholders = re.findall(r's\[\d+\]\[\d+\]|s\[-1\]\[\d+\]', result)
                for placeholder in placeholders:
                    # 移除未被替换的占位符
                    result = result.replace(placeholder, '')
                
                return result
            else:
                # 如果没有匹配的规则，使用默认规则
                return self.config['separator'].join([c[0] for c in char_codes])
        except Exception as e:
            logger.error(f"执行自定义规则失败: {e}")
            # 失败时使用默认规则
            return self.config['separator'].join([c[0] for c in char_codes])
    
    def validate_code(self, code: str) -> bool:
        """验证编码
        
        Args:
            code: 编码
            
        Returns:
            是否有效
        """
        try:
            # 简单的编码验证逻辑
            return isinstance(code, str) and len(code) > 0
        except Exception as e:
            logger.error(f"验证编码失败: {e}")
            return False
