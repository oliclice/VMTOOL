from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config_manager import config_manager

# 创建数据库引擎
database_path = config_manager.get("database_path")
engine = create_engine(
    f"sqlite:///{database_path}",
    connect_args={
        "check_same_thread": False,  # SQLite 特定配置，允许跨线程访问
        "timeout": 30  # 增加超时时间，避免并发访问冲突
    },
    poolclass=StaticPool,  # SQLite 使用静态连接池
    pool_pre_ping=True  # 连接前检查连接是否有效
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
