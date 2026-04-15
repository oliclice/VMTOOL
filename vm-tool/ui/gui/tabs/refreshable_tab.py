from PyQt6.QtWidgets import (QDialog, QFormLayout, QTextEdit, QMessageBox, QTableWidgetItem, 
                             QLabel, QHBoxLayout, QVBoxLayout, QApplication)
from PyQt6.QtCore import Qt
from ..threads import AddBatchThread
from ..threads.refresh_data_thread import RefreshDataThread


class RefreshableTab:
    """可刷新标签页混入类，提供通用的刷新和批量添加功能"""
    
    def init_refreshable_tab(self):
        """初始化可刷新标签页的属性"""
        self.refresh_thread = None
        self.is_refreshing = False
    
    def create_refresh_thread(self, table_type):
        """创建刷新线程"""
        if not self.dict_service:
            return None
        
        if self.is_refreshing or (self.refresh_thread and self.refresh_thread.isRunning()):
            if self.parent and hasattr(self.parent, 'show_toast'):
                self.parent.show_toast("请勿频繁操作")
            return None
        
        self.is_refreshing = True
        self.refresh_thread = RefreshDataThread(self.dict_service, table_type)
        return self.refresh_thread
    
    def setup_refresh_callbacks(self, thread, table, task_description, on_finished_callback=None):
        """设置刷新回调函数"""
        def on_progress(progress, message):
            if self.parent and hasattr(self.parent, 'progress_bar'):
                self.parent.progress_bar.update_progress(progress, message)
        
        def on_finished(data):
            self.update_table_data(table, data, task_description)
            if on_finished_callback:
                on_finished_callback(data)
            self.cleanup_refresh_thread()
        
        def on_error(error_msg):
            if self.parent and hasattr(self.parent, 'progress_bar'):
                self.parent.progress_bar.error_progress(f"加载失败: {error_msg}")
            QMessageBox.critical(self, "错误", f"刷新失败: {error_msg}")
            self.cleanup_refresh_thread()
        
        thread.progress.connect(on_progress)
        thread.finished.connect(on_finished)
        thread.error.connect(on_error)
    
    def update_table_data(self, table, data, task_description):
        """更新表格数据（优化版本）"""
        if not data:
            return
        
        # 1. 阻塞信号，避免每次 setItem 都触发 cellChanged
        table.blockSignals(True)
        
        # 2. 禁用排序，避免插入数据时重新排序
        was_sorted = table.isSortingEnabled()
        table.setSortingEnabled(False)
        
        # 3. 清空并预分配行数
        table.setRowCount(0)
        total_rows = len(data)
        table.setRowCount(total_rows)
        
        # 4. 批量更新表格数据
        batch_size = 1000
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            
            for i in range(batch_start, batch_end):
                self.update_table_row(table, i, data[i])
            
            # 处理事件，避免UI卡顿
            QApplication.processEvents()
        
        # 5. 恢复信号和排序
        table.blockSignals(False)
        table.setSortingEnabled(was_sorted)
        
        if self.parent and hasattr(self.parent, 'progress_bar'):
            self.parent.progress_bar.finish_progress(f"{task_description}完成，共 {total_rows} 条记录")
    
    def update_table_row(self, table, row, data):
        """更新表格单行数据，子类可重写"""
        pass
    
    def cleanup_refresh_thread(self):
        """清理刷新线程"""
        if self.refresh_thread:
            self.refresh_thread.deleteLater()
            self.refresh_thread = None
        self.is_refreshing = False
    
    def create_batch_add_dialog(self, title, label_text, add_button_text, add_callback):
        """创建批量添加对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setGeometry(200, 200, 500, 300)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel(label_text)
        layout.addWidget(label)
        
        text_edit = QTextEdit()
        layout.addWidget(text_edit)
        
        button_layout = QHBoxLayout()
        add_button = QPushButton(add_button_text)
        cancel_button = QPushButton("取消")
        
        def on_add():
            text = text_edit.toPlainText()
            items = text.strip().split('\n')
            items = [item.strip() for item in items if item.strip()]
            
            if not items:
                QMessageBox.warning(self, "警告", "请输入要添加的内容")
                return
            
            reply = QMessageBox.question(
                self, "确认", f"确定要添加 {len(items)} 项吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                add_callback(items, dialog)
        
        add_button.clicked.connect(on_add)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        return dialog
    
    def execute_batch_add(self, items, dialog, thread_params, success_message):
        """执行批量添加操作"""
        if self.parent and hasattr(self.parent, 'progress_bar'):
            progress_bar = self.parent.progress_bar
            progress_bar.start_progress("正在添加...")
        else:
            progress_bar = None
        
        self.add_batch_thread = AddBatchThread(self.dict_service, items, **thread_params)
        
        def update_progress(progress, message):
            if progress_bar:
                progress_bar.update_progress(progress, message)
        
        def on_finished(result):
            if progress_bar:
                progress_bar.finish_progress(success_message.format(result.get('added', 0)), success=True)
            else:
                if hasattr(self.parent, 'show_toast'):
                    self.parent.show_toast(success_message.format(result.get('added', 0)))
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
