from PyQt6.QtWidgets import QPushButton, QMessageBox
from .general_table_tab import GeneralTableTab


class WordsTab(GeneralTableTab):
    table_type = "words"
    item_type_name = "词"
    add_extra_button_text = "批量重新计算编码"

    def set_column_widths(self):
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)

    def on_extra_button_clicked(self):
        self.recalculate_all_codes()

    @property
    def search_method(self):
        return self.dict_service.search_words

    @property
    def add_method(self):
        return self.dict_service.add_word

    @property
    def delete_method(self):
        return self.dict_service.delete_word

    @property
    def update_method(self):
        return self.dict_service.update_word

    @property
    def batch_add_params(self):
        return {"is_character": False}

    def recalculate_all_codes(self):
        if not self.dict_service:
            QMessageBox.warning(self, "警告", "词典服务未初始化")
            return

        reply = QMessageBox.question(
            self, "确认",
            "是否批量重新计算所有未手动修改过编码的词条的编码？\n\n"
            "注意：这会使用当前设置的编码规则重新计算所有自动编码的词条。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.parent and hasattr(self.parent, 'progress_bar'):
                progress_bar = self.parent.progress_bar
                progress_bar.start_progress("正在重新计算编码...")
            else:
                progress_bar = None

            def update_progress(progress, message):
                if progress_bar:
                    progress_bar.update_progress(progress, message)

            def on_finished(result):
                if progress_bar:
                    progress_bar.finish_progress(f"批量重新计算编码完成！共处理 {result.get('total', 0)} 个词条", success=True)

                if hasattr(self.parent, 'show_toast'):
                    self.parent.show_toast(
                        f"批量重新计算编码完成！\n"
                        f"总词条数: {result.get('total', 0)}\n"
                        f"成功更新: {result.get('updated', 0)}\n"
                        f"更新失败: {result.get('failed', 0)}"
                    )

                self.refresh_data()

            def on_error(error):
                if progress_bar:
                    progress_bar.error_progress(f"批量重新计算编码失败: {error}")
                if hasattr(self.parent, 'show_toast'):
                    self.parent.show_toast(f"批量重新计算编码失败: {error}")

            from ..threads import CalculateThread
            self.calculate_thread = CalculateThread(self.dict_service)
            self.calculate_thread.progress.connect(update_progress)
            self.calculate_thread.finished.connect(on_finished)
            self.calculate_thread.error.connect(on_error)
            self.calculate_thread.start()