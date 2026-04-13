from PyQt6.QtWidgets import (QPushButton, QLineEdit, QDialog, QFormLayout, QTextEdit, QMessageBox, QTableWidgetItem, QLabel)
from .base_table_tab import BaseTableTab
from ..threads import AddBatchThread

class CharsTab(BaseTableTab):
    """字表管理标签页"""
    def __init__(self, parent=None, dict_service=None):
        super().__init__(parent, dict_service)
    
    def set_column_widths(self):
        """设置列宽"""
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)
    
    def refresh_data(self):
        """刷新字表"""
        if not self.dict_service:
            return
        
        try:
            chars = self.dict_service.get_characters()
            self.table.setRowCount(len(chars))
            
            for i, char in enumerate(chars):
                self.table.setItem(i, 0, QTableWidgetItem(char["word"]))
                self.table.setItem(i, 1, QTableWidgetItem(char["code"]))
                self.table.setItem(i, 2, QTableWidgetItem(str(char["weight"])))
                self.table.setItem(i, 3, QTableWidgetItem("是" if char["manual"] else "否"))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新字表失败: {e}")
    
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
        
        dialog = QDialog(self)
        dialog.setWindowTitle("批量添加汉字")
        dialog.setGeometry(200, 200, 500, 300)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("请输入要添加的汉字，每个汉字占一行:")
        layout.addWidget(label)
        
        text_edit = QTextEdit()
        layout.addWidget(text_edit)
        
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        cancel_button = QPushButton("取消")
        
        def add_chars():
            text = text_edit.toPlainText()
            chars = text.strip().split('\n')
            chars = [c.strip() for c in chars if c.strip()]
            
            if not chars:
                QMessageBox.warning(self, "警告", "请输入要添加的汉字")
                return
            
            # 显示确认对话框
            reply = QMessageBox.question(
                self, "确认", f"确定要添加 {len(chars)} 个汉字吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 使用统一的进度条
                if self.parent and hasattr(self.parent, 'progress_bar'):
                    progress_bar = self.parent.progress_bar
                    progress_bar.start_progress("正在添加汉字...")
                else:
                    progress_bar = None
                
                # 创建并启动线程（保存为实例变量，防止被垃圾回收）
                self.add_batch_thread = AddBatchThread(self.dict_service, chars, is_character=True)
                
                def update_progress(progress, message):
                    if progress_bar:
                        progress_bar.update_progress(progress, message)
                
                def on_finished(result):
                    if progress_bar:
                        progress_bar.finish_progress(f"添加成功，共添加 {result.get('added', 0)} 个汉字", success=True)
                    else:
                        if hasattr(self.parent, 'show_toast'):
                            self.parent.show_toast(f"添加成功，共添加 {result.get('added', 0)} 个汉字")
                    self.refresh_data()
                    dialog.accept()
                
                def on_error(error):
                    if progress_bar:
                        progress_bar.error_progress(f"添加失败：{error}")
                    else:
                        if hasattr(self.parent, 'show_toast'):
                            self.parent.show_toast(f"添加失败：{error}")
                
                self.add_batch_thread.progress.connect(update_progress)
                self.add_batch_thread.finished.connect(on_finished)
                self.add_batch_thread.error.connect(on_error)
                self.add_batch_thread.start()
        
        add_button.clicked.connect(add_chars)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
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
        
        # 显示确认对话框
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
        char_edit.setEnabled(False)  # 字不可编辑
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
        
        # 获取字
        char_item = self.table.item(row, 0)
        if not char_item:
            return
        char = char_item.text()
        
        # 获取编辑后的值
        edited_item = self.table.item(row, column)
        if not edited_item:
            return
        new_value = edited_item.text()
        
        try:
            if column == 1:  # 编码
                # 获取权重
                weight_item = self.table.item(row, 2)
                if weight_item:
                    weight = float(weight_item.text())
                    self.dict_service.update_character(char, new_value, weight)
                    if hasattr(self.parent, 'show_toast'):
                        self.parent.show_toast(f"字 '{char}' 编码更新成功")
            elif column == 2:  # 权重
                # 获取编码
                code_item = self.table.item(row, 1)
                if code_item:
                    code = code_item.text()
                    weight = float(new_value)
                    self.dict_service.update_character(char, code, weight)
                    if hasattr(self.parent, 'show_toast'):
                        self.parent.show_toast(f"字 '{char}' 权重更新成功")
            # 手动列不允许直接编辑，需要通过其他方式处理
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败: {e}")
            # 恢复原始值
            self.refresh_data()