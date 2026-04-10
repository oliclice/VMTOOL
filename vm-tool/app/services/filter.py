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
    
    def __init__(self, db: Session = None):
        if db:
            self.db = db
        else:
            self.db = next(get_db())
        self.repo = WordRepository(self.db)
    
    def filter_by_length(self, min_length: int = 1, max_length: int = None) -> List[Dict[str, Any]]:
        """根据词长过滤"""
        try:
            all_words = self.repo.get_all()
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
    
    def filter_by_weight(self, min_weight: float = 0.0, max_weight: float = None) -> List[Dict[str, Any]]:
        """根据权重过滤"""
        try:
            all_words = self.repo.get_all()
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
            return self.repo.search(pattern)
        except Exception as e:
            logger.error(f"根据模式过滤失败: {e}")
            raise DictError(f"根据模式过滤失败: {e}")
    
    def import_from_txt(self, file_path: str, encoding: str = 'utf-8', progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """从TXT文件导入"""
        try:
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
                        progress = int((processed_lines / total_lines) * 100)
                        progress_callback(progress, f"处理文件: {os.path.basename(file_path)}")
            
            # 批量添加
            from app.services.dict import DictService
            dict_service = DictService(self.db)
            result = dict_service.add_words(words)
            
            if progress_callback:
                progress_callback(100, f"导入完成: {os.path.basename(file_path)}")
            
            return result
        except FileError:
            raise
        except Exception as e:
            logger.error(f"从TXT文件导入失败: {e}")
            raise FileError(f"从TXT文件导入失败: {e}")
    
    def import_from_csv(self, file_path: str, encoding: str = 'utf-8', progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """从CSV文件导入"""
        try:
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
                        progress = int((processed_rows / total_rows) * 100)
                        progress_callback(progress, f"处理文件: {os.path.basename(file_path)}")
            
            # 批量添加
            from app.services.dict import DictService
            dict_service = DictService(self.db)
            result = dict_service.add_words(words)
            
            if progress_callback:
                progress_callback(100, f"导入完成: {os.path.basename(file_path)}")
            
            return result
        except FileError:
            raise
        except Exception as e:
            logger.error(f"从CSV文件导入失败: {e}")
            raise FileError(f"从CSV文件导入失败: {e}")
    
    def import_from_json(self, file_path: str, encoding: str = 'utf-8', progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """从JSON文件导入"""
        try:
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
                        progress = int((processed_items / total_items) * 100)
                        progress_callback(progress, f"处理文件: {os.path.basename(file_path)}")
            
            # 批量添加
            from app.services.dict import DictService
            dict_service = DictService(self.db)
            result = dict_service.add_words(words)
            
            if progress_callback:
                progress_callback(100, f"导入完成: {os.path.basename(file_path)}")
            
            return result
        except FileError:
            raise
        except Exception as e:
            logger.error(f"从JSON文件导入失败: {e}")
            raise FileError(f"从JSON文件导入失败: {e}")
    
    def export_to_txt(self, output_file: str, words: List[Dict[str, Any]] = None, encoding: str = 'utf-8') -> int:
        """导出到TXT文件"""
        try:
            if not words:
                # 获取所有词
                all_words = self.repo.get_all()
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
    
    def export_to_csv(self, output_file: str, words: List[Dict[str, Any]] = None, encoding: str = 'utf-8') -> int:
        """导出到CSV文件"""
        try:
            if not words:
                # 获取所有词
                all_words = self.repo.get_all()
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
    
    def export_to_json(self, output_file: str, words: List[Dict[str, Any]] = None, encoding: str = 'utf-8') -> int:
        """导出到JSON文件"""
        try:
            if not words:
                # 获取所有词
                all_words = self.repo.get_all()
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
    
    def batch_import(self, directory: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """批量导入目录中的文件"""
        try:
            if not os.path.exists(directory):
                raise FileError(f"目录不存在: {directory}")
            
            # 获取所有待导入的文件
            import_files = []
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
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
