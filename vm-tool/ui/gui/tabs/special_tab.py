from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QLineEdit, QLabel, QComboBox, QMenu, QMessageBox,
                             QDialog, QFormLayout)
from PyQt6.QtCore import Qt
from .refreshable_tab import RefreshableTab


class SpecialTab(QWidget, RefreshableTab):
    table_type = "special"
    item_type_name = "特殊字符"

    def __init__(self, parent=None, dict_service=None):
        super().__init__(parent)
        self.dict_service = dict_service
        self.init_refreshable_tab()
        self.init_ui()
        self.refresh_special()

    def init_ui(self):
        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.special_search_edit = QLineEdit()
        self.special_search_edit.setPlaceholderText("输入关键词搜索")

        self.special_search_field = QComboBox()
        self.special_search_field.addItems(["特殊字符", "编码", "权重"])

        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.search_special)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.special_search_edit)
        search_layout.addWidget(self.special_search_field)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        self.special_table = QTableWidget()
        self.special_table.setColumnCount(3)
        self.special_table.setHorizontalHeaderLabels(["特殊字符", "编码", "权重"])
        self.special_table.setSortingEnabled(True)
        self.special_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.special_table.setColumnWidth(0, 150)
        self.special_table.setColumnWidth(1, 150)
        self.special_table.setColumnWidth(2, 100)

        self.special_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.special_table.customContextMenuRequested.connect(self.show_special_context_menu)

        self.special_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked)
        self.special_table.cellChanged.connect(self.on_cell_changed_special)

        layout.addWidget(self.special_table)

        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_special)

        add_batch_button = QPushButton("批量添加")
        add_batch_button.clicked.connect(self.add_batch_special)

        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self.delete_special)

        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_special)

        auto_dedupe_button = QPushButton("自动去重")
        auto_dedupe_button.clicked.connect(self.auto_dedupe)

        button_layout.addWidget(add_button)
        button_layout.addWidget(add_batch_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(auto_dedupe_button)
        layout.addLayout(button_layout)

    def update_table_row(self, table, row, data):
        item_0 = QTableWidgetItem()
        item_0.setData(Qt.ItemDataRole.DisplayRole, data["word"])
        table.setItem(row, 0, item_0)

        item_1 = QTableWidgetItem()
        item_1.setData(Qt.ItemDataRole.DisplayRole, data["code"])
        table.setItem(row, 1, item_1)

        item_2 = QTableWidgetItem()
        item_2.setData(Qt.ItemDataRole.DisplayRole, str(data["weight"]))
        item_2.setData(Qt.ItemDataRole.EditRole, data["weight"])
        table.setItem(row, 2, item_2)

    def refresh_special(self):
        if not self.dict_service:
            return

        thread = self.create_refresh_thread("special")
        if not thread:
            return

        if self.parent and hasattr(self.parent, 'progress_bar'):
            self.parent.progress_bar.start_progress("正在加载特殊表...")

        def on_progress(progress, message):
            if self.parent and hasattr(self.parent, 'progress_bar'):
                self.parent.progress_bar.update_progress(progress, message)

        def on_finished(data):
            self.update_table_data_special(self.special_table, data, "特殊表加载")
            self.cleanup_refresh_thread()

        def on_error(error_msg):
            if self.parent and hasattr(self.parent, 'progress_bar'):
                self.parent.progress_bar.error_progress(f"加载失败: {error_msg}")
            QMessageBox.critical(self, "错误", f"刷新失败: {error_msg}")
            self.cleanup_refresh_thread()

        thread.progress.connect(on_progress)
        thread.finished.connect(on_finished)
        thread.error.connect(on_error)
        thread.start()

    def update_table_data_special(self, table, data, task_description):
        if not data:
            return

        table.blockSignals(True)
        was_sorted = table.isSortingEnabled()
        table.setSortingEnabled(False)

        table.setRowCount(0)
        total_rows = len(data)
        table.setRowCount(total_rows)

        batch_size = 1000
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            for i in range(batch_start, batch_end):
                self.update_table_row(table, i, data[i])
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()

        table.blockSignals(False)
        table.setSortingEnabled(was_sorted)

        if self.parent and hasattr(self.parent, 'progress_bar'):
            self.parent.progress_bar.finish_progress(f"{task_description}完成，共 {total_rows} 条记录")

    def search_special(self):
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
        if not self.dict_service:
            return

        def add_callback(chars, dialog):
            self.execute_batch_add(chars, dialog, {"is_special": True}, "添加成功，共添加 {} 个特殊字符")

        dialog = self.create_batch_add_dialog(
            "批量添加特殊字符",
            "请输入要添加的特殊字符，每个特殊字符占一行:",
            "添加",
            add_callback
        )
        dialog.exec()

    def delete_special(self):
        if not self.dict_service:
            return

        selected_row = self.special_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要删除的特殊字符")
            return

        char = self.special_table.item(selected_row, 0).text()

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
        char_edit.setEnabled(False)
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

    def on_cell_changed_special(self, row, column):
        if not self.dict_service:
            return

        char_item = self.special_table.item(row, 0)
        if not char_item:
            return
        char = char_item.text()

        edited_item = self.special_table.item(row, column)
        if not edited_item:
            return
        new_value = edited_item.text()

        try:
            if column == 1:
                weight_item = self.special_table.item(row, 2)
                if weight_item:
                    weight = float(weight_item.text())
                    self.dict_service.update_special_char(char, new_value, weight)
                    if hasattr(self.parent, 'show_toast'):
                        self.parent.show_toast(f"特殊字符 '{char}' 编码更新成功")
            elif column == 2:
                code_item = self.special_table.item(row, 1)
                if code_item:
                    code = code_item.text()
                    weight = float(new_value)
                    self.dict_service.update_special_char(char, code, weight)
                    if hasattr(self.parent, 'show_toast'):
                        self.parent.show_toast(f"特殊字符 '{char}' 权重更新成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败: {e}")
            self.refresh_special()

    def show_special_context_menu(self, position):
        if not self.dict_service:
            return

        menu = QMenu()

        add_action = menu.addAction("添加")
        delete_action = menu.addAction("删除")
        update_action = menu.addAction("编辑")

        action = menu.exec(self.special_table.mapToGlobal(position))

        if action == add_action:
            self.add_special()
        elif action == delete_action:
            self.delete_special()
        elif action == update_action:
            self.update_special()