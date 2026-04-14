from PyQt6.QtCore import QThread, pyqtSignal


class DeleteTableThread(QThread):
    """删除表线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, dict_service, table_name, table_display_name):
        super().__init__()
        self.dict_service = dict_service
        self.table_name = table_name
        self.table_display_name = table_display_name
    
    def run(self):
        """执行删除操作"""
        try:
            self.progress.emit(0, f"正在删除{self.table_display_name}...")
            result = self.dict_service.delete_table(self.table_name)
            self.progress.emit(100, "删除完成")
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class SetAllManualToFalseThread(QThread):
    """设置所有manual为False线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, dict_service, table_name, table_display_name):
        super().__init__()
        self.dict_service = dict_service
        self.table_name = table_name
        self.table_display_name = table_display_name
    
    def run(self):
        """执行设置操作"""
        try:
            self.progress.emit(0, f"正在更新{self.table_display_name}...")
            
            def progress_callback(progress, message):
                self.progress.emit(progress, message)
            
            result = self.dict_service.set_all_manual_to_false(self.table_name, progress_callback)
            self.progress.emit(100, "更新完成")
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
