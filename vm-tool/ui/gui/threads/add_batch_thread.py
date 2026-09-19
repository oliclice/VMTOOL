from .base_batch_thread import BaseBatchThread


class AddBatchThread(BaseBatchThread):
    """批量添加线程"""

    def process_item(self, item, dict_service):
        """处理单个项（dict_service 为本线程私有实例）"""
        if self.is_character:
            dict_service.add_character(item, "")
        else:
            dict_service.add_word(item, "")
