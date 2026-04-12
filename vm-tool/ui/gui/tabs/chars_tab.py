from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QLineEdit, QLabel, QComboBox, QMenu, QInputDialog, 
                             QMessageBox, QDialog, QFormLayout, QTextEdit)
from PyQt6.QtCore import Qt
from app.services.dict import DictService
from ..threads import AddBatchThread

class CharsTab(QWidget):
    """字表管理标签页"""
    def __init__(self, parent=None, dict_service=None):
        super().__init__(parent)
        self.dict_service = dict_service
        self.init_ui()
        self.refresh_chars()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.char_search_edit = QLineEdit()
        self.char_search_edit.setPlaceholderText("输入关键词搜索")
        
        # 添加字段选择下拉菜单
        self.char_search_field = QComboBox()
        self.char_search_field.addItems(["字", "编码", "权重", "手动"])
        
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.search_chars)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.char_search_edit)
        search_layout.addWidget(self.char_search_field)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        
        # 字表表格
        self.char_table = QTableWidget()
        self.char_table.setColumnCount(4)
        self.char_table.setHorizontalHeaderLabels(["字", "编码", "权重", "手动"])
        self.char_table.setSortingEnabled(True)
        self.char_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 设置列宽
        self.char_table.setColumnWidth(0, 100)
        self.char_table.setColumnWidth(1, 150)
        self.char_table.setColumnWidth(2, 100)
        self.char_table.setColumnWidth(3, 80)
        
        # 添加右键菜单
        self.char_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.char_table.customContextMenuRequested.connect(self.show_char_context_menu)
        
        layout.addWidget(self.char_table)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_char)
        
        add_batch_button = QPushButton("批量添加")
        add_batch_button.clicked.connect(self.add_batch_chars)
        
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self.delete_char)
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_chars)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(add_batch_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(refresh_button)
        layout.addLayout(button_layout)
    
    def refresh_chars(self):
        """刷新字表"""
        if not self.dict_service:
            return
        
        try:
            chars = self.dict_service.get_characters()
            self.char_table.setRowCount(len(chars))
            
            for i, char in enumerate(chars):
                self.char_table.setItem(i, 0, QTableWidgetItem(char["word"]))
                self.char_table.setItem(i, 1, QTableWidgetItem(char["code"]))
                self.char_table.setItem(i, 2, QTableWidgetItem(str(char["weight"])))
                self.char_table.setItem(i, 3, QTableWidgetItem("是" if char["manual"] else "否"))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新字表失败: {e}")
    
    def search_chars(self):
        """搜索字表"""
        if not self.dict_service:
            return
        
        keyword = self.char_search_edit.text()
        field = self.char_search_field.currentText()
        
        try:
            chars = self.dict_service.search_characters(keyword, field)
            self.char_table.setRowCount(len(chars))
            
            for i, char in enumerate(chars):
                self.char_table.setItem(i, 0, QTableWidgetItem(char["word"]))
                self.char_table.setItem(i, 1, QTableWidgetItem(char["code"]))
                self.char_table.setItem(i, 2, QTableWidgetItem(str(char["weight"])))
                self.char_table.setItem(i, 3, QTableWidgetItem("是" if char["manual"] else "否"))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {e}")
    
    def add_char(self):
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
                self.refresh_chars()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加失败: {e}")
        
        add_button.clicked.connect(add_char_confirm)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)
        
        dialog.exec()
    
    def add_batch_chars(self):
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
                    self.refresh_chars()
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
    
    def delete_char(self):
        """删除字"""
        if not self.dict_service:
            return
        
        selected_row = self.char_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要删除的字")
            return
        
        char = self.char_table.item(selected_row, 0).text()
        
        # 显示确认对话框
        reply = QMessageBox.question(
            self, "确认", f"确定要删除 '{char}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.dict_service.delete_character(char)
                QMessageBox.information(self, "成功", f"字 '{char}' 删除成功")
                self.refresh_chars()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
    
    def update_char(self):
        """更新字"""
        if not self.dict_service:
            return
        
        selected_row = self.char_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要更新的字")
            return
        
        char = self.char_table.item(selected_row, 0).text()
        code = self.char_table.item(selected_row, 1).text()
        weight = self.char_table.item(selected_row, 2).text()
        
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
                self.refresh_chars()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新失败: {e}")
        
        update_button.clicked.connect(update_char_confirm)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(update_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)
        
        dialog.exec()
    
    def show_char_context_menu(self, position):
        """显示字表右键菜单"""
        if not self.dict_service:
            return
        
        menu = QMenu()
        
        add_action = menu.addAction("添加")
        delete_action = menu.addAction("删除")
        update_action = menu.addAction("编辑")
        
        action = menu.exec(self.char_table.mapToGlobal(position))
        
        if action == add_action:
            self.add_char()
        elif action == delete_action:
            self.delete_char()
        elif action == update_action:
            self.update_char()