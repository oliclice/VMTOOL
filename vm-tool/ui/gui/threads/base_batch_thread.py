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
            for i, item in enumerate(self.items):
                try:
                    self.process_item(item)
                    self.added += 1
                except Exception as e:
                    self.failed += 1
                    self.progress.emit(int((i + 1) / self.total * 100), f"处理失败: {item} - {str(e)}")
                self.progress.emit(int((i + 1) / self.total * 100), f"处理中: {item} ({i + 1}/{self.total})")
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