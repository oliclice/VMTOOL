"""数据库初始化脚本"""
import logging
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.dal.database import engine, Base
from app.dal.models import Word, DictConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库"""
    try:
        logger.info("开始创建数据库表结构...")
        # 只创建不存在的表，不删除现有表
        # 注释掉删除表的代码，保持数据库数据
        # Base.metadata.drop_all(bind=engine)
        # 创建所有表（不包含索引，索引将在数据导入后创建）
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表结构创建成功")
        
        # 插入初始配置
        from sqlalchemy.orm import Session
        from app.dal.database import SessionLocal
        
        db = SessionLocal()
        try:
            # 检查是否已有配置
            if db.query(DictConfig).count() == 0:
                # 插入默认配置
                default_configs = [
                    DictConfig(key="version", value="2.0.0", description="当前版本"),
                    DictConfig(key="encoding", value="utf-8", description="默认编码"),
                    DictConfig(key="auto_backup", value="true", description="自动备份"),
                ]
                db.add_all(default_configs)
                db.commit()
                logger.info("初始配置插入成功")
            else:
                logger.info("配置已存在，跳过初始配置")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def create_indexes():
    """创建数据库索引"""
    try:
        logger.info("开始创建数据库索引...")
        # 使用原始SQL创建索引
        from sqlalchemy import text
        with engine.connect() as conn:
            # 为words表创建索引
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_words_word ON words (word)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_words_code ON words (code)"))
            # 创建 (word, code) 复合索引，加速 get_by_word_and_code 查询
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_words_word_code ON words (word, code)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_words_is_active ON words (is_active)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_words_is_character ON words (is_character)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_words_is_special ON words (is_special)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_words_manual ON words (manual)"))
            # 提交事务
            conn.commit()
        logger.info("数据库索引创建成功")
    except Exception as e:
        logger.error(f"创建数据库索引失败: {e}")
        raise


def optimize_database():
    """优化数据库"""
    try:
        logger.info("开始优化数据库...")
        # 使用原始SQL执行VACUUM和PRAGMA optimize
        from sqlalchemy import text
        with engine.connect() as conn:
            # 执行PRAGMA optimize
            conn.execute(text("PRAGMA optimize"))
            # 执行VACUUM
            conn.execute(text("VACUUM"))
            # 提交事务
            conn.commit()
        logger.info("数据库优化成功")
    except Exception as e:
        logger.error(f"数据库优化失败: {e}")
        raise


if __name__ == "__main__":
    init_database()
