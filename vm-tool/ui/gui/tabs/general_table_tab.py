from PyQt6.QtWidgets import (QDialog, QFormLayout, QHBoxLayout, QLineEdit, QMessageBox, QTableWidgetItem, QPushButton)
from PyQt6.QtCore import Qt
from .base_table_tab import BaseTableTab
from .refreshable_tab import RefreshableTab


class GeneralTableTab(BaseTableTab, RefreshableTab):
    item_type_name = "项"
    add_extra_button_text = None

    def __init__(self, parent=None, dict_service=None):
        self.init_refreshable_tab()
        super().__init__(parent, dict_service)

    def set_column_widths(self):
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)

    def add_extra_buttons(self, layout):
        if self.add_extra_button_text:
            btn = QPushButton(self.add_extra_button_text)
            btn.clicked.connect(self.on_extra_button_clicked)
            layout.addWidget(btn)

        auto_dedupe_button = QPushButton("自动去重")
        auto_dedupe_button.clicked.connect(self.auto_dedupe)
        layout.addWidget(auto_dedupe_button)

    def on_extra_button_clicked(self):
        pass

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

        item_3 = QTableWidgetItem()
        item_3.setData(Qt.ItemDataRole.DisplayRole, "是" if data["manual"] else "否")
        table.setItem(row, 3, item_3)

    def refresh_data(self):
        if not self.dict_service:
            return

        thread = self.create_refresh_thread(self.table_type)
        if not thread:
            return

        if self.parent and hasattr(self.parent, 'progress_bar'):
            self.parent.progress_bar.start_progress(f"正在加载{self.item_type_name}表...")

        self.setup_refresh_callbacks(thread, self.table, f"{self.item_type_name}表加载")
        thread.start()

    def search_data(self):
        if not self.dict_service:
            return

        keyword = self.search_edit.text()
        field = self.search_field.currentText()

        try:
            items = self.search_method(keyword, field)
            self.table.setRowCount(len(items))

            for i, item in enumerate(items):
                self.table.setItem(i, 0, QTableWidgetItem(item["word"]))
                self.table.setItem(i, 1, QTableWidgetItem(item["code"]))
                self.table.setItem(i, 2, QTableWidgetItem(str(item["weight"])))
                self.table.setItem(i, 3, QTableWidgetItem("是" if item["manual"] else "否"))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {e}")

    def add_item(self):
        if not self.dict_service:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"添加{self.item_type_name}")
        dialog.setGeometry(200, 200, 400, 200)

        layout = QFormLayout(dialog)

        name_edit = QLineEdit()
        name_edit.setPlaceholderText(f"请输入{self.item_type_name}")
        code_edit = QLineEdit()
        code_edit.setPlaceholderText("请输入编码")
        weight_edit = QLineEdit()
        weight_edit.setPlaceholderText("请输入权重")
        weight_edit.setText("1.0")

        layout.addRow(f"{self.item_type_name}:", name_edit)
        layout.addRow("编码:", code_edit)
        layout.addRow("权重:", weight_edit)

        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        cancel_button = QPushButton("取消")

        def add_confirm():
            name = name_edit.text().strip()
            code = code_edit.text().strip()
            weight = float(weight_edit.text().strip())

            if not name:
                QMessageBox.warning(self, "警告", f"请输入{self.item_type_name}")
                return

            try:
                self.add_method(name, code, weight, True)
                QMessageBox.information(self, "成功", f"{self.item_type_name} '{name}' 添加成功")
                self.refresh_data()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加失败: {e}")

        add_button.clicked.connect(add_confirm)
        cancel_button.clicked.connect(dialog.reject)

        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

        dialog.exec()

    def add_batch_items(self):
        if not self.dict_service:
            return

        def add_callback(items, dialog):
            self.execute_batch_add(items, dialog, self.batch_add_params, f"添加成功，共添加 {{}} 个{self.item_type_name}")

        dialog = self.create_batch_add_dialog(
            f"批量添加{self.item_type_name}",
            f"请输入要添加的{self.item_type_name}，每个{self.item_type_name}占一行:",
            "添加",
            add_callback
        )
        dialog.exec()

    def delete_item(self):
        if not self.dict_service:
            return

        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", f"请选择要删除的{self.item_type_name}")
            return

        name = self.table.item(selected_row, 0).text()

        reply = QMessageBox.question(
            self, "确认", f"确定要删除 '{name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.delete_method(name)
                QMessageBox.information(self, "成功", f"{self.item_type_name} '{name}' 删除成功")
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")

    def update_item(self):
        if not self.dict_service:
            return

        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", f"请选择要更新的{self.item_type_name}")
            return

        name = self.table.item(selected_row, 0).text()
        code = self.table.item(selected_row, 1).text()
        weight = self.table.item(selected_row, 2).text()

        dialog = QDialog(self)
        dialog.setWindowTitle(f"更新{self.item_type_name}")
        dialog.setGeometry(200, 200, 400, 200)

        layout = QFormLayout(dialog)

        name_edit = QLineEdit(name)
        name_edit.setEnabled(False)
        code_edit = QLineEdit(code)
        weight_edit = QLineEdit(weight)

        layout.addRow(f"{self.item_type_name}:", name_edit)
        layout.addRow("编码:", code_edit)
        layout.addRow("权重:", weight_edit)

        button_layout = QHBoxLayout()
        update_button = QPushButton("更新")
        cancel_button = QPushButton("取消")

        def update_confirm():
            new_code = code_edit.text().strip()
            new_weight = float(weight_edit.text().strip())

            try:
                self.update_method(name, code=new_code, weight=new_weight)
                QMessageBox.information(self, "成功", f"{self.item_type_name} '{name}' 更新成功")
                self.refresh_data()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新失败: {e}")

        update_button.clicked.connect(update_confirm)
        cancel_button.clicked.connect(dialog.reject)

        button_layout.addWidget(update_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

        dialog.exec()

    def on_cell_changed(self, row, column):
        if self.is_initializing or not self.dict_service:
            return

        name_item = self.table.item(row, 0)
        if not name_item:
            return
        name = name_item.text()

        edited_item = self.table.item(row, column)
        if not edited_item:
            return
        new_value = edited_item.text()

        try:
            if column == 1:
                weight_item = self.table.item(row, 2)
                if weight_item:
                    weight = float(weight_item.text())
                    self.update_method(name, code=new_value, weight=weight)
                    if hasattr(self.parent, 'show_toast'):
                        self.parent.show_toast(f"{self.item_type_name} '{name}' 编码更新成功")
            elif column == 2:
                code_item = self.table.item(row, 1)
                if code_item:
                    code = code_item.text()
                    weight = float(new_value)
                    self.update_method(name, code=code, weight=weight)
                    if hasattr(self.parent, 'show_toast'):
                        self.parent.show_toast(f"{self.item_type_name} '{name}' 权重更新成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新失败: {e}")
            self.refresh_data()