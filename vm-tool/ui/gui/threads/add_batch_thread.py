from .base_batch_thread import BaseBatchThread

class AddBatchThread(BaseBatchThread):
    """批量添加线程"""
    def process_item(self, item):
        """处理单个项"""
        if self.is_character:
            self.dict_service.add_character(item, "")
        else:
            self.dict_service.add_word(item, "")