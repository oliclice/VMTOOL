from PyQt6.QtCore import QThread, pyqtSignal

class CalculateThread(QThread):
    """批量计算编码线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, dict_service):
        super().__init__()
        self.dict_service = dict_service
    
    def run(self):
        try:
            self.progress.emit(0, "准备计算编码...")
            
            # 定义进度回调函数
            def progress_callback(progress, message):
                self.progress.emit(progress, message)
            
            # 调用计算方法，传递进度回调
            result = self.dict_service.calculate_all_codes(progress_callback)
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))