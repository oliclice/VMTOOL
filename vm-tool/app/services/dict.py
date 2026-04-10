"""码表词条服务"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

from app.dal.repositories import WordRepository
from app.dal.database import get_db
from app.dal.models import Word
from app.core.errors import DictError
from app.core.cache import cache, optimize_batch_operation, performance_monitor
from app.services.code_generator import CodeGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DictService:
    """码表词条服务"""
    
    def __init__(self, db: Session = None):
        if db:
            self.db = db
        else:
            self.db = next(get_db())
        self.repo = WordRepository(self.db)
        self.code_generator = CodeGenerator()
    
    @cache.decorator()
    def get_word(self, word: str) -> Optional[Dict[str, Any]]:
        """获取单个词条"""
        try:
            db_word = self.repo.get_by_word(word)
            if db_word:
                return {
                    "word": db_word.word,
                    "code": db_word.code,
                    "weight": db_word.weight,
                    "is_active": db_word.is_active,
                    "created_at": db_word.created_at,
                    "updated_at": db_word.updated_at
                }
            return None
        except Exception as e:
            logger.error(f"获取词条失败: {e}")
            raise DictError(f"获取词条失败: {e}")
    
    @cache.decorator()
    def get_words_by_code(self, code: str) -> List[Dict[str, Any]]:
        """根据编码获取词条列表"""
        try:
            db_words = self.repo.get_by_code(code)
            return [{
                "word": word.word,
                "code": word.code,
                "weight": word.weight,
                "is_active": word.is_active
            } for word in db_words]
        except Exception as e:
            logger.error(f"根据编码获取词条失败: {e}")
            raise DictError(f"根据编码获取词条失败: {e}")
    
    @cache.decorator()
    def search_words(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索词条"""
        try:
            db_words = self.repo.search(keyword)
            return [{
                "word": word.word,
                "code": word.code,
                "weight": word.weight
            } for word in db_words]
        except Exception as e:
            logger.error(f"搜索词条失败: {e}")
            raise DictError(f"搜索词条失败: {e}")
    
    @performance_monitor
    def add_word(self, word: str, code: str = None, weight: float = 1.0, is_character: bool = None, manual: bool = False) -> Dict[str, Any]:
        """添加单个词条"""
        try:
            # 如果没有提供编码，自动生成
            if code is None:
                code = self.generate_code(word)
                manual = False  # 自动生成的编码，manual设为False
            
            # 检查是否已存在相同的word和code组合
            existing = self.repo.get_by_word_and_code(word, code)
            if existing:
                raise DictError(f"词条 '{word}' 与编码 '{code}' 的组合已存在")
            
            # 自动判断是字还是词
            if is_character is None:
                is_character = len(word) == 1
            
            db_word = self.repo.create(word, code, weight, is_character, manual)
            return {
                "word": db_word.word,
                "code": db_word.code,
                "weight": db_word.weight,
                "is_character": db_word.is_character,
                "manual": db_word.manual
            }
        except DictError:
            raise
        except Exception as e:
            logger.error(f"添加词条失败: {e}")
            raise DictError(f"添加词条失败: {e}")
    
    @optimize_batch_operation(batch_size=500)
    def add_words(self, words: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量添加词条"""
        try:
            # 过滤已存在的词条（不检查manual字段）
            valid_words = []
            existing_pairs = []
            
            for word_data in words:
                word = word_data.get("word")
                code = word_data.get("code")
                
                # 如果没有提供编码，自动生成
                if code is None:
                    code = self.generate_code(word)
                    word_data["code"] = code
                    word_data["manual"] = False  # 自动生成的编码，manual设为False
                
                # 自动判断是字还是词
                if "is_character" not in word_data:
                    word_data["is_character"] = len(word) == 1
                
                if not self.repo.get_by_word_and_code(word, code):
                    valid_words.append(word_data)
                else:
                    existing_pairs.append(f"{word}:{code}")
            
            # 批量创建
            if valid_words:
                db_words = self.repo.bulk_create(valid_words)
                
            return {
                "added": len(valid_words),
                "existing": len(existing_pairs),
                "existing_pairs": existing_pairs
            }
        except Exception as e:
            logger.error(f"批量添加词条失败: {e}")
            raise DictError(f"批量添加词条失败: {e}")
    
    def add_characters(self, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量添加字表"""
        try:
            # 为每个字添加is_character=True
            for char_data in characters:
                char_data["is_character"] = True
            
            # 调用批量添加方法
            return self.add_words(characters)
        except Exception as e:
            logger.error(f"批量添加字表失败: {e}")
            raise DictError(f"批量添加字表失败: {e}")
    
    def update_word(self, word: str, **kwargs) -> Dict[str, Any]:
        """更新词条"""
        try:
            db_word = self.repo.get_by_word(word)
            if not db_word:
                raise DictError(f"词条 '{word}' 不存在")
            
            # 如果更新编码，设置manual为True
            if "code" in kwargs:
                kwargs["manual"] = True
            
            # 更新词条
            updated = self.repo.update(db_word.id, **kwargs)
            return {
                "word": updated.word,
                "code": updated.code,
                "weight": updated.weight,
                "is_active": updated.is_active,
                "manual": updated.manual
            }
        except DictError:
            raise
        except Exception as e:
            logger.error(f"更新词条失败: {e}")
            raise DictError(f"更新词条失败: {e}")
    
    def delete_word(self, word: str) -> bool:
        """删除词条"""
        try:
            db_word = self.repo.get_by_word(word)
            if not db_word:
                raise DictError(f"词条 '{word}' 不存在")
            
            return self.repo.delete(db_word.id)
        except DictError:
            raise
        except Exception as e:
            logger.error(f"删除词条失败: {e}")
            raise DictError(f"删除词条失败: {e}")
    
    def delete_words(self, words: List[str]) -> Dict[str, Any]:
        """批量删除词条"""
        try:
            deleted = 0
            not_found = []
            
            for word in words:
                db_word = self.repo.get_by_word(word)
                if db_word:
                    self.repo.delete(db_word.id)
                    deleted += 1
                else:
                    not_found.append(word)
            
            return {
                "deleted": deleted,
                "not_found": len(not_found),
                "not_found_words": not_found
            }
        except Exception as e:
            logger.error(f"批量删除词条失败: {e}")
            raise DictError(f"批量删除词条失败: {e}")
    
    def generate_code(self, word: str) -> str:
        """生成编码"""
        return self.code_generator.generate_code(word)
    
    def replace_code(self, word: str, new_code: str) -> Dict[str, Any]:
        """替换编码"""
        try:
            return self.update_word(word, code=new_code)
        except Exception as e:
            logger.error(f"替换编码失败: {e}")
            raise DictError(f"替换编码失败: {e}")
    
    def get_all_words(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有词条"""
        try:
            db_words = self.repo.get_all(skip, limit)
            return [{
                "word": word.word,
                "code": word.code,
                "weight": word.weight,
                "manual": word.manual
            } for word in db_words]
        except Exception as e:
            logger.error(f"获取所有词条失败: {e}")
            raise DictError(f"获取所有词条失败: {e}")
    
    def calculate_all_codes(self) -> Dict[str, Any]:
        """计算所有未手动修改过编码的词条的编码"""
        try:
            # 获取所有未手动修改过编码的词条
            db_words = self.db.query(Word).filter(Word.manual == False).all()
            
            updated = 0
            failed = 0
            
            for db_word in db_words:
                try:
                    # 生成新编码
                    new_code = self.generate_code(db_word.word)
                    if new_code:
                        # 更新编码，不设置manual为True，因为这是自动计算的
                        db_word.code = new_code
                        updated += 1
                except Exception as e:
                    logger.error(f"计算词条 '{db_word.word}' 的编码失败: {e}")
                    failed += 1
            
            # 提交更改
            self.db.commit()
            
            return {
                "total": len(db_words),
                "updated": updated,
                "failed": failed
            }
        except Exception as e:
            logger.error(f"批量计算编码失败: {e}")
            raise DictError(f"批量计算编码失败: {e}")
