"""数据库初始化脚本"""
import logging
from app.dal.database import engine, Base
from app.dal.models import Word, DictConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库"""
    try:
        logger.info("开始创建数据库表结构...")
        # 创建所有表
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


if __name__ == "__main__":
    init_database()
