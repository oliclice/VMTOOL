from PyQt6.QtCore import QThread, pyqtSignal

from .service_factory import filter_service_scope


class ImportThread(QThread):
    """导入线程（服务实例由本线程创建并释放）"""

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, file_path, format):
        super().__init__()
        self.file_path = file_path
        self.format = format

    def run(self):
        try:

            def progress_callback(progress, message):
                self.progress.emit(progress, message)

            with filter_service_scope() as filter_service:
                if self.format == "txt":
                    result = filter_service.import_from_txt(
                        self.file_path, progress_callback=progress_callback
                    )
                elif self.format == "csv":
                    result = filter_service.import_from_csv(
                        self.file_path, progress_callback=progress_callback
                    )
                elif self.format == "json":
                    result = filter_service.import_from_json(
                        self.file_path, progress_callback=progress_callback
                    )
                else:
                    self.error.emit("不支持的格式")
                    return

            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
