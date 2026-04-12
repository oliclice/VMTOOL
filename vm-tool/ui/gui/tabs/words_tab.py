from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QLineEdit, QLabel, QComboBox, QMenu, QInputDialog, 
                             QMessageBox, QDialog, QFormLayout, QTextEdit)
from PyQt6.QtCore import Qt
from app.services.dict import DictService
from ..threads import AddBatchThread

class WordsTab(QWidget):
    """词表管理标签页"""
    def __init__(self, parent=None, dict_service=None):
        super().__init__(parent)
        self.dict_service = dict_service
        self.init_ui()
        self.refresh_words()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.word_search_edit = QLineEdit()
        self.word_search_edit.setPlaceholderText("输入关键词搜索")
        
        # 添加字段选择下拉菜单
        self.word_search_field = QComboBox()
        self.word_search_field.addItems(["词", "编码", "权重", "手动"])
        
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.search_words)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.word_search_edit)
        search_layout.addWidget(self.word_search_field)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        
        # 词表表格
        self.word_table = QTableWidget()
        self.word_table.setColumnCount(4)
        self.word_table.setHorizontalHeaderLabels(["词", "编码", "权重", "手动"])
        self.word_table.setSortingEnabled(True)
        self.word_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 设置列宽
        self.word_table.setColumnWidth(0, 200)
        self.word_table.setColumnWidth(1, 150)
        self.word_table.setColumnWidth(2, 100)
        self.word_table.setColumnWidth(3, 80)
        
        # 添加右键菜单
        self.word_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.word_table.customContextMenuRequested.connect(self.show_word_context_menu)
        
        layout.addWidget(self.word_table)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_word)
        
        add_batch_button = QPushButton("批量添加")
        add_batch_button.clicked.connect(self.add_batch_words)
        
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self.delete_word)
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_words)
        
        recalculate_button = QPushButton("批量重新计算编码")
        recalculate_button.clicked.connect(self.recalculate_all_codes)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(add_batch_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(recalculate_button)
        layout.addLayout(button_layout)
    
    def refresh_words(self):
        """刷新词表"""
        if not self.dict_service:
            return
        
        try:
            words = self.dict_service.get_words()
            self.word_table.setRowCount(len(words))
            
            for i, word in enumerate(words):
                self.word_table.setItem(i, 0, QTableWidgetItem(word["word"]))
                self.word_table.setItem(i, 1, QTableWidgetItem(word["code"]))
                self.word_table.setItem(i, 2, QTableWidgetItem(str(word["weight"])))
                self.word_table.setItem(i, 3, QTableWidgetItem("是" if word["manual"] else "否"))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新词表失败: {e}")
    
    def search_words(self):
        """搜索词表"""
        if not self.dict_service:
            return
        
        keyword = self.word_search_edit.text()
        field = self.word_search_field.currentText()
        
        try:
            words = self.dict_service.search_words(keyword, field)
            self.word_table.setRowCount(len(words))
            
            for i, word in enumerate(words):
                self.word_table.setItem(i, 0, QTableWidgetItem(word["word"]))
                self.word_table.setItem(i, 1, QTableWidgetItem(word["code"]))
                self.word_table.setItem(i, 2, QTableWidgetItem(str(word["weight"])))
                self.word_table.setItem(i, 3, QTableWidgetItem("是" if word["manual"] else "否"))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {e}")
    
    def add_word(self):
        """添加词"""
        if not self.dict_service:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("添加词")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QFormLayout(dialog)
        
        word_edit = QLineEdit()
        word_edit.setPlaceholderText("请输入词")
        code_edit = QLineEdit()
        code_edit.setPlaceholderText("请输入编码")
        weight_edit = QLineEdit()
        weight_edit.setPlaceholderText("请输入权重")
        weight_edit.setText("1.0")
        
        layout.addRow("词:", word_edit)
        layout.addRow("编码:", code_edit)
        layout.addRow("权重:", weight_edit)
        
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        cancel_button = QPushButton("取消")
        
        def add_word_confirm():
            word = word_edit.text().strip()
            code = code_edit.text().strip()
            weight = float(weight_edit.text().strip())
            
            if not word:
                QMessageBox.warning(self, "警告", "请输入词")
                return
            
            try:
                self.dict_service.add_word(word, code, weight, True)
                QMessageBox.information(self, "成功", f"词 '{word}' 添加成功")
                self.refresh_words()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加失败: {e}")
        
        add_button.clicked.connect(add_word_confirm)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)
        
        dialog.exec()
    
    def add_batch_words(self):
        """批量添加词"""
        if not self.dict_service:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("批量添加词")
        dialog.setGeometry(200, 200, 500, 300)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("请输入要添加的词，每个词占一行:")
        layout.addWidget(label)
        
        text_edit = QTextEdit()
        layout.addWidget(text_edit)
        
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        cancel_button = QPushButton("取消")
        
        def add_words():
            text = text_edit.toPlainText()
            words = text.strip().split('\n')
            words = [w.strip() for w in words if w.strip()]
            
            if not words:
                QMessageBox.warning(self, "警告", "请输入要添加的词")
                return
            
            # 显示确认对话框
            reply = QMessageBox.question(
                self, "确认", f"确定要添加 {len(words)} 个词吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 使用统一的进度条
                if self.parent and hasattr(self.parent, 'progress_bar'):
                    progress_bar = self.parent.progress_bar
                    progress_bar.start_progress("正在添加词...")
                else:
                    progress_bar = None
                
                # 创建并启动线程（保存为实例变量，防止被垃圾回收）
                self.add_batch_thread = AddBatchThread(self.dict_service, words, is_character=False)
                
                def update_progress(progress, message):
                    if progress_bar:
                        progress_bar.update_progress(progress, message)
                
                def on_finished(result):
                    if progress_bar:
                        progress_bar.finish_progress(f"添加成功，共添加 {result.get('added', 0)} 个词", success=True)
                    else:
                        if hasattr(self.parent, 'show_toast'):
                            self.parent.show_toast(f"添加成功，共添加 {result.get('added', 0)} 个词")
                    self.refresh_words()
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
        
        add_button.clicked.connect(add_words)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def delete_word(self):
        """删除词"""
        if not self.dict_service:
            return
        
        selected_row = self.word_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要删除的词")
            return
        
        word = self.word_table.item(selected_row, 0).text()
        
        # 显示确认对话框
        reply = QMessageBox.question(
            self, "确认", f"确定要删除 '{word}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.dict_service.delete_word(word)
                QMessageBox.information(self, "成功", f"词 '{word}' 删除成功")
                self.refresh_words()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
    
    def update_word(self):
        """更新词"""
        if not self.dict_service:
            return
        
        selected_row = self.word_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要更新的词")
            return
        
        word = self.word_table.item(selected_row, 0).text()
        code = self.word_table.item(selected_row, 1).text()
        weight = self.word_table.item(selected_row, 2).text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("更新词")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QFormLayout(dialog)
        
        word_edit = QLineEdit(word)
        word_edit.setEnabled(False)  # 词不可编辑
        code_edit = QLineEdit(code)
        weight_edit = QLineEdit(weight)
        
        layout.addRow("词:", word_edit)
        layout.addRow("编码:", code_edit)
        layout.addRow("权重:", weight_edit)
        
        button_layout = QHBoxLayout()
        update_button = QPushButton("更新")
        cancel_button = QPushButton("取消")
        
        def update_word_confirm():
            new_code = code_edit.text().strip()
            new_weight = float(weight_edit.text().strip())
            
            try:
                self.dict_service.update_word(word, new_code, new_weight)
                QMessageBox.information(self, "成功", f"词 '{word}' 更新成功")
                self.refresh_words()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新失败: {e}")
        
        update_button.clicked.connect(update_word_confirm)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(update_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)
        
        dialog.exec()
    
    def show_word_context_menu(self, position):
        """显示词表右键菜单"""
        if not self.dict_service:
            return
        
        menu = QMenu()
        
        add_action = menu.addAction("添加")
        delete_action = menu.addAction("删除")
        update_action = menu.addAction("编辑")
        
        action = menu.exec(self.word_table.mapToGlobal(position))
        
        if action == add_action:
            self.add_word()
        elif action == delete_action:
            self.delete_word()
        elif action == update_action:
            self.update_word()
    
    def recalculate_all_codes(self):
        """批量重新计算编码"""
        if not self.dict_service:
            QMessageBox.warning(self, "警告", "词典服务未初始化")
            return
        
        # 确认操作
        reply = QMessageBox.question(
            self, "确认", 
            "是否批量重新计算所有未手动修改过编码的词条的编码？\n\n" 
            "注意：这会使用当前设置的编码规则重新计算所有自动编码的词条。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 使用统一的进度条
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
                
                # 显示结果
                if hasattr(self.parent, 'show_toast'):
                    self.parent.show_toast(
                        f"批量重新计算编码完成！\n" 
                        f"总词条数: {result.get('total', 0)}\n" 
                        f"成功更新: {result.get('updated', 0)}\n" 
                        f"更新失败: {result.get('failed', 0)}"
                    )
                
                # 刷新词表
                self.refresh_words()
            
            def on_error(error):
                if progress_bar:
                    progress_bar.error_progress(f"批量重新计算编码失败: {error}")
                if hasattr(self.parent, 'show_toast'):
                    self.parent.show_toast(f"批量重新计算编码失败: {error}")
            
            # 创建并启动线程
            from ..threads import CalculateThread
            self.calculate_thread = CalculateThread(self.dict_service)
            self.calculate_thread.progress.connect(update_progress)
            self.calculate_thread.finished.connect(on_finished)
            self.calculate_thread.error.connect(on_error)
            self.calculate_thread.start()