from PyQt6.QtWidgets import (QPushButton, QLineEdit, QDialog, QFormLayout, QMessageBox, QTableWidgetItem)
from PyQt6.QtCore import Qt
from .base_table_tab import BaseTableTab
from .refreshable_tab import RefreshableTab


class CharsTab(BaseTableTab, RefreshableTab):
    """字表管理标签页"""
    def __init__(self, parent=None, dict_service=None):
        self.init_refreshable_tab()
        super().__init__(parent, dict_service)
    
    def set_column_widths(self):
        """设置列宽"""
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)

    def add_extra_buttons(self, layout):
        """添加额外按钮"""
        auto_dedupe_button = QPushButton("自动去重")
        auto_dedupe_button.clicked.connect(self.auto_dedupe)
        layout.addWidget(auto_dedupe_button)

    def auto_dedupe(self):
        if not self.dict_service:
            QMessageBox.warning(self, "警告", "词典服务未初始化")
            return

        if hasattr(self, 'dedupe_thread') and self.dedupe_thread and self.dedupe_thread.isRunning():
            QMessageBox.warning(self, "警告", "去重任务正在进行中，请稍后再试")
            return

        reply = QMessageBox.question(
            self, "确认",
            "是否自动去重？\n\n删除规则：\n1. 词相同，编码不同\n2. 较短的编码是较长编码的前缀\n3. 被删除项的manual必须为False",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.parent and hasattr(self.parent, 'progress_bar'):
                progress_bar = self.parent.progress_bar
                progress_bar.start_progress("正在自动去重...")
            else:
                progress_bar = None

            def update_progress(progress, message):
                if progress_bar:
                    progress_bar.update_progress(progress, message)

            def on_finished(result):
                if progress_bar:
                    progress_bar.finish_progress(f"自动去重完成！分析 {result.get('analyzed', 0)} 条，删除 {result.get('deleted', 0)} 条", success=True)
                if hasattr(self.parent, 'show_toast'):
                    self.parent.show_toast(f"自动去重完成！\n分析: {result.get('analyzed', 0)}\n删除: {result.get('deleted', 0)}\n错误: {result.get('errors', 0)}")
                self.refresh_data()
                if self.dedupe_thread:
                    self.dedupe_thread.cleanup()
                    self.dedupe_thread = None

            def on_error(error):
                if progress_bar:
                    progress_bar.error_progress(f"自动去重失败: {error}")
                if hasattr(self.parent, 'show_toast'):
                    self.parent.show_toast(f"自动去重失败: {error}")
                if self.dedupe_thread:
                    self.dedupe_thread.cleanup()
                    self.dedupe_thread = None

            from ..threads import AutoDedupeThread
            self.dedupe_thread = AutoDedupeThread(self.dict_service, "chars")
            self.dedupe_thread.progress.connect(update_progress)
            self.dedupe_thread.finished.connect(on_finished)
            self.dedupe_thread.error.connect(on_error)
            self.dedupe_thread.start()

    def update_table_row(self, table, row, data):
        """更新表格单行数据"""
        char = data
        # 第0列：字
        item_0 = QTableWidgetItem()
        item_0.setData(Qt.ItemDataRole.DisplayRole, char["word"])
        table.setItem(row, 0, item_0)
        
        # 第1列：编码
        item_1 = QTableWidgetItem()
        item_1.setData(Qt.ItemDataRole.DisplayRole, char["code"])
        table.setItem(row, 1, item_1)
        
        # 第2列：权重
        item_2 = QTableWidgetItem()
        item_2.setData(Qt.ItemDataRole.DisplayRole, str(char["weight"]))
        item_2.setData(Qt.ItemDataRole.EditRole, char["weight"])
        table.setItem(row, 2, item_2)
        
        # 第3列：手动
        item_3 = QTableWidgetItem()
        item_3.setData(Qt.ItemDataRole.DisplayRole, "是" if char["manual"] else "否")
        table.setItem(row, 3, item_3)
    
    def refresh_data(self):
        """刷新字表（异步）"""
        if not self.dict_service:
            return
        
        thread = self.create_refresh_thread("chars")
        if not thread:
            return
        
        if self.parent and hasattr(self.parent, 'progress_bar'):
            self.parent.progress_bar.start_progress("正在加载字表...")
        
        self.setup_refresh_callbacks(thread, self.table, "字表加载")
        thread.start()
    
    def search_data(self):
        """搜索字表"""
        if not self.dict_service:
            return
        
        keyword = self.search_edit.text()
        field = self.search_field.currentText()
        
        try:
            chars = self.dict_service.search_characters(keyword, field)
            self.table.setRowCount(len(chars))
            
            for i, char in enumerate(chars):
                self.table.setItem(i, 0, QTableWidgetItem(char["word"]))
                self.table.setItem(i, 1, QTableWidgetItem(char["code"]))
                self.table.setItem(i, 2, QTableWidgetItem(str(char["weight"])))
                self.table.setItem(i, 3, QTableWidgetItem("是" if char["manual"] else "否"))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {e}")
    
    def add_item(self):
        """添加字"""
        if not self.dict_service:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("添加字")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QFormLayout(dialog)
        
        char_edit = QLineEdit()
        char_edit.setPlaceholderText("请输入字")
        code_edit = QLineEdit()
        code_edit.setPlaceholderText("请输入编码")
        weight_edit = QLineEdit()
        weight_edit.setPlaceholderText("请输入权重")
        weight_edit.setText("1.0")
        
        layout.addRow("字:", char_edit)
        layout.addRow("编码:", code_edit)
        layout.addRow("权重:", weight_edit)
        
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        cancel_button = QPushButton("取消")
        
        def add_char_confirm():
            char = char_edit.text().strip()
            code = code_edit.text().strip()
            weight = float(weight_edit.text().strip())
            
            if not char:
                QMessageBox.warning(self, "警告", "请输入字")
                return
            
            try:
                self.dict_service.add_character(char, code, weight, True)
                QMessageBox.information(self, "成功", f"字 '{char}' 添加成功")
                self.refresh_data()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加失败: {e}")
        
        add_button.clicked.connect(add_char_confirm)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)
        
        dialog.exec()
    
    def add_batch_items(self):
        """批量添加汉字"""
        if not self.dict_service:
            return
        
        def add_callback(chars, dialog):
            self.execute_batch_add(chars, dialog, {"is_character": True}, "添加成功，共添加 {} 个汉字")
        
        dialog = self.create_batch_add_dialog(
            "批量添加汉字",
            "请输入要添加的汉字，每个汉字占一行:",
            "添加",
            add_callback
        )
        dialog.exec()
    
    def delete_item(self):
        """删除字"""
        if not self.dict_service:
            return
        
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要删除的字")
            return
        
        char = self.table.item(selected_row, 0).text()
        
        reply = QMessageBox.question(
            self, "确认", f"确定要删除 '{char}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.dict_service.delete_character(char)
                QMessageBox.information(self, "成功", f"字 '{char}' 删除成功")
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
    
    def update_item(self):
        """更新字"""
        if not self.dict_service:
            return
        
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要更新的字")
            return
        
        char = self.table.item(selected_row, 0).text()
        code = self.table.item(selected_row, 1).text()
        weight = self.table.item(selected_row, 2).text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("更新字")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QFormLayout(dialog)
        
        char_edit = QLineEdit(char)
        char_edit.setEnabled(False)
        code_edit = QLineEdit(code)
        weight_edit = QLineEdit(weight)
        
        layout.addRow("字:", char_edit)
        layout.addRow("编码:", code_edit)
        layout.addRow("权重:", weight_edit)
        
        button_layout = QHBoxLayout()
        update_button = QPushButton("更新")
        cancel_button = QPushButton("取消")
        
        def update_char_confirm():
            new_code = code_edit.text().strip()
            new_weight = float(weight_edit.text().strip())
            
            try:
                self.dict_service.update_character(char, new_code, new_weight)
                QMessageBox.information(self, "成功", f"字 '{char}' 更新成功")
                self.refresh_data()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新失败: {e}")
        
        update_button.clicked.connect(update_char_confirm)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(update_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)
        
        dialog.exec()
    
    def on_cell_changed(self, row, column):
        """处理字表单元格编辑完成"""
        if self.is_initializing or not self.dict_service:
            return
        
        char_item = self.table.item(row, 0)
        if not char_item:
            return
        char = char_item.text()
        
        edited_item = self.table.item(row, column)
        if not edited_item:
            return
        new_value = edited_item.text()
        
        try:
            if column == 1:
                weight_item = self.table.item(row, 2)
                if weight_item:
                    weight = float(weight_item.text())
                    self.dict_service.update_character(char, new_value, weight)
                    if hasattr(self.parent, 'show_toast'):
                        self.parent.show_toast(f"字 '{char}' 编码更新成功")
            elif column == 2:
                code_item = self.table.item(row, 1)
                if code_item:
                    code = code_item.text()
                    weight = float(new_value)
                    self.dict_service.update_character(char, code, weight)
                    if hasattr(self.parent, 'show_toast'):
                        self.parent.show_toast(f"字 '{char}' 权重更新成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败: {e}")
            self.refresh_data()
