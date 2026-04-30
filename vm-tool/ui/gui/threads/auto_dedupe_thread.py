from PyQt6.QtCore import QThread, pyqtSignal
import logging

logger = logging.getLogger(__name__)


class AutoDedupeThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, dict_service, table_type, batch_size=1000):
        super().__init__()
        self.dict_service = dict_service
        self.table_type = table_type
        self.batch_size = batch_size
        self.setTerminationEnabled(True)

    def run(self):
        try:
            def progress_callback(progress, message):
                self.progress.emit(progress, message)

            self.progress.emit(0, "正在分析数据...")
            result = self.dict_service.auto_dedupe(self.table_type, self.batch_size, progress_callback)
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"[AutoDedupeThread] 自动去重失败: {e}")
            self.error.emit(str(e))

    def cleanup(self):
        if self.isRunning():
            self.quit()
            self.wait(1000)
            if self.isRunning():
                self.terminate()
                self.wait(500)
        self.deleteLater()