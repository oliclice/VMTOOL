from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from sqlalchemy.sql import func

from app.dal.database import Base


class Word(Base):
    """码表词条模型"""
    __tablename__ = "words"
    
    id = Column(Integer, primary_key=True)  # 主键默认有索引
    word = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    weight = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    is_character = Column(Boolean, default=False)  # 是否为单个字符（字）
    is_special = Column(Boolean, default=False)  # 是否为特殊字符（非汉字、emoji等）
    manual = Column(Boolean, default=False)  # 是否手动修改过编码
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Word(word='{self.word}', code='{self.code}', weight={self.weight})>"


class DictConfig(Base):
    """码表配置模型"""
    __tablename__ = "dict_configs"
    
    id = Column(Integer, primary_key=True)  # 主键默认有索引
    key = Column(String(100), unique=True, nullable=False)  # unique约束会自动创建索引
    value = Column(Text)
    description = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<DictConfig(key='{self.key}', value='{self.value}')>"
