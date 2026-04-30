from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.dal.models import Word, DictConfig


class BaseRepository:
    """仓库基类"""
    
    def __init__(self, db: Session):
        self.db = db


class WordRepository(BaseRepository):
    """词库仓库"""
    
    def create(self, word: str, code: str, weight: float = 1.0, is_character: bool = False, is_special: bool = False, manual: bool = False) -> Word:
        """创建词条"""
        db_word = Word(word=word, code=code, weight=weight, is_character=is_character, is_special=is_special, manual=manual)
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
    
    def get_by_word_code_pairs(self, word_code_pairs: List[tuple]) -> List[tuple]:
        """批量根据词和编码获取词条"""
        if not word_code_pairs:
            return []
        
        existing_words = []
        # 分批次查询，每批处理100个，避免SQL语句过长
        batch_size = 100
        for i in range(0, len(word_code_pairs), batch_size):
            batch = word_code_pairs[i:i+batch_size]
            # 使用 in_ 子句批量查询
            batch_existing = self.db.query(Word.word, Word.code).filter(
                or_(*[and_(Word.word == word, Word.code == code) for word, code in batch])
            ).all()
            existing_words.extend(batch_existing)
        
        return existing_words
    
    def get_by_code(self, code: str) -> List[Word]:
        """根据编码获取词条列表"""
        return self.db.query(Word).filter(Word.code == code).all()
    
    def get_all(self, skip: int = 0, limit: int = None) -> List[Word]:
        """获取所有词条"""
        query = self.db.query(Word).offset(skip)
        if limit is not None:
            query = query.limit(limit)
        return query.all()
    
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
        # 使用bulk_insert_mappings进行更高效的批量插入
        # 每批处理5000条记录，减少数据库提交次数
        batch_size = 5000
        total = len(words)
        
        # 分批次处理
        for i in range(0, total, batch_size):
            batch = words[i:i+batch_size]
            # 使用bulk_insert_mappings进行批量插入
            self.db.bulk_insert_mappings(Word, batch)
            # 每批次提交一次
            self.db.commit()
        
        # 由于bulk_insert_mappings不返回对象，我们返回空列表
        # 如果需要返回对象，需要在插入后查询
        return []
    
    def search(self, keyword: str, field: str = "word") -> List[Word]:
        """搜索词条"""
        if field == "word":
            return self.db.query(Word).filter(Word.word.contains(keyword)).all()
        elif field == "code":
            return self.db.query(Word).filter(Word.code.contains(keyword)).all()
        elif field == "weight":
            try:
                weight = float(keyword)
                return self.db.query(Word).filter(Word.weight == weight).all()
            except ValueError:
                return []
        elif field == "manual":
            if keyword.lower() in ["是", "true", "1"]:
                return self.db.query(Word).filter(Word.manual == True).all()
            elif keyword.lower() in ["否", "false", "0"]:
                return self.db.query(Word).filter(Word.manual == False).all()
            else:
                return []
        else:
            return self.db.query(Word).filter(Word.word.contains(keyword)).all()
    
    def get_special_chars(self, skip: int = 0, limit: int = None) -> List[Word]:
        """获取所有特殊字符"""
        query = self.db.query(Word).filter(Word.is_special == True).offset(skip)
        if limit is not None:
            query = query.limit(limit)
        result = query.all()
        return result
    
    def count_special_chars(self) -> int:
        """统计特殊字符数量"""
        return self.db.query(Word).filter(Word.is_special == True).count()
    
    def get_characters(self, skip: int = 0, limit: int = None) -> List[Word]:
        """获取所有字"""
        query = self.db.query(Word).filter(Word.is_character == True).offset(skip)
        if limit is not None:
            query = query.limit(limit)
        result = query.all()
        return result
    
    def get_words(self, skip: int = 0, limit: int = None) -> List[Word]:
        """获取所有词"""
        query = self.db.query(Word).filter(Word.is_character == False, Word.is_special == False).offset(skip)
        if limit is not None:
            query = query.limit(limit)
        result = query.all()
        return result

    def get_all_by_type(self, table_type: str, skip: int = 0, limit: int = None) -> List[Word]:
        """根据表类型获取所有词条"""
        query = self.db.query(Word)
        if table_type == "chars":
            query = query.filter(Word.is_character == True)
        elif table_type == "words":
            query = query.filter(Word.is_character == False, Word.is_special == False)
        elif table_type == "special":
            query = query.filter(Word.is_special == True)
        query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def count_by_type(self, table_type: str) -> int:
        """根据表类型统计数量"""
        query = self.db.query(Word)
        if table_type == "chars":
            query = query.filter(Word.is_character == True)
        elif table_type == "words":
            query = query.filter(Word.is_character == False, Word.is_special == False)
        elif table_type == "special":
            query = query.filter(Word.is_special == True)
        return query.count()

    def bulk_delete(self, word_ids: List[int]) -> int:
        """批量删除词条"""
        if not word_ids:
            return 0
        deleted = self.db.query(Word).filter(Word.id.in_(word_ids)).delete(synchronize_session=False)
        self.db.commit()
        return deleted


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
