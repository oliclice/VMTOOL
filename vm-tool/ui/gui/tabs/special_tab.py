from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QLineEdit, QLabel, QComboBox, QMenu, QInputDialog, 
                             QMessageBox, QDialog, QFormLayout, QTextEdit)
from PyQt6.QtCore import Qt
from app.services.dict import DictService
from ..threads import AddBatchThread

class SpecialTab(QWidget):
    """特殊表管理标签页"""
    def __init__(self, parent=None, dict_service=None):
        super().__init__(parent)
        self.dict_service = dict_service
        self.init_ui()
        self.refresh_special()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.special_search_edit = QLineEdit()
        self.special_search_edit.setPlaceholderText("输入关键词搜索")
        
        # 添加字段选择下拉菜单
        self.special_search_field = QComboBox()
        self.special_search_field.addItems(["特殊字符", "编码", "权重"])
        
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.search_special)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.special_search_edit)
        search_layout.addWidget(self.special_search_field)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        
        # 特殊表表格
        self.special_table = QTableWidget()
        self.special_table.setColumnCount(3)
        self.special_table.setHorizontalHeaderLabels(["特殊字符", "编码", "权重"])
        self.special_table.setSortingEnabled(True)
        self.special_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 设置列宽
        self.special_table.setColumnWidth(0, 150)
        self.special_table.setColumnWidth(1, 150)
        self.special_table.setColumnWidth(2, 100)
        
        # 添加右键菜单
        self.special_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.special_table.customContextMenuRequested.connect(self.show_special_context_menu)
        
        layout.addWidget(self.special_table)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_special)
        
        add_batch_button = QPushButton("批量添加")
        add_batch_button.clicked.connect(self.add_batch_special)
        
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self.delete_special)
        
        update_button = QPushButton("更新")
        update_button.clicked.connect(self.update_special)
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_special)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(add_batch_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(update_button)
        button_layout.addWidget(refresh_button)
        layout.addLayout(button_layout)
    
    def refresh_special(self):
        """刷新特殊表"""
        if not self.dict_service:
            return
        
        try:
            special_chars = self.dict_service.get_special_chars()
            self.special_table.setRowCount(len(special_chars))
            
            for i, char in enumerate(special_chars):
                self.special_table.setItem(i, 0, QTableWidgetItem(char["word"]))
                self.special_table.setItem(i, 1, QTableWidgetItem(char["code"]))
                self.special_table.setItem(i, 2, QTableWidgetItem(str(char["weight"])))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新特殊表失败: {e}")
    
    def search_special(self):
        """搜索特殊表"""
        if not self.dict_service:
            return
        
        keyword = self.special_search_edit.text()
        field = self.special_search_field.currentText()
        
        try:
            special_chars = self.dict_service.search_special_chars(keyword, field)
            self.special_table.setRowCount(len(special_chars))
            
            for i, char in enumerate(special_chars):
                self.special_table.setItem(i, 0, QTableWidgetItem(char["word"]))
                self.special_table.setItem(i, 1, QTableWidgetItem(char["code"]))
                self.special_table.setItem(i, 2, QTableWidgetItem(str(char["weight"])))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {e}")
    
    def add_special(self):
        """添加特殊字符"""
        if not self.dict_service:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("添加特殊字符")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QFormLayout(dialog)
        
        char_edit = QLineEdit()
        char_edit.setPlaceholderText("请输入特殊字符")
        code_edit = QLineEdit()
        code_edit.setPlaceholderText("请输入编码")
        weight_edit = QLineEdit()
        weight_edit.setPlaceholderText("请输入权重")
        weight_edit.setText("1.0")
        
        layout.addRow("特殊字符:", char_edit)
        layout.addRow("编码:", code_edit)
        layout.addRow("权重:", weight_edit)
        
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        cancel_button = QPushButton("取消")
        
        def add_special_confirm():
            char = char_edit.text().strip()
            code = code_edit.text().strip()
            weight = float(weight_edit.text().strip())
            
            if not char:
                QMessageBox.warning(self, "警告", "请输入特殊字符")
                return
            
            try:
                self.dict_service.add_special_char(char, code, weight)
                QMessageBox.information(self, "成功", f"特殊字符 '{char}' 添加成功")
                self.refresh_special()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加失败: {e}")
        
        add_button.clicked.connect(add_special_confirm)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)
        
        dialog.exec()
    
    def add_batch_special(self):
        """批量添加特殊字符"""
        if not self.dict_service:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("批量添加特殊字符")
        dialog.setGeometry(200, 200, 500, 300)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("请输入要添加的特殊字符，每个特殊字符占一行:")
        layout.addWidget(label)
        
        text_edit = QTextEdit()
        layout.addWidget(text_edit)
        
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        cancel_button = QPushButton("取消")
        
        def add_special_chars():
            text = text_edit.toPlainText()
            chars = text.strip().split('\n')
            chars = [c.strip() for c in chars if c.strip()]
            
            if not chars:
                QMessageBox.warning(self, "警告", "请输入要添加的特殊字符")
                return
            
            # 显示确认对话框
            reply = QMessageBox.question(
                self, "确认", f"确定要添加 {len(chars)} 个特殊字符吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 使用统一的进度条
                if self.parent and hasattr(self.parent, 'progress_bar'):
                    progress_bar = self.parent.progress_bar
                    progress_bar.start_progress("正在添加特殊字符...")
                else:
                    progress_bar = None
                
                # 创建并启动线程（保存为实例变量，防止被垃圾回收）
                self.add_batch_thread = AddBatchThread(self.dict_service, chars, is_special=True)
                
                def update_progress(progress, message):
                    if progress_bar:
                        progress_bar.update_progress(progress, message)
                
                def on_finished(result):
                    if progress_bar:
                        progress_bar.finish_progress(f"添加成功，共添加 {result.get('added', 0)} 个特殊字符", success=True)
                    else:
                        if hasattr(self.parent, 'show_toast'):
                            self.parent.show_toast(f"添加成功，共添加 {result.get('added', 0)} 个特殊字符")
                    self.refresh_special()
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
        
        add_button.clicked.connect(add_special_chars)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def delete_special(self):
        """删除特殊字符"""
        if not self.dict_service:
            return
        
        selected_row = self.special_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要删除的特殊字符")
            return
        
        char = self.special_table.item(selected_row, 0).text()
        
        # 显示确认对话框
        reply = QMessageBox.question(
            self, "确认", f"确定要删除 '{char}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.dict_service.delete_special_char(char)
                QMessageBox.information(self, "成功", f"特殊字符 '{char}' 删除成功")
                self.refresh_special()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
    
    def update_special(self):
        """更新特殊字符"""
        if not self.dict_service:
            return
        
        selected_row = self.special_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要更新的特殊字符")
            return
        
        char = self.special_table.item(selected_row, 0).text()
        code = self.special_table.item(selected_row, 1).text()
        weight = self.special_table.item(selected_row, 2).text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("更新特殊字符")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QFormLayout(dialog)
        
        char_edit = QLineEdit(char)
        char_edit.setEnabled(False)  # 特殊字符不可编辑
        code_edit = QLineEdit(code)
        weight_edit = QLineEdit(weight)
        
        layout.addRow("特殊字符:", char_edit)
        layout.addRow("编码:", code_edit)
        layout.addRow("权重:", weight_edit)
        
        button_layout = QHBoxLayout()
        update_button = QPushButton("更新")
        cancel_button = QPushButton("取消")
        
        def update_special_confirm():
            new_code = code_edit.text().strip()
            new_weight = float(weight_edit.text().strip())
            
            try:
                self.dict_service.update_special_char(char, new_code, new_weight)
                QMessageBox.information(self, "成功", f"特殊字符 '{char}' 更新成功")
                self.refresh_special()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新失败: {e}")
        
        update_button.clicked.connect(update_special_confirm)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(update_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)
        
        dialog.exec()
    
    def show_special_context_menu(self, position):
        """显示特殊表右键菜单"""
        if not self.dict_service:
            return
        
        menu = QMenu()
        
        add_action = menu.addAction("添加")
        delete_action = menu.addAction("删除")
        update_action = menu.addAction("更新")
        
        action = menu.exec(self.special_table.mapToGlobal(position))
        
        if action == add_action:
            self.add_special()
        elif action == delete_action:
            self.delete_special()
        elif action == update_action:
            self.update_special()