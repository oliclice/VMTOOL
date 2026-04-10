from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.dal.models import Word, DictConfig


class BaseRepository:
    """仓库基类"""
    
    def __init__(self, db: Session):
        self.db = db


class WordRepository(BaseRepository):
    """词库仓库"""
    
    def create(self, word: str, code: str, weight: float = 1.0, manual: bool = False) -> Word:
        """创建词条"""
        db_word = Word(word=word, code=code, weight=weight, manual=manual)
        self.db.add(db_word)
        self.db.commit()
        self.db.refresh(db_word)
        return db_word
    
    def get_by_word(self, word: str) -> Optional[Word]:
        """根据词获取词条"""
        return self.db.query(Word).filter(Word.word == word).first()
    
    def get_by_word_and_code(self, word: str, code: str) -> Optional[Word]:
        """根据词和编码获取词条"""
        return self.db.query(Word).filter(Word.word == word, Word.code == code).first()
    
    def get_by_code(self, code: str) -> List[Word]:
        """根据编码获取词条列表"""
        return self.db.query(Word).filter(Word.code == code).all()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Word]:
        """获取所有词条"""
        return self.db.query(Word).offset(skip).limit(limit).all()
    
    def update(self, word_id: int, **kwargs) -> Optional[Word]:
        """更新词条"""
        db_word = self.db.query(Word).filter(Word.id == word_id).first()
        if db_word:
            for key, value in kwargs.items():
                setattr(db_word, key, value)
            self.db.commit()
            self.db.refresh(db_word)
        return db_word
    
    def delete(self, word_id: int) -> bool:
        """删除词条"""
        db_word = self.db.query(Word).filter(Word.id == word_id).first()
        if db_word:
            self.db.delete(db_word)
            self.db.commit()
            return True
        return False
    
    def bulk_create(self, words: List[Dict[str, Any]]) -> List[Word]:
        """批量创建词条"""
        db_words = [Word(**word) for word in words]
        self.db.add_all(db_words)
        self.db.commit()
        for word in db_words:
            self.db.refresh(word)
        return db_words
    
    def search(self, keyword: str) -> List[Word]:
        """搜索词条"""
        return self.db.query(Word).filter(Word.word.contains(keyword)).all()


class DictConfigRepository(BaseRepository):
    """码表配置仓库"""
    
    def create(self, key: str, value: str, description: Optional[str] = None) -> DictConfig:
        """创建配置"""
        db_config = DictConfig(key=key, value=value, description=description)
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        return db_config
    
    def get_by_key(self, key: str) -> Optional[DictConfig]:
        """根据键获取配置"""
        return self.db.query(DictConfig).filter(DictConfig.key == key).first()
    
    def get_all(self) -> List[DictConfig]:
        """获取所有配置"""
        return self.db.query(DictConfig).all()
    
    def update(self, key: str, value: str) -> Optional[DictConfig]:
        """更新配置"""
        db_config = self.db.query(DictConfig).filter(DictConfig.key == key).first()
        if db_config:
            db_config.value = value
            self.db.commit()
            self.db.refresh(db_config)
        return db_config
    
    def delete(self, key: str) -> bool:
        """删除配置"""
        db_config = self.db.query(DictConfig).filter(DictConfig.key == key).first()
        if db_config:
            self.db.delete(db_config)
            self.db.commit()
            return True
        return False
