from PyQt6.QtWidgets import (QPushButton, QLineEdit, QDialog, QFormLayout, QTextEdit, QMessageBox, QTableWidgetItem, QLabel, QHBoxLayout, QVBoxLayout)
from PyQt6.QtCore import Qt
from .base_table_tab import BaseTableTab
from ..threads import AddBatchThread
from ..threads.refresh_data_thread import RefreshDataThread
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

class WordsTab(BaseTableTab):
    """词表管理标签页"""
    def __init__(self, parent=None, dict_service=None):
        self.refresh_thread = None
        self.is_refreshing = False
        super().__init__(parent, dict_service)
    
    def set_column_widths(self):
        """设置列宽"""
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)
    
    def add_extra_buttons(self, layout):
        """添加额外按钮"""
        recalculate_button = QPushButton("批量重新计算编码")
        recalculate_button.clicked.connect(self.recalculate_all_codes)
        layout.addWidget(recalculate_button)
    
    def refresh_data(self):
        """刷新词表（异步）"""
        if not self.dict_service:
            return
        
        # 如果已有刷新操作在进行，显示提示并返回
        if self.is_refreshing or (self.refresh_thread and self.refresh_thread.isRunning()):
            if self.parent and hasattr(self.parent, 'show_toast'):
                self.parent.show_toast("请勿频繁操作")
            return
        
        # 设置刷新状态为True
        self.is_refreshing = True
        
        # 创建并启动刷新线程
        table_type = "words"
        
        # 根据任务类型设置描述
        task_description = {
            "words": "加载词表",
            "chars": "加载字符表",
            "special": "加载特殊字符表"
        }.get(table_type, "加载数据")
        
        # 获取数据总数量
        try:
            if table_type == "words":
                total_count = self.dict_service.count_words()
            elif table_type == "chars":
                total_count = self.dict_service.count_characters()
            elif table_type == "special":
                total_count = self.dict_service.count_special_chars()
            else:
                total_count = 100
        except Exception as e:
            print(f"[WordsTab] 获取数据总数量失败: {e}")
            total_count = 100
        
        # 显示进度条
        if self.parent and hasattr(self.parent, 'progress_bar'):
            self.parent.progress_bar.start_progress(f"正在{task_description}...")
        
        self.refresh_thread = RefreshDataThread(self.dict_service, table_type)
        
        # 创建Rich进度条
        progress = Progress(
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            BarColumn(),
            TextColumn("[progress.completed]{task.completed:.0f}/{task.total:.0f}"),
            TimeElapsedColumn(),
        )
        progress.start()
        task = progress.add_task(f"[cyan]{task_description}", total=total_count)
        
        def on_progress(progress_val, message):
            # 从message中提取实际已加载的数据量
            try:
                # 解析message，提取数字部分
                import re
                match = re.search(r'已加载 (\d+) 条', message)
                if match:
                    actual_completed = int(match.group(1))
                    progress.update(task, completed=actual_completed)
                elif message == "加载完成":
                    # 完成时设置为总数量
                    progress.update(task, completed=total_count)
                else:
                    # 如果解析失败，使用百分比计算
                    actual_completed = int(total_count * (progress_val / 100))
                    progress.update(task, completed=actual_completed)
            except Exception as e:
                # 如果解析失败，使用百分比计算
                actual_completed = int(total_count * (progress_val / 100))
                progress.update(task, completed=actual_completed)
            
            if self.parent and hasattr(self.parent, 'progress_bar'):
                self.parent.progress_bar.update_progress(progress_val, message)
        
        def on_finished(words):
            progress.update(task, completed=total_count)
            progress.stop()
            
            # 优化表格数据更新，避免UI卡顿
            from PyQt6.QtWidgets import QApplication
            
            # 1. 阻塞信号，避免每次 setItem 都触发 cellChanged
            self.table.blockSignals(True)
            
            # 2. 禁用排序，避免插入数据时重新排序
            was_sorted = self.table.isSortingEnabled()
            self.table.setSortingEnabled(False)
            
            # 3. 清空表格
            self.table.setRowCount(0)
            
            # 4. 预分配行数
            total_rows = len(words)
            self.table.setRowCount(total_rows)
            
            # 5. 批量更新表格数据，使用更高效的策略
            batch_size = 1000
            for batch_start in range(0, total_rows, batch_size):
                batch_end = min(batch_start + batch_size, total_rows)
                
                for i in range(batch_start, batch_end):
                    word = words[i]
                    # 使用 setData 而不是创建 QTableWidgetItem，更高效
                    # 第0列：词
                    item_0 = QTableWidgetItem()
                    item_0.setData(Qt.ItemDataRole.DisplayRole, word["word"])
                    self.table.setItem(i, 0, item_0)
                    
                    # 第1列：编码
                    item_1 = QTableWidgetItem()
                    item_1.setData(Qt.ItemDataRole.DisplayRole, word["code"])
                    self.table.setItem(i, 1, item_1)
                    
                    # 第2列：权重
                    item_2 = QTableWidgetItem()
                    item_2.setData(Qt.ItemDataRole.DisplayRole, str(word["weight"]))
                    item_2.setData(Qt.ItemDataRole.EditRole, word["weight"])  # 用于排序
                    self.table.setItem(i, 2, item_2)
                    
                    # 第3列：手动
                    item_3 = QTableWidgetItem()
                    item_3.setData(Qt.ItemDataRole.DisplayRole, "是" if word["manual"] else "否")
                    self.table.setItem(i, 3, item_3)
                
                # 处理事件，避免UI卡顿
                QApplication.processEvents()
            
            # 6. 恢复信号和排序
            self.table.blockSignals(False)
            self.table.setSortingEnabled(was_sorted)
            
            if self.parent and hasattr(self.parent, 'progress_bar'):
                self.parent.progress_bar.finish_progress(f"词表加载完成，共 {total_rows} 条记录")
            
            # 清理线程
            self.refresh_thread.deleteLater()
            self.refresh_thread = None
            # 重置刷新状态
            self.is_refreshing = False
        
        def on_error(error_msg):
            progress.stop()
            if self.parent and hasattr(self.parent, 'progress_bar'):
                self.parent.progress_bar.error_progress(f"加载词表失败: {error_msg}")
            QMessageBox.critical(self, "错误", f"刷新词表失败: {error_msg}")
            
            # 清理线程
            self.refresh_thread.deleteLater()
            self.refresh_thread = None
            # 重置刷新状态
            self.is_refreshing = False
        
        # 连接信号
        self.refresh_thread.progress.connect(on_progress)
        self.refresh_thread.finished.connect(on_finished)
        self.refresh_thread.error.connect(on_error)
        
        # 启动线程
        self.refresh_thread.start()
    
    def search_data(self):
        """搜索词表"""
        if not self.dict_service:
            return
        
        keyword = self.search_edit.text()
        field = self.search_field.currentText()
        
        try:
            words = self.dict_service.search_words(keyword, field)
            self.table.setRowCount(len(words))
            
            for i, word in enumerate(words):
                self.table.setItem(i, 0, QTableWidgetItem(word["word"]))
                self.table.setItem(i, 1, QTableWidgetItem(word["code"]))
                self.table.setItem(i, 2, QTableWidgetItem(str(word["weight"])))
                self.table.setItem(i, 3, QTableWidgetItem("是" if word["manual"] else "否"))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {e}")
    
    def add_item(self):
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
                self.refresh_data()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加失败: {e}")
        
        add_button.clicked.connect(add_word_confirm)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)
        
        dialog.exec()
    
    def add_batch_items(self):
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
        
        add_button.clicked.connect(add_words)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def delete_item(self):
        """删除词"""
        if not self.dict_service:
            return
        
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要删除的词")
            return
        
        word = self.table.item(selected_row, 0).text()
        
        # 显示确认对话框
        reply = QMessageBox.question(
            self, "确认", f"确定要删除 '{word}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.dict_service.delete_word(word)
                QMessageBox.information(self, "成功", f"词 '{word}' 删除成功")
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
    
    def update_item(self):
        """更新词"""
        if not self.dict_service:
            return
        
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要更新的词")
            return
        
        word = self.table.item(selected_row, 0).text()
        code = self.table.item(selected_row, 1).text()
        weight = self.table.item(selected_row, 2).text()
        
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
                self.refresh_data()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新失败: {e}")
        
        update_button.clicked.connect(update_word_confirm)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(update_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)
        
        dialog.exec()
    
    def on_cell_changed(self, row, column):
        """处理词表单元格编辑完成"""
        if self.is_initializing or not self.dict_service:
            return
        
        # 获取词
        word_item = self.table.item(row, 0)
        if not word_item:
            return
        word = word_item.text()
        
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
                    self.dict_service.update_word(word, code=new_value, weight=weight)
                    if hasattr(self.parent, 'show_toast'):
                        self.parent.show_toast(f"词 '{word}' 编码更新成功")
            elif column == 2:  # 权重
                # 获取编码
                code_item = self.table.item(row, 1)
                if code_item:
                    code = code_item.text()
                    weight = float(new_value)
                    self.dict_service.update_word(word, code=code, weight=weight)
                    if hasattr(self.parent, 'show_toast'):
                        self.parent.show_toast(f"词 '{word}' 权重更新成功")
            # 手动列不允许直接编辑，需要通过其他方式处理
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败: {e}")
            # 恢复原始值
            self.refresh_data()
    
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
                self.refresh_data()
            
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