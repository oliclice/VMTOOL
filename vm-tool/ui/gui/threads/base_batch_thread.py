from PyQt6.QtCore import QThread, pyqtSignal
from app.services.dict import DictService

class BaseBatchThread(QThread):
    """批量操作线程基类"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, dict_service: DictService, items: list, is_character: bool = False):
        super().__init__()
        self.dict_service = dict_service
        self.items = items
        self.is_character = is_character
        self.total = len(items)
        self.added = 0
        self.failed = 0
    
    def run(self):
        """执行批量操作"""
        try:
            last_progress = -1
            for i, item in enumerate(self.items):
                try:
                    self.process_item(item)
                    self.added += 1
                except Exception as e:
                    self.failed += 1
                    current_progress = int((i + 1) / self.total * 100)
                    if current_progress != last_progress:
                        self.progress.emit(current_progress, f"处理失败: {item} - {str(e)}")
                        last_progress = current_progress
                # 只在进度变化时发射信号，避免过多信号导致GUI卡顿
                current_progress = int((i + 1) / self.total * 100)
                if current_progress != last_progress:
                    self.progress.emit(current_progress, f"处理中: {item} ({i + 1}/{self.total})")
                    last_progress = current_progress
            self.finished.emit({
                "total": self.total,
                "added": self.added,
                "failed": self.failed
            })
        except Exception as e:
            self.error.emit(str(e))
    
    def process_item(self, item):
        """处理单个项，子类必须重写"""
        raise NotImplementedError