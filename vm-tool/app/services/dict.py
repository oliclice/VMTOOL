"""码表词条服务"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

from app.dal.repositories import WordRepository
from app.dal.database import get_db
from app.core.errors import DictError
from app.core.cache import cache, optimize_batch_operation, performance_monitor

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
    def add_word(self, word: str, code: str, weight: float = 1.0) -> Dict[str, Any]:
        """添加单个词条"""
        try:
            # 检查是否已存在
            existing = self.repo.get_by_word(word)
            if existing:
                raise DictError(f"词条 '{word}' 已存在")
            
            db_word = self.repo.create(word, code, weight)
            return {
                "word": db_word.word,
                "code": db_word.code,
                "weight": db_word.weight
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
            # 过滤已存在的词条
            valid_words = []
            existing_words = []
            
            for word_data in words:
                if not self.repo.get_by_word(word_data.get("word")):
                    valid_words.append(word_data)
                else:
                    existing_words.append(word_data.get("word"))
            
            # 批量创建
            if valid_words:
                db_words = self.repo.bulk_create(valid_words)
                
            return {
                "added": len(valid_words),
                "existing": len(existing_words),
                "existing_words": existing_words
            }
        except Exception as e:
            logger.error(f"批量添加词条失败: {e}")
            raise DictError(f"批量添加词条失败: {e}")
    
    def update_word(self, word: str, **kwargs) -> Dict[str, Any]:
        """更新词条"""
        try:
            db_word = self.repo.get_by_word(word)
            if not db_word:
                raise DictError(f"词条 '{word}' 不存在")
            
            # 更新词条
            updated = self.repo.update(db_word.id, **kwargs)
            return {
                "word": updated.word,
                "code": updated.code,
                "weight": updated.weight,
                "is_active": updated.is_active
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
        # 这里需要根据具体的编码规则实现
        # 暂时返回一个简单的示例
        return "".join([str(ord(c) % 26 + 97) for c in word])[:4]
    
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
                "weight": word.weight
            } for word in db_words]
        except Exception as e:
            logger.error(f"获取所有词条失败: {e}")
            raise DictError(f"获取所有词条失败: {e}")
