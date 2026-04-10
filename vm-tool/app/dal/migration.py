"""数据迁移工具"""
import os
import json
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.dal.models import Word, DictConfig
from app.dal.database import SessionLocal
from app.core.config import settings
from app.core.errors import FileError, DictError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def import_from_old_format(file_path: str) -> List[Dict[str, Any]]:
    """从旧格式文件导入数据"""
    words = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 解析旧格式: 词 编码 权重
                parts = line.split('\t')
                if len(parts) >= 2:
                    word = parts[0]
                    code = parts[1]
                    weight = float(parts[2]) if len(parts) >= 3 else 1.0
                    
                    words.append({
                        'word': word,
                        'code': code,
                        'weight': weight
                    })
    except Exception as e:
        logger.error(f"导入文件失败: {e}")
        raise
    
    return words


def migrate_old_data(old_file_path: str = None) -> Dict[str, Any]:
    """迁移旧数据到新数据库"""
    if not old_file_path:
        old_file_path = settings.MAIN_DICT
    
    if not os.path.exists(old_file_path):
        logger.error(f"旧数据文件不存在: {old_file_path}")
        return {"success": False, "message": f"旧数据文件不存在: {old_file_path}"}
    
    logger.info(f"开始从 {old_file_path} 导入数据...")
    
    # 导入旧数据
    words = import_from_old_format(old_file_path)
    logger.info(f"共导入 {len(words)} 条数据")
    
    # 保存到数据库
    db = SessionLocal()
    try:
        # 批量插入
        batch_size = 1000
        total_added = 0
        total_skipped = 0
        
        for i in range(0, len(words), batch_size):
            batch = words[i:i+batch_size]
            valid_words = []
            
            for word_data in batch:
                # 检查是否已存在
                if not db.query(Word).filter(Word.word == word_data['word']).first():
                    valid_words.append(word_data)
                else:
                    total_skipped += 1
            
            if valid_words:
                db_words = [Word(**word) for word in valid_words]
                db.add_all(db_words)
                db.commit()
                total_added += len(valid_words)
                logger.info(f"已插入 {total_added}/{len(words)} 条数据，跳过 {total_skipped} 条重复数据")
        
        logger.info("数据迁移完成")
        return {
            "success": True,
            "total": len(words),
            "added": total_added,
            "skipped": total_skipped
        }
    except Exception as e:
        logger.error(f"数据迁移失败: {e}")
        db.rollback()
        return {"success": False, "message": f"数据迁移失败: {e}"}
    finally:
        db.close()


def export_to_old_format(output_file: str = None) -> int:
    """导出数据到旧格式"""
    if not output_file:
        output_file = settings.OUTPUT_FILE
    
    logger.info(f"开始导出数据到 {output_file}...")
    
    db = SessionLocal()
    try:
        # 获取所有词
        words = db.query(Word).filter(Word.is_active == True).all()
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            for word in words:
                f.write(f"{word.word}\t{word.code}\t{word.weight}\n")
        
        logger.info(f"共导出 {len(words)} 条数据")
        return len(words)
    except Exception as e:
        logger.error(f"数据导出失败: {e}")
        return 0
    finally:
        db.close()


def migrate_config() -> Dict[str, Any]:
    """迁移配置"""
    logger.info("开始迁移配置...")
    
    db = SessionLocal()
    try:
        # 检查是否已有配置
        if db.query(DictConfig).count() == 0:
            # 插入默认配置
            default_configs = [
                DictConfig(key="version", value="2.0.0", description="当前版本"),
                DictConfig(key="encoding", value="utf-8", description="默认编码"),
                DictConfig(key="auto_backup", value="true", description="自动备份"),
                DictConfig(key="batch_size", value="1000", description="批量操作大小"),
                DictConfig(key="cache_size", value="1000", description="缓存大小"),
                DictConfig(key="cache_ttl", value="3600", description="缓存过期时间（秒）"),
            ]
            db.add_all(default_configs)
            db.commit()
            logger.info("初始配置插入成功")
            return {"success": True, "added": len(default_configs)}
        else:
            logger.info("配置已存在，跳过初始配置")
            return {"success": True, "added": 0}
    except Exception as e:
        logger.error(f"配置迁移失败: {e}")
        db.rollback()
        return {"success": False, "message": f"配置迁移失败: {e}"}
    finally:
        db.close()


