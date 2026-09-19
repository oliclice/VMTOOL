"""过滤和导入服务"""
import concurrent.futures
import csv
import json
import logging
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import DictError, FileError
from app.dal.database import get_db
from app.dal.repositories import WordRepository

logger = logging.getLogger(__name__)


class FilterService:
    """过滤和导入服务

    会话所有权（与 DictService / WeightCalculator / StatsService 一致）：
    - ``db=None``：本服务自建会话并持有，必须由调用方调 :meth:`close` 释放
      （可作上下文管理器：``with FilterService() as svc: ...``）；
    - ``db=<外部会话>``：由注入方负责关闭，本服务不碰它的生命周期。

    此前每个方法都用 ``self.db or get_db()`` 现场建会话且从不关闭；T5 把
    ``get_db()`` 改成显式会话工厂后，这种写法从「被生成器意外关闭」变成真实泄漏。
    """

    def __init__(self, db: Session | None = None):
        self._owns_db = db is None
        self.db = db if db is not None else get_db()

    def close(self) -> None:
        """释放本服务自建的会话（幂等）；外部注入的会话由注入方关闭。"""
        if not self._owns_db:
            return
        db, self.db = self.db, None
        if db is not None:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"关闭数据库会话失败: {e}")

    def __enter__(self) -> "FilterService":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def filter_by_length(
        self, min_length: int = 1, max_length: int | None = None
    ) -> list[dict[str, Any]]:
        """根据词长过滤"""
        try:
            # 使用自己的数据库会话
            db = self.db
            repo = WordRepository(db)

            all_words = repo.get_all()
            filtered = []

            for word in all_words:
                length = len(word.word)
                if length >= min_length and (
                    max_length is None or length <= max_length
                ):
                    filtered.append(
                        {"word": word.word, "code": word.code, "weight": word.weight}
                    )

            return filtered
        except Exception as e:
            logger.error(f"根据词长过滤失败: {e}")
            raise DictError(f"根据词长过滤失败: {e}") from e

    def filter_by_weight(
        self, min_weight: float = 0.0, max_weight: float | None = None
    ) -> list[dict[str, Any]]:
        """根据权重过滤"""
        try:
            # 使用自己的数据库会话
            db = self.db
            repo = WordRepository(db)

            all_words = repo.get_all()
            filtered = []

            for word in all_words:
                if word.weight >= min_weight and (
                    max_weight is None or word.weight <= max_weight
                ):
                    filtered.append(
                        {"word": word.word, "code": word.code, "weight": word.weight}
                    )

            return filtered
        except Exception as e:
            logger.error(f"根据权重过滤失败: {e}")
            raise DictError(f"根据权重过滤失败: {e}") from e

    def filter_by_pattern(self, pattern: str) -> list[dict[str, Any]]:
        """根据模式过滤"""
        try:
            # 使用自己的数据库会话
            db = self.db
            repo = WordRepository(db)

            db_words = repo.search(pattern)
            return [
                {"word": word.word, "code": word.code, "weight": word.weight}
                for word in db_words
            ]
        except Exception as e:
            logger.error(f"根据模式过滤失败: {e}")
            raise DictError(f"根据模式过滤失败: {e}") from e

    def import_from_txt(
        self,
        file_path: str,
        encoding: str = "utf-8",
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> dict[str, Any]:
        """从TXT文件导入"""
        import pathlib
        import time

        from app.core.config_manager import ConfigManager

        start_time = time.time()

        try:
            # 规范化路径，防止路径遍历攻击
            file_path = str(pathlib.Path(file_path).resolve())
            if not os.path.exists(file_path):
                raise FileError(f"文件不存在: {file_path}")

            # 获取配置的分隔符，默认为 Tab
            config_manager = ConfigManager()
            separator = config_manager.get("separator", "\t")

            # 先计算文件总行数（包括空行和注释行），用于进度显示
            total_lines = 0
            with open(file_path, encoding=encoding) as f:
                for _ in f:
                    total_lines += 1

            # 扫描文件并处理内容
            words = []
            processed_lines = 0
            valid_lines = 0

            with open(file_path, encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    processed_lines += 1

                    if not line or line.startswith("#"):
                        # 跳过空行和注释行
                        if progress_callback and total_lines > 0:
                            progress = int((processed_lines / total_lines) * 50)
                            progress_callback(
                                progress, f"处理文件: {os.path.basename(file_path)}"
                            )
                        continue

                    parts = line.split(separator)
                    if len(parts) >= 2:
                        word = parts[0]
                        code = parts[1]
                        weight = float(parts[2]) if len(parts) >= 3 else 1.0

                        words.append({"word": word, "code": code, "weight": weight})
                        valid_lines += 1

                    if progress_callback and total_lines > 0:
                        # 文件读取阶段只占用0-50%的进度
                        progress = int((processed_lines / total_lines) * 50)
                        progress_callback(
                            progress, f"处理文件: {os.path.basename(file_path)}"
                        )

            # 如果没有有效行，返回空结果
            if valid_lines == 0:
                return {"added": 0, "existing": 0, "existing_pairs": []}

            # 批量添加
            from app.services.dict import DictService

            # 使用自己的数据库会话
            db = self.db
            # dict_service 内部 CodeGenerator 的会话由 dict_service.close() 释放；
            # 这里注入的 db 归本服务（或注入方）所有，close() 不会动它。
            dict_service = DictService(db)

            # 传递进度回调，调整进度范围为50-100%
            def batch_progress_callback(progress: int, message: str) -> None:
                # 将批量添加的进度映射到50-100%的范围
                adjusted_progress = 50 + int(progress * 0.5)
                if progress_callback:
                    progress_callback(adjusted_progress, message)

            try:
                result = dict_service.add_words(
                    words, progress_callback=batch_progress_callback
                )
            finally:
                dict_service.close()

            # 计算耗时和每千条平均耗时
            end_time = time.time()
            total_time = end_time - start_time
            added_count = result.get("added", 0)
            avg_time_per_1000 = (
                (total_time / added_count * 1000) if added_count > 0 else 0
            )

            # 添加耗时信息到结果
            result["total_time"] = total_time
            result["avg_time_per_1000"] = avg_time_per_1000
            result["total_count"] = len(words)

            if progress_callback:
                progress_callback(95, f"导入完成: {os.path.basename(file_path)}")

            # 数据导入完成后创建索引并优化数据库
            from app.dal.init_db import create_indexes, optimize_database

            create_indexes()
            optimize_database()

            if progress_callback:
                progress_callback(100, "数据库优化完成")

            return result
        except FileError:
            raise
        except Exception as e:
            logger.error(f"从TXT文件导入失败: {e}")
            raise FileError(f"从TXT文件导入失败: {e}") from e

    def import_from_csv(
        self,
        file_path: str,
        encoding: str = "utf-8",
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> dict[str, Any]:
        """从CSV文件导入"""
        import pathlib
        import time

        start_time = time.time()

        try:
            # 规范化路径，防止路径遍历攻击
            file_path = str(pathlib.Path(file_path).resolve())
            if not os.path.exists(file_path):
                raise FileError(f"文件不存在: {file_path}")

            # 先计算文件行数，用于进度显示
            total_rows = 0
            with open(file_path, encoding=encoding) as f:
                reader = csv.DictReader(f)
                for _row in reader:
                    total_rows += 1

            words = []
            processed_rows = 0

            with open(file_path, encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    word = row.get("word") or row.get("词")
                    code = row.get("code") or row.get("编码")
                    weight = float(row.get("weight", 1.0) or row.get("权重", 1.0))

                    if word and code:
                        words.append({"word": word, "code": code, "weight": weight})

                    processed_rows += 1
                    if progress_callback and total_rows > 0:
                        # 文件读取阶段只占用0-50%的进度
                        progress = int((processed_rows / total_rows) * 50)
                        progress_callback(
                            progress, f"处理文件: {os.path.basename(file_path)}"
                        )

            # 批量添加
            from app.services.dict import DictService

            # 使用自己的数据库会话
            db = self.db
            # dict_service 内部 CodeGenerator 的会话由 dict_service.close() 释放；
            # 这里注入的 db 归本服务（或注入方）所有，close() 不会动它。
            dict_service = DictService(db)

            # 传递进度回调，调整进度范围为50-100%
            def batch_progress_callback(progress: int, message: str) -> None:
                # 将批量添加的进度映射到50-100%的范围
                adjusted_progress = 50 + int(progress * 0.5)
                if progress_callback:
                    progress_callback(adjusted_progress, message)

            try:
                result = dict_service.add_words(
                    words, progress_callback=batch_progress_callback
                )
            finally:
                dict_service.close()

            # 计算耗时和每千条平均耗时
            end_time = time.time()
            total_time = end_time - start_time
            added_count = result.get("added", 0)
            avg_time_per_1000 = (
                (total_time / added_count * 1000) if added_count > 0 else 0
            )

            # 添加耗时信息到结果
            result["total_time"] = total_time
            result["avg_time_per_1000"] = avg_time_per_1000
            result["total_count"] = len(words)

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
            raise FileError(f"从CSV文件导入失败: {e}") from e

    def import_from_json(
        self,
        file_path: str,
        encoding: str = "utf-8",
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> dict[str, Any]:
        """从JSON文件导入"""
        import pathlib
        import time

        start_time = time.time()

        try:
            # 规范化路径，防止路径遍历攻击
            file_path = str(pathlib.Path(file_path).resolve())
            if not os.path.exists(file_path):
                raise FileError(f"文件不存在: {file_path}")

            with open(file_path, encoding=encoding) as f:
                data = json.load(f)

            words = []
            total_items = len(data) if isinstance(data, list) else 0
            processed_items = 0

            if isinstance(data, list):
                for item in data:
                    word = item.get("word") or item.get("词")
                    code = item.get("code") or item.get("编码")
                    weight = float(item.get("weight", 1.0) or item.get("权重", 1.0))

                    if word and code:
                        words.append({"word": word, "code": code, "weight": weight})

                    processed_items += 1
                    if progress_callback and total_items > 0:
                        # 文件读取阶段只占用0-50%的进度
                        progress = int((processed_items / total_items) * 50)
                        progress_callback(
                            progress, f"处理文件: {os.path.basename(file_path)}"
                        )

            # 批量添加
            from app.services.dict import DictService

            # 使用自己的数据库会话
            db = self.db
            # dict_service 内部 CodeGenerator 的会话由 dict_service.close() 释放；
            # 这里注入的 db 归本服务（或注入方）所有，close() 不会动它。
            dict_service = DictService(db)

            # 传递进度回调，调整进度范围为50-100%
            def batch_progress_callback(progress: int, message: str) -> None:
                # 将批量添加的进度映射到50-100%的范围
                adjusted_progress = 50 + int(progress * 0.5)
                if progress_callback:
                    progress_callback(adjusted_progress, message)

            try:
                result = dict_service.add_words(
                    words, progress_callback=batch_progress_callback
                )
            finally:
                dict_service.close()

            # 计算耗时和每千条平均耗时
            end_time = time.time()
            total_time = end_time - start_time
            added_count = result.get("added", 0)
            avg_time_per_1000 = (
                (total_time / added_count * 1000) if added_count > 0 else 0
            )

            # 添加耗时信息到结果
            result["total_time"] = total_time
            result["avg_time_per_1000"] = avg_time_per_1000
            result["total_count"] = len(words)

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
            raise FileError(f"从JSON文件导入失败: {e}") from e

    def export_to_txt(
        self,
        output_file: str,
        words: list[dict[str, Any]] | None = None,
        encoding: str = "utf-8",
    ) -> int:
        """导出到TXT文件"""
        import pathlib

        from app.core.config_manager import ConfigManager

        try:
            # 规范化路径，防止路径遍历攻击
            output_file = str(pathlib.Path(output_file).resolve())

            # 获取配置的分隔符，默认为 Tab
            config_manager = ConfigManager()
            separator = config_manager.get("separator", "\t")

            if words is None:
                # 使用自己的数据库会话
                db = self.db
                repo = WordRepository(db)
                # 获取所有词
                all_words = repo.get_all()
                words = [
                    {"word": word.word, "code": word.code, "weight": word.weight}
                    for word in all_words
                ]

            with open(output_file, "w", encoding=encoding) as f:
                for word in words:
                    f.write(
                        f"{word['word']}{separator}{word['code']}{separator}{word['weight']}\n"
                    )

            return len(words)
        except Exception as e:
            logger.error(f"导出到TXT文件失败: {e}")
            raise FileError(f"导出到TXT文件失败: {e}") from e

    def export_to_csv(
        self,
        output_file: str,
        words: list[dict[str, Any]] | None = None,
        encoding: str = "utf-8",
    ) -> int:
        """导出到CSV文件"""
        import pathlib

        try:
            # 规范化路径，防止路径遍历攻击
            output_file = str(pathlib.Path(output_file).resolve())

            if words is None:
                # 使用自己的数据库会话
                db = self.db
                repo = WordRepository(db)
                # 获取所有词
                all_words = repo.get_all()
                words = [
                    {"word": word.word, "code": word.code, "weight": word.weight}
                    for word in all_words
                ]

            with open(output_file, "w", newline="", encoding=encoding) as f:
                fieldnames = ["word", "code", "weight"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(words)

            return len(words)
        except Exception as e:
            logger.error(f"导出到CSV文件失败: {e}")
            raise FileError(f"导出到CSV文件失败: {e}") from e

    def export_to_json(
        self,
        output_file: str,
        words: list[dict[str, Any]] | None = None,
        encoding: str = "utf-8",
    ) -> int:
        """导出到JSON文件"""
        import pathlib

        try:
            # 规范化路径，防止路径遍历攻击
            output_file = str(pathlib.Path(output_file).resolve())

            if words is None:
                # 使用自己的数据库会话
                db = self.db
                repo = WordRepository(db)
                # 获取所有词
                all_words = repo.get_all()
                words = [
                    {"word": word.word, "code": word.code, "weight": word.weight}
                    for word in all_words
                ]

            with open(output_file, "w", encoding=encoding) as f:
                json.dump(words, f, ensure_ascii=False, indent=2)

            return len(words)
        except Exception as e:
            logger.error(f"导出到JSON文件失败: {e}")
            raise FileError(f"导出到JSON文件失败: {e}") from e

    def import_from_thuocl(
        self,
        data_dir: str,
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> dict[str, Any]:
        """从词频数据目录导入

        读取 data/ 下所有词频文件，格式为 "词\t词频"。
        词频取对数 log10(词频) 作为权重，code 自动生成。
        """
        import math
        import pathlib
        import time

        start_time = time.time()

        try:
            data_dir = str(pathlib.Path(data_dir).resolve())
            if not os.path.isdir(data_dir):
                raise FileError(f"目录不存在: {data_dir}")

            if progress_callback:
                progress_callback(5, "加载词频数据...")

            # 加载所有词频数据
            from app.services.thuocl import load_thuocl_data

            freq_dict = load_thuocl_data(data_dir)

            if not freq_dict:
                return {"added": 0, "existing": 0, "existing_pairs": []}

            if progress_callback:
                progress_callback(20, f"已加载 {len(freq_dict)} 条词频数据")

            # 构造词条列表：word + code(自动生成) + weight(log10(词频))
            words = []
            for word, freq in freq_dict.items():
                if freq <= 0:
                    continue
                weight = math.log10(freq)
                words.append(
                    {
                        "word": word,
                        "code": None,  # 自动生成
                        "weight": weight,
                    }
                )

            if progress_callback:
                progress_callback(30, f"准备导入 {len(words)} 个词条...")

            # 批量添加
            from app.services.dict import DictService

            db = self.db
            # dict_service 内部 CodeGenerator 的会话由 dict_service.close() 释放；
            # 这里注入的 db 归本服务（或注入方）所有，close() 不会动它。
            dict_service = DictService(db)

            def batch_progress_callback(progress: int, message: str) -> None:
                adjusted_progress = 30 + int(progress * 0.65)
                if progress_callback:
                    progress_callback(adjusted_progress, message)

            try:
                result = dict_service.add_words(
                    words, progress_callback=batch_progress_callback
                )
            finally:
                dict_service.close()

            end_time = time.time()
            total_time = end_time - start_time
            added_count = result.get("added", 0)
            result["total_time"] = total_time
            result["avg_time_per_1000"] = (
                (total_time / added_count * 1000) if added_count > 0 else 0
            )
            result["total_count"] = len(words)

            if progress_callback:
                progress_callback(95, "词频导入完成")

            from app.dal.init_db import create_indexes, optimize_database

            create_indexes()
            optimize_database()

            if progress_callback:
                progress_callback(100, "数据库优化完成")

            return result
        except FileError:
            raise
        except Exception as e:
            logger.error(f"从词频数据导入失败: {e}")
            raise FileError(f"从词频数据导入失败: {e}") from e

    def _import_file_in_own_session(
        self,
        file_path: str,
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> dict[str, Any]:
        """在**当前线程**内自建 FilterService（与会话）导入单个文件，用完即关。

        专供 :meth:`batch_import` 的线程池使用。并发任务必须各持自己的 Session：
        共用同一个 ``self.db`` 会让多线程在同一个 Session 上交错事务（T11-F2 实测
        6/6 文件失败、落库 39/240，异常 ``This transaction is closed`` /
        ``sqlite3.InterfaceError``）。

        分层约束：``app/services/`` 不得反向依赖 ``ui/gui/threads/service_factory.py``，
        故这里就地按 T5/T20 的显式所有权模型创建与释放（谁创建、谁 ``close()``）。
        """
        service = FilterService()
        try:
            if file_path.endswith(".txt"):
                return service.import_from_txt(file_path, "utf-8", progress_callback)
            if file_path.endswith(".csv"):
                return service.import_from_csv(file_path, "utf-8", progress_callback)
            if file_path.endswith(".json"):
                return service.import_from_json(file_path, "utf-8", progress_callback)
            raise FileError(f"不支持的文件类型: {file_path}")
        finally:
            service.close()

    def batch_import(
        self,
        directory: str,
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> dict[str, Any]:
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
                if "/" in filename or "\\" in filename:
                    continue
                file_path = str(pathlib.Path(directory) / filename)
                if os.path.isfile(file_path) and (
                    filename.endswith(".txt")
                    or filename.endswith(".csv")
                    or filename.endswith(".json")
                ):
                    import_files.append(file_path)

            total_files = len(import_files)
            if total_files == 0:
                return {"total_imported": 0, "failed_files": []}

            total_imported = 0
            failed_files = []
            processed_files = 0

            # 多线程处理
            with ThreadPoolExecutor(max_workers=4) as executor:
                # 提交所有导入任务
                future_to_file = {}
                for file_path in import_files:
                    # 每个任务在**自己的工作线程内**自建服务与会话，见
                    # _import_file_in_own_session：并行任务共用 self.db 会让多个
                    # 线程在同一个 Session 上交错事务（T11-F2 实测 6/6 文件失败、
                    # 落库 39/240，异常 This transaction is closed /
                    # sqlite3.InterfaceError: bad parameter or other API misuse）。
                    future = executor.submit(
                        self._import_file_in_own_session, file_path, progress_callback
                    )
                    future_to_file[future] = file_path

                # 处理任务结果
                for future in concurrent.futures.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    filename = os.path.basename(file_path)
                    try:
                        result = future.result()
                        total_imported += result.get("added", 0)
                    except Exception as e:
                        logger.error(f"导入文件 {filename} 失败: {e}")
                        failed_files.append(filename)

                    processed_files += 1
                    if progress_callback and total_files > 0:
                        overall_progress = int((processed_files / total_files) * 100)
                        progress_callback(
                            overall_progress,
                            f"已处理 {processed_files}/{total_files} 个文件",
                        )

            if progress_callback:
                progress_callback(100, "批量导入完成")

            return {"total_imported": total_imported, "failed_files": failed_files}
        except FileError:
            raise
        except Exception as e:
            logger.error(f"批量导入失败: {e}")
            raise FileError(f"批量导入失败: {e}") from e
