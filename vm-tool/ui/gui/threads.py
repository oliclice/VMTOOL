from PyQt6.QtCore import QThread, pyqtSignal

class ImportThread(QThread):
    """导入线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, filter_service, file_path, format):
        super().__init__()
        self.filter_service = filter_service
        self.file_path = file_path
        self.format = format
    
    def run(self):
        try:
            def progress_callback(progress, message):
                self.progress.emit(progress, message)
            
            if self.format == "txt":
                result = self.filter_service.import_from_txt(self.file_path, progress_callback=progress_callback)
            elif self.format == "csv":
                result = self.filter_service.import_from_csv(self.file_path, progress_callback=progress_callback)
            elif self.format == "json":
                result = self.filter_service.import_from_json(self.file_path, progress_callback=progress_callback)
            else:
                self.error.emit("不支持的格式")
                return
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AddBatchThread(QThread):
    """批量添加线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, dict_service, items, is_character=False, is_special=False):
        super().__init__()
        self.dict_service = dict_service
        self.items = items
        self.is_character = is_character
        self.is_special = is_special
    
    def run(self):
        try:
            def progress_callback(progress, message):
                self.progress.emit(progress, message)
            
            item_data = []
            for item in self.items:
                item_data.append({"word": item, "code": None, "weight": 1.0, "is_special": self.is_special})
            
            if self.is_character:
                result = self.dict_service.add_characters(item_data, progress_callback=progress_callback)
            else:
                result = self.dict_service.add_words(item_data, progress_callback=progress_callback)
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class CalculateThread(QThread):
    """批量计算编码线程"""
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, dict_service):
        super().__init__()
        self.dict_service = dict_service
    
    def run(self):
        try:
            self.progress_updated.emit(0, "准备计算编码...")
            
            # 定义进度回调函数
            def progress_callback(progress, message):
                self.progress_updated.emit(progress, message)
            
            # 调用计算方法，传递进度回调
            result = self.dict_service.calculate_all_codes(progress_callback)
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))