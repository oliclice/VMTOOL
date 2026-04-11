"""过滤和导入服务"""
import os
import json
import csv
from typing import List, Dict, Any, Optional, Callable
from sqlalchemy.orm import Session
import logging
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from app.dal.repositories import WordRepository
from app.dal.database import get_db
from app.core.errors import FileError, DictError
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FilterService:
    """过滤和导入服务"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
    
    def filter_by_length(self, min_length: int = 1, max_length: Optional[int] = None) -> List[Dict[str, Any]]:
        """根据词长过滤"""
        try:
            # 使用自己的数据库会话
            db = self.db or next(get_db())
            repo = WordRepository(db)
            
            all_words = repo.get_all()
            filtered = []
            
            for word in all_words:
                length = len(word.word)
                if length >= min_length and (max_length is None or length <= max_length):
                    filtered.append({
                        "word": word.word,
                        "code": word.code,
                        "weight": word.weight
                    })
            
            return filtered
        except Exception as e:
            logger.error(f"根据词长过滤失败: {e}")
            raise DictError(f"根据词长过滤失败: {e}")
    
    def filter_by_weight(self, min_weight: float = 0.0, max_weight: Optional[float] = None) -> List[Dict[str, Any]]:
        """根据权重过滤"""
        try:
            # 使用自己的数据库会话
            db = self.db or next(get_db())
            repo = WordRepository(db)
            
            all_words = repo.get_all()
            filtered = []
            
            for word in all_words:
                if word.weight >= min_weight and (max_weight is None or word.weight <= max_weight):
                    filtered.append({
                        "word": word.word,
                        "code": word.code,
                        "weight": word.weight
                    })
            
            return filtered
        except Exception as e:
            logger.error(f"根据权重过滤失败: {e}")
            raise DictError(f"根据权重过滤失败: {e}")
    
    def filter_by_pattern(self, pattern: str) -> List[Dict[str, Any]]:
        """根据模式过滤"""
        try:
            # 使用自己的数据库会话
            db = self.db or next(get_db())
            repo = WordRepository(db)
            
            db_words = repo.search(pattern)
            return [{
                "word": word.word,
                "code": word.code,
                "weight": word.weight
            } for word in db_words]
        except Exception as e:
            logger.error(f"根据模式过滤失败: {e}")
            raise DictError(f"根据模式过滤失败: {e}")
    
    def import_from_txt(self, file_path: str, encoding: str = 'utf-8', progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """从TXT文件导入"""
        import time
        import pathlib
        start_time = time.time()
        
        try:
            # 规范化路径，防止路径遍历攻击
            file_path = str(pathlib.Path(file_path).resolve())
            if not os.path.exists(file_path):
                raise FileError(f"文件不存在: {file_path}")
            
            # 先计算文件行数，用于进度显示
            total_lines = 0
            with open(file_path, 'r', encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    total_lines += 1
            
            words = []
            processed_lines = 0
            
            with open(file_path, 'r', encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
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
                    
                    processed_lines += 1
                    if progress_callback and total_lines > 0:
                        # 文件读取阶段只占用0-50%的进度
                        progress = int((processed_lines / total_lines) * 50)
                        progress_callback(progress, f"处理文件: {os.path.basename(file_path)}")
            
            # 批量添加
            from app.services.dict import DictService
            # 使用自己的数据库会话
            db = self.db or next(get_db())
            dict_service = DictService(db)
            
            # 传递进度回调，调整进度范围为50-100%
            def batch_progress_callback(progress: int, message: str) -> None:
                # 将批量添加的进度映射到50-100%的范围
                adjusted_progress = 50 + int(progress * 0.5)
                if progress_callback:
                    progress_callback(adjusted_progress, message)
            
            result = dict_service.add_words(words, progress_callback=batch_progress_callback)
            
            # 计算耗时和每千条平均耗时
            end_time = time.time()
            total_time = end_time - start_time
            added_count = result.get('added', 0)
            avg_time_per_1000 = (total_time / added_count * 1000) if added_count > 0 else 0
            
            # 添加耗时信息到结果
            result['total_time'] = total_time
            result['avg_time_per_1000'] = avg_time_per_1000
            result['total_count'] = len(words)
            
            if progress_callback:
                progress_callback(100, f"导入完成: {os.path.basename(file_path)}")
            
            # 数据导入完成后创建索引并优化数据库
            from app.dal.init_db import create_indexes, optimize_database
            create_indexes()
            optimize_database()
            
            return result
        except FileError:
            raise
        except Exception as e:
            logger.error(f"从TXT文件导入失败: {e}")
            raise FileError(f"从TXT文件导入失败: {e}")
    
    def import_from_csv(self, file_path: str, encoding: str = 'utf-8', progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """从CSV文件导入"""
        import time
        import pathlib
        start_time = time.time()
        
        try:
            # 规范化路径，防止路径遍历攻击
            file_path = str(pathlib.Path(file_path).resolve())
            if not os.path.exists(file_path):
                raise FileError(f"文件不存在: {file_path}")
            
            # 先计算文件行数，用于进度显示
            total_rows = 0
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_rows += 1
            
            words = []
            processed_rows = 0
            
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    word = row.get('word') or row.get('词')
                    code = row.get('code') or row.get('编码')
                    weight = float(row.get('weight', 1.0) or row.get('权重', 1.0))
                    
                    if word and code:
                        words.append({
                            'word': word,
                            'code': code,
                            'weight': weight
                        })
                    
                    processed_rows += 1
                    if progress_callback and total_rows > 0:
                        # 文件读取阶段只占用0-50%的进度
                        progress = int((processed_rows / total_rows) * 50)
                        progress_callback(progress, f"处理文件: {os.path.basename(file_path)}")
            
            # 批量添加
            from app.services.dict import DictService
            # 使用自己的数据库会话
            db = self.db or next(get_db())
            dict_service = DictService(db)
            
            # 传递进度回调，调整进度范围为50-100%
            def batch_progress_callback(progress: int, message: str) -> None:
                # 将批量添加的进度映射到50-100%的范围
                adjusted_progress = 50 + int(progress * 0.5)
                if progress_callback:
                    progress_callback(adjusted_progress, message)
            
            result = dict_service.add_words(words, progress_callback=batch_progress_callback)
            
            # 计算耗时和每千条平均耗时
            end_time = time.time()
            total_time = end_time - start_time
            added_count = result.get('added', 0)
            avg_time_per_1000 = (total_time / added_count * 1000) if added_count > 0 else 0
            
            # 添加耗时信息到结果
            result['total_time'] = total_time
            result['avg_time_per_1000'] = avg_time_per_1000
            result['total_count'] = len(words)
            
            if progress_callback:
                progress_callback(100, f"导入完成: {os.path.basename(file_path)}")
            
            # 数据导入完成后创建索引并优化数据库
            from app.dal.init_db import create_indexes, optimize_database
            create_indexes()
            optimize_database()
            
            return result
        except FileError:
            raise
        except Exception as e:
            logger.error(f"从CSV文件导入失败: {e}")
            raise FileError(f"从CSV文件导入失败: {e}")
    
    def import_from_json(self, file_path: str, encoding: str = 'utf-8', progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """从JSON文件导入"""
        import time
        import pathlib
        start_time = time.time()
        
        try:
            # 规范化路径，防止路径遍历攻击
            file_path = str(pathlib.Path(file_path).resolve())
            if not os.path.exists(file_path):
                raise FileError(f"文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
            
            words = []
            total_items = len(data) if isinstance(data, list) else 0
            processed_items = 0
            
            if isinstance(data, list):
                for item in data:
                    word = item.get('word') or item.get('词')
                    code = item.get('code') or item.get('编码')
                    weight = float(item.get('weight', 1.0) or item.get('权重', 1.0))
                    
                    if word and code:
                        words.append({
                            'word': word,
                            'code': code,
                            'weight': weight
                        })
                    
                    processed_items += 1
                    if progress_callback and total_items > 0:
                        # 文件读取阶段只占用0-50%的进度
                        progress = int((processed_items / total_items) * 50)
                        progress_callback(progress, f"处理文件: {os.path.basename(file_path)}")
            
            # 批量添加
            from app.services.dict import DictService
            # 使用自己的数据库会话
            db = self.db or next(get_db())
            dict_service = DictService(db)
            
            # 传递进度回调，调整进度范围为50-100%
            def batch_progress_callback(progress: int, message: str) -> None:
                # 将批量添加的进度映射到50-100%的范围
                adjusted_progress = 50 + int(progress * 0.5)
                if progress_callback:
                    progress_callback(adjusted_progress, message)
            
            result = dict_service.add_words(words, progress_callback=batch_progress_callback)
            
            # 计算耗时和每千条平均耗时
            end_time = time.time()
            total_time = end_time - start_time
            added_count = result.get('added', 0)
            avg_time_per_1000 = (total_time / added_count * 1000) if added_count > 0 else 0
            
            # 添加耗时信息到结果
            result['total_time'] = total_time
            result['avg_time_per_1000'] = avg_time_per_1000
            result['total_count'] = len(words)
            
            if progress_callback:
                progress_callback(100, f"导入完成: {os.path.basename(file_path)}")
            
            # 数据导入完成后创建索引并优化数据库
            from app.dal.init_db import create_indexes, optimize_database
            create_indexes()
            optimize_database()
            
            return result
        except FileError:
            raise
        except Exception as e:
            logger.error(f"从JSON文件导入失败: {e}")
            raise FileError(f"从JSON文件导入失败: {e}")
    
    def export_to_txt(self, output_file: str, words: Optional[List[Dict[str, Any]]] = None, encoding: str = 'utf-8') -> int:
        """导出到TXT文件"""
        import pathlib
        try:
            # 规范化路径，防止路径遍历攻击
            output_file = str(pathlib.Path(output_file).resolve())
            
            if not words:
                # 使用自己的数据库会话
                db = self.db or next(get_db())
                repo = WordRepository(db)
                # 获取所有词
                all_words = repo.get_all()
                words = [{
                    "word": word.word,
                    "code": word.code,
                    "weight": word.weight
                } for word in all_words]
            
            with open(output_file, 'w', encoding=encoding) as f:
                for word in words:
                    f.write(f"{word['word']}\t{word['code']}\t{word['weight']}\n")
            
            return len(words)
        except Exception as e:
            logger.error(f"导出到TXT文件失败: {e}")
            raise FileError(f"导出到TXT文件失败: {e}")
    
    def export_to_csv(self, output_file: str, words: Optional[List[Dict[str, Any]]] = None, encoding: str = 'utf-8') -> int:
        """导出到CSV文件"""
        import pathlib
        try:
            # 规范化路径，防止路径遍历攻击
            output_file = str(pathlib.Path(output_file).resolve())
            
            if not words:
                # 使用自己的数据库会话
                db = self.db or next(get_db())
                repo = WordRepository(db)
                # 获取所有词
                all_words = repo.get_all()
                words = [{
                    "word": word.word,
                    "code": word.code,
                    "weight": word.weight
                } for word in all_words]
            
            with open(output_file, 'w', newline='', encoding=encoding) as f:
                fieldnames = ['word', 'code', 'weight']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(words)
            
            return len(words)
        except Exception as e:
            logger.error(f"导出到CSV文件失败: {e}")
            raise FileError(f"导出到CSV文件失败: {e}")
    
    def export_to_json(self, output_file: str, words: Optional[List[Dict[str, Any]]] = None, encoding: str = 'utf-8') -> int:
        """导出到JSON文件"""
        import pathlib
        try:
            # 规范化路径，防止路径遍历攻击
            output_file = str(pathlib.Path(output_file).resolve())
            
            if not words:
                # 使用自己的数据库会话
                db = self.db or next(get_db())
                repo = WordRepository(db)
                # 获取所有词
                all_words = repo.get_all()
                words = [{
                    "word": word.word,
                    "code": word.code,
                    "weight": word.weight
                } for word in all_words]
            
            with open(output_file, 'w', encoding=encoding) as f:
                json.dump(words, f, ensure_ascii=False, indent=2)
            
            return len(words)
        except Exception as e:
            logger.error(f"导出到JSON文件失败: {e}")
            raise FileError(f"导出到JSON文件失败: {e}")
    
    def batch_import(self, directory: str, progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """批量导入目录中的文件"""
        import pathlib
        try:
            # 规范化路径，防止路径遍历攻击
            directory = str(pathlib.Path(directory).resolve())
            
            if not os.path.exists(directory):
                raise FileError(f"目录不存在: {directory}")
            
            # 获取所有待导入的文件
            import_files = []
            for filename in os.listdir(directory):
                # 确保文件名安全，不包含路径分隔符
                if '/' in filename or '\\' in filename:
                    continue
                file_path = str(pathlib.Path(directory) / filename)
                if os.path.isfile(file_path) and (filename.endswith('.txt') or filename.endswith('.csv') or filename.endswith('.json')):
                    import_files.append(file_path)
            
            total_files = len(import_files)
            if total_files == 0:
                return {
                    "total_imported": 0,
                    "failed_files": []
                }
            
            total_imported = 0
            failed_files = []
            processed_files = 0
            
            # 多线程处理
            with ThreadPoolExecutor(max_workers=4) as executor:
                # 提交所有导入任务
                future_to_file = {}
                for file_path in import_files:
                    filename = os.path.basename(file_path)
                    if filename.endswith('.txt'):
                        future = executor.submit(self.import_from_txt, file_path, 'utf-8', progress_callback)
                    elif filename.endswith('.csv'):
                        future = executor.submit(self.import_from_csv, file_path, 'utf-8', progress_callback)
                    elif filename.endswith('.json'):
                        future = executor.submit(self.import_from_json, file_path, 'utf-8', progress_callback)
                    else:
                        continue
                    future_to_file[future] = file_path
                
                # 处理任务结果
                for future in concurrent.futures.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    filename = os.path.basename(file_path)
                    try:
                        result = future.result()
                        total_imported += result.get('added', 0)
                    except Exception as e:
                        logger.error(f"导入文件 {filename} 失败: {e}")
                        failed_files.append(filename)
                    
                    processed_files += 1
                    if progress_callback and total_files > 0:
                        overall_progress = int((processed_files / total_files) * 100)
                        progress_callback(overall_progress, f"已处理 {processed_files}/{total_files} 个文件")
            
            if progress_callback:
                progress_callback(100, "批量导入完成")
            
            return {
                "total_imported": total_imported,
                "failed_files": failed_files
            }
        except FileError:
            raise
        except Exception as e:
            logger.error(f"批量导入失败: {e}")
            raise FileError(f"批量导入失败: {e}")