def validate_data() -> Dict[str, Any]:
    """验证数据"""
    logger.info("开始验证数据...")
    
    db = SessionLocal()
    try:
        issues = {
            "empty_word": [],
            "empty_code": [],
            "invalid_weight": [],
            "duplicate_word": []
        }
        
        # 获取所有词
        words = db.query(Word).all()
        word_set = set()
        
        for word in words:
            # 检查空词
            if not word.word or word.word.strip() == "":
                issues["empty_word"].append(word.id)
            
            # 检查空编码
            if not word.code or word.code.strip() == "":
                issues["empty_code"].append(word.id)
            
            # 检查无效权重
            if word.weight < 0 or word.weight > 100:
                issues["invalid_weight"].append(word.id)
            
            # 检查重复词
            if word.word in word_set:
                issues["duplicate_word"].append(word.id)
            else:
                word_set.add(word.word)
        
        # 计算问题总数
        total_issues = sum(len(items) for items in issues.values())
        
        logger.info(f"数据验证完成，发现 {total_issues} 个问题")
        return {
            "success": True,
            "total_issues": total_issues,
            "issues": issues
        }
    except Exception as e:
        logger.error(f"数据验证失败: {e}")
        return {"success": False, "message": f"数据验证失败: {e}"}
    finally:
        db.close()


def fix_data() -> Dict[str, Any]:
    """修复数据"""
    logger.info("开始修复数据...")
    
    db = SessionLocal()
    try:
        fixes = {
            "empty_word": 0,
            "empty_code": 0,
            "invalid_weight": 0,
            "duplicate_word": 0
        }
        
        # 修复空词
        empty_word_count = db.query(Word).filter(Word.word == "").delete()
        fixes["empty_word"] = empty_word_count
        
        # 修复空编码
        empty_code_count = db.query(Word).filter(Word.code == "").delete()
        fixes["empty_code"] = empty_code_count
        
        # 修复无效权重
        invalid_weight_count = db.query(Word).filter((Word.weight < 0) | (Word.weight > 100)).update({"weight": 1.0})
        fixes["invalid_weight"] = invalid_weight_count
        
        # 修复重复词（保留权重最高的）
        # 这里需要更复杂的逻辑，暂时跳过
        
        db.commit()
        
        total_fixes = sum(fixes.values())
        logger.info(f"数据修复完成，修复了 {total_fixes} 个问题")
        return {
            "success": True,
            "total_fixes": total_fixes,
            "fixes": fixes
        }
    except Exception as e:
        logger.error(f"数据修复失败: {e}")
        db.rollback()
        return {"success": False, "message": f"数据修复失败: {e}"}
    finally:
        db.close()


def full_migration() -> Dict[str, Any]:
    """完整迁移流程"""
    logger.info("开始完整迁移流程...")
    
    # 迁移旧数据
    data_migration = migrate_old_data()
    
    # 迁移配置
    config_migration = migrate_config()
    
    # 验证数据
    validation = validate_data()
    
    # 修复数据
    if validation.get("total_issues", 0) > 0:
        fix = fix_data()
    else:
        fix = {"success": True, "total_fixes": 0, "fixes": {}}
    
    logger.info("完整迁移流程完成")
    return {
        "data_migration": data_migration,
        "config_migration": config_migration,
        "validation": validation,
        "fix": fix
    }


if __name__ == "__main__":
    # 示例用法
    result = full_migration()
    print(json.dumps(result, ensure_ascii=False, indent=2))
