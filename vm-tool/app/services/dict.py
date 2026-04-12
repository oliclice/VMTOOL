"""码表词条服务"""
from typing import List, Optional, Dict, Any, Callable
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
    
    def __init__(self, db: Optional[Session] = None):
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
                    "is_character": db_word.is_character,
                    "is_special": db_word.is_special,
                    "created_at": db_word.created_at,
                    "updated_at": db_word.updated_at
                }
            return None
        except Exception as e:
            logger.error(f"获取词条失败: {e}")
            raise DictError(f"获取词条失败: {e}")
    
    def get_word_by_text(self, word: str) -> Optional[Word]:
        """根据词的文本获取词对象"""
        try:
            return self.repo.get_by_word(word)
        except Exception as e:
            logger.error(f"获取词条失败: {e}")
            raise DictError(f"获取词条失败: {e}")
    
    def get_word_by_id(self, word_id: int) -> Optional[Word]:
        """根据词的ID获取词对象"""
        try:
            return self.db.query(Word).filter(Word.id == word_id).first()
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
    
    def get_special_chars(self, skip: int = 0, limit: int = None) -> List[Dict[str, Any]]:
        """获取所有特殊字符"""
        try:
            db_words = self.repo.get_special_chars(skip, limit)
            return [{
                "id": word.id,
                "word": word.word,
                "code": word.code,
                "weight": word.weight,
                "is_active": word.is_active,
                "is_special": word.is_special,
                "manual": word.manual
            } for word in db_words]
        except Exception as e:
            logger.error(f"获取特殊字符失败: {e}")
            raise DictError(f"获取特殊字符失败: {e}")
    
    def count_special_chars(self) -> int:
        """统计特殊字符数量"""
        try:
            return self.repo.count_special_chars()
        except Exception as e:
            logger.error(f"统计特殊字符数量失败: {e}")
            raise DictError(f"统计特殊字符数量失败: {e}")
    
    def get_characters(self, skip: int = 0, limit: int = None) -> List[Dict[str, Any]]:
        """获取所有字"""
        try:
            db_words = self.repo.get_characters(skip, limit)
            return [{
                "id": word.id,
                "word": word.word,
                "code": word.code,
                "weight": word.weight,
                "is_active": word.is_active,
                "is_character": word.is_character,
                "is_special": word.is_special,
                "manual": word.manual
            } for word in db_words]
        except Exception as e:
            logger.error(f"获取字失败: {e}")
            raise DictError(f"获取字失败: {e}")
    
    def get_words(self, skip: int = 0, limit: int = None) -> List[Dict[str, Any]]:
        """获取所有词"""
        try:
            db_words = self.repo.get_words(skip, limit)
            return [{
                "id": word.id,
                "word": word.word,
                "code": word.code,
                "weight": word.weight,
                "is_active": word.is_active,
                "is_character": word.is_character,
                "is_special": word.is_special,
                "manual": word.manual
            } for word in db_words]
        except Exception as e:
            logger.error(f"获取词失败: {e}")
            raise DictError(f"获取词失败: {e}")
    

    
    @performance_monitor
    def add_word(self, word: str, code: Optional[str] = None, weight: float = 1.0, is_character: Optional[bool] = None, is_special: bool = False, manual: bool = False) -> Dict[str, Any]:
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
            
            db_word = self.repo.create(word, code, weight, is_character, is_special, manual)
            return {
                "word": db_word.word,
                "code": db_word.code,
                "weight": db_word.weight,
                "is_character": db_word.is_character,
                "is_special": db_word.is_special,
                "manual": db_word.manual
            }
        except DictError:
            raise
        except Exception as e:
            logger.error(f"添加词条失败: {e}")
            raise DictError(f"添加词条失败: {e}")
    
    @optimize_batch_operation(batch_size=500)
    def add_words(self, words: List[Dict[str, Any]], progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """批量添加词条"""
        try:
            total_words = len(words)
            if total_words == 0:
                return {
                    "added": 0,
                    "existing": 0,
                    "existing_pairs": []
                }
            
            # 预处理词条数据
            processed_words_data = []
            valid_words = []
            existing_pairs = []
            
            for word_data in words:
                word = word_data.get("word")
                code = word_data.get("code")
                
                # 自动判断是字还是词
                if "is_character" not in word_data:
                    word_data["is_character"] = len(word) == 1
                
                # 如果没有提供编码，自动生成（仅对词表，字表不自动生成）
                if code is None and not word_data["is_character"]:
                    code = self.generate_code(word)
                    word_data["code"] = code
                    word_data["manual"] = False  # 自动生成的编码，manual设为False
                elif code is None and word_data["is_character"]:
                    # 字表没有提供编码，跳过
                    continue
                
                processed_words_data.append(word_data)
            
            # 批量查询已存在的词条
            if processed_words_data:
                # 收集所有 (word, code) 对
                word_code_pairs = [(wd.get("word"), wd.get("code")) for wd in processed_words_data]
                
                # 批量查询已存在的词条
                existing_word_code_pairs = self.repo.get_by_word_code_pairs(word_code_pairs)
                
                # 转换为集合，方便快速查找
                existing_set = set(existing_word_code_pairs)
                
                # 过滤出有效的词条
                for word_data in processed_words_data:
                    word = word_data.get("word")
                    code = word_data.get("code")
                    
                    if (word, code) not in existing_set:
                        valid_words.append(word_data)
                    else:
                        existing_pairs.append(f"{word}:{code}")
            
            # 处理进度回调
            processed_count = len(processed_words_data)
            if progress_callback and total_words > 0:
                progress_callback(50, "完成词条预处理")
            
            # 批量创建
            if valid_words:
                if progress_callback:
                    progress_callback(70, "开始批量创建...")
                # 调用批量创建方法
                self.repo.bulk_create(valid_words)
                if progress_callback:
                    progress_callback(100, "批量创建完成")
                
            return {
                "added": len(valid_words),
                "existing": len(existing_pairs),
                "existing_pairs": existing_pairs
            }
        except Exception as e:
            logger.error(f"批量添加词条失败: {e}")
            raise DictError(f"批量添加词条失败: {e}")
    
    def add_characters(self, characters: List[Dict[str, Any]], progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """批量添加字表"""
        try:
            total_chars = len(characters)
            if total_chars == 0:
                return {
                    "added": 0,
                    "existing": 0,
                    "existing_pairs": []
                }
            
            # 为每个字添加is_character=True
            for char_data in characters:
                char_data["is_character"] = True
            
            # 调用批量添加方法
            return self.add_words(characters, progress_callback=progress_callback)
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
    
    def delete_character(self, char: str) -> bool:
        """删除字符"""
        try:
            # 调用现有的delete_word方法
            return self.delete_word(char)
        except Exception as e:
            logger.error(f"删除字符失败: {e}")
            raise DictError(f"删除字符失败: {e}")
    
    def delete_table(self, table_type: str) -> Dict[str, Any]:
        """删除指定类型的数据表
        
        Args:
            table_type: 表类型，支持 "chars"（字表）、"words"（词表）、"special"（特殊字符表）
        
        Returns:
            Dict[str, Any]: 删除结果，包含 deleted 字段表示删除的数量
        """
        from sqlalchemy import text
        
        try:
            # 根据类型删除对应的数据
            if table_type == "chars":
                # 删除字表（is_character=True 的记录）
                result = self.db.execute(
                    text("DELETE FROM words WHERE is_character = :is_character"),
                    {"is_character": True}
                )
            elif table_type == "words":
                # 删除词表（is_character=False 且 is_special=False 的记录）
                result = self.db.execute(
                    text("DELETE FROM words WHERE is_character = :is_character AND is_special = :is_special"),
                    {"is_character": False, "is_special": False}
                )
            elif table_type == "special":
                # 删除特殊字符表（is_special=True 的记录）
                result = self.db.execute(
                    text("DELETE FROM words WHERE is_special = :is_special"),
                    {"is_special": True}
                )
            else:
                raise DictError(f"不支持的表类型：{table_type}")
            
            # 提交事务
            self.db.commit()
            
            return {"deleted": result.rowcount}
        except DictError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除表失败: {e}")
            raise DictError(f"删除表失败: {e}")
    
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
    
    def get_all_words(self, skip: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有词条"""
        try:
            db_words = self.repo.get_all(skip, limit)
            return [{
                "word": word.word,
                "code": word.code,
                "weight": word.weight,
                "manual": word.manual,
                "is_character": word.is_character
            } for word in db_words]
        except Exception as e:
            logger.error(f"获取所有词条失败: {e}")
            raise DictError(f"获取所有词条失败: {e}")
    
    def search_words(self, keyword: str, field: str = "word") -> List[Dict[str, Any]]:
        """搜索词条"""
        try:
            db_words = self.repo.search(keyword, field)
            return [{
                "word": word.word,
                "code": word.code,
                "weight": word.weight,
                "manual": word.manual
            } for word in db_words]
        except Exception as e:
            logger.error(f"搜索词条失败: {e}")
            raise DictError(f"搜索词条失败: {e}")
    
    def search_characters(self, keyword: str, field: str = "word") -> List[Dict[str, Any]]:
        """搜索字符"""
        try:
            db_words = self.repo.search(keyword, field)
            # 过滤出is_character=True的结果
            return [{
                "id": word.id,
                "word": word.word,
                "code": word.code,
                "weight": word.weight,
                "is_active": word.is_active,
                "is_character": word.is_character,
                "is_special": word.is_special,
                "manual": word.manual
            } for word in db_words if word.is_character]
        except Exception as e:
            logger.error(f"搜索字符失败: {e}")
            raise DictError(f"搜索字符失败: {e}")
    
    def get_code_preview(self) -> List[Dict[str, Any]]:
        """获取编码变化预览数据"""
        try:
            from sqlalchemy import func
            
            preview_data = []
            
            # 获取不同长度的词各2个
            for length in [2, 3, 4]:
                # 获取该长度的词，排除手动编码的
                words = self.db.query(Word).filter(
                    Word.manual == False, 
                    Word.is_character == False, 
                    func.length(Word.word) == length
                ).limit(2).all()
                
                for word in words:
                    old_code = word.code
                    new_code = self.generate_code(word.word)
                    preview_data.append({
                        "word": word.word,
                        "old_code": old_code,
                        "new_code": new_code
                    })
            
            return preview_data
        except Exception as e:
            logger.error(f"获取编码预览失败: {e}")
            return []
    
    def calculate_all_codes(self, progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """计算所有未手动修改过编码的词条的编码"""
        try:
            # 保存原始配置
            original_config = self.code_generator.get_config().copy()
            
            # 设置为使用自定义规则，这样会使用默认规则
            self.code_generator.set_config({'rule': 'custom'})
            
            try:
                # 获取所有未手动修改过编码的词条，排除字表（is_character=True）
                db_words = self.db.query(Word).filter(Word.manual == False, Word.is_character == False).all()
                
                total = len(db_words)
                updated = 0
                failed = 0
                
                for i, db_word in enumerate(db_words):
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
                    
                    # 每处理100个词条更新一次进度
                    if progress_callback and (i + 1) % 100 == 0:
                        progress = int((i + 1) / total * 100)
                        progress_callback(progress, f"已处理 {i + 1}/{total} 词条")
                
                # 提交更改
                self.db.commit()
                
                if progress_callback:
                    progress_callback(100, "计算完成")
                
                return {
                    "total": total,
                    "updated": updated,
                    "failed": failed
                }
            finally:
                # 恢复原始配置
                self.code_generator.set_config(original_config)
        except Exception as e:
            logger.error(f"批量计算编码失败: {e}")
            raise DictError(f"批量计算编码失败: {e}")
    
    def export_data(self, output_file: str, format: str = "txt", encoding: str = "utf-8", table: str = None) -> int:
        """导出数据"""
        try:
            from app.services.filter import FilterService
            filter_service = FilterService(self.db)
            
            # 获取指定表的数据
            if table:
                if table == "words":
                    # 只获取词表数据
                    words = self.get_words()
                elif table == "chars":
                    # 只获取字表数据
                    chars = self.get_characters()
                    words = [{
                        "word": char["word"],
                        "code": char["code"],
                        "weight": char["weight"]
                    } for char in chars]
                elif table == "special":
                    # 只获取特殊字符表数据
                    special_chars = self.get_special_chars()
                    words = [{
                        "word": char["word"],
                        "code": char["code"],
                        "weight": char["weight"]
                    } for char in special_chars]
                else:
                    raise DictError(f"不支持的表名: {table}")
            else:
                words = None
            
            if format == "txt":
                return filter_service.export_to_txt(output_file, words=words, encoding=encoding)
            elif format == "csv":
                return filter_service.export_to_csv(output_file, words=words, encoding=encoding)
            elif format == "json":
                return filter_service.export_to_json(output_file, words=words, encoding=encoding)
            else:
                raise DictError(f"不支持的导出格式: {format}")
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            raise DictError(f"导出数据失败: {e}")
