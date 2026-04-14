from PyQt6.QtCore import QThread, pyqtSignal


class RefreshDataThread(QThread):
    """刷新数据线程基类"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, dict_service, table_type, batch_size=1000):
        super().__init__()
        self.dict_service = dict_service
        self.table_type = table_type
        self.batch_size = batch_size
    
    def run(self):
        """执行刷新操作"""
        try:
            self.progress.emit(0, "正在加载数据...")
            
            all_data = []
            offset = 0
            
            while True:
                # 分批获取数据
                if self.table_type == "chars":
                    batch = self.dict_service.get_characters(skip=offset, limit=self.batch_size)
                elif self.table_type == "words":
                    batch = self.dict_service.get_words(skip=offset, limit=self.batch_size)
                elif self.table_type == "special":
                    batch = self.dict_service.get_special_chars(skip=offset, limit=self.batch_size)
                else:
                    raise ValueError(f"不支持的表类型: {self.table_type}")
                
                if not batch:
                    break
                
                all_data.extend(batch)
                offset += len(batch)
                
                # 更新进度
                progress = min(90, int(offset / (offset + self.batch_size) * 90))
                self.progress.emit(progress, f"已加载 {offset} 条数据...")
                
                # 如果这批数据少于batch_size，说明已经加载完所有数据
                if len(batch) < self.batch_size:
                    break
            
            self.progress.emit(100, "加载完成")
            self.finished.emit(all_data)
        except Exception as e:
            self.error.emit(str(e))
