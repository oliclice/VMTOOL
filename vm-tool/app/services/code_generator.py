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
                # 自定义规则，可以在这里扩展
                code = self.config['separator'].join(char_codes)
            else:
                # 默认规则
                code = self.config['separator'].join([c[0] for c in char_codes])
            
            # 限制编码长度
            return code[:self.config['max_length']]
        except Exception as e:
            logger.error(f"根据字表生成编码失败: {e}")
            return ""
    
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
