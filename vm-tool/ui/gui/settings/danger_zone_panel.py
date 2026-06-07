"""危险操作面板 - 删除表等不可逆操作"""

from PyQt6.QtWidgets import QPushButton, QMessageBox, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

from .base_panel import SettingsPanel
from ..threads.delete_table_thread import DeleteTableThread, SetAllManualToFalseThread


class DangerZonePanel(SettingsPanel):
    """危险操作面板 - 删除表、重置数据等不可逆操作"""

    panel_name = "危险操作"
    panel_description = "删除表数据等不可逆操作，请谨慎使用"

    def __init__(self, parent=None, dict_service=None):
        self.dict_service = dict_service
        super().__init__(parent)
        # 设置红色警示样式
        self.setStyleSheet("""
            QGroupBox {
                border: 2px solid #ff4444;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #ff4444;
            }
        """)

    def _setup_ui(self):
        # 警告说明
        warning_label = QLabel("⚠️ 以下操作不可逆，请谨慎使用！")
        warning_label.setStyleSheet("color: #ff4444; font-weight: bold; padding: 8px;")
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._main_layout.addWidget(warning_label)

        # 删除表区域
        delete_label = QLabel("删除表数据:")
        delete_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        self._main_layout.addWidget(delete_label)

        self.delete_chars_button = QPushButton("删除字表")
        self.delete_words_button = QPushButton("删除词表")
        self.delete_special_button = QPushButton("删除特殊字符表")

        # 设置删除按钮样式
        delete_button_style = """
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
            QPushButton:pressed {
                background-color: #990000;
            }
        """
        self.delete_chars_button.setStyleSheet(delete_button_style)
        self.delete_words_button.setStyleSheet(delete_button_style)
        self.delete_special_button.setStyleSheet(delete_button_style)

        self.delete_chars_button.clicked.connect(
            lambda: self._delete_table("chars", "字表")
        )
        self.delete_words_button.clicked.connect(
            lambda: self._delete_table("words", "词表")
        )
        self.delete_special_button.clicked.connect(
            lambda: self._delete_table("special", "特殊字符表")
        )

        self._main_layout.addWidget(self.delete_chars_button)
        self._main_layout.addWidget(self.delete_words_button)
        self._main_layout.addWidget(self.delete_special_button)

        # 分隔线
        separator = QLabel("")
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #ff4444;")
        self._main_layout.addWidget(separator)

        # 手动全部为否区域
        manual_label = QLabel("重置手动标记:")
        manual_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        self._main_layout.addWidget(manual_label)

        self.manual_chars_button = QPushButton("字表手动全部为否")
        self.manual_words_button = QPushButton("词表手动全部为否")
        self.manual_special_button = QPushButton("特殊字符表手动全部为否")

        # 设置重置按钮样式
        reset_button_style = """
            QPushButton {
                background-color: #ff8800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc6600;
            }
            QPushButton:pressed {
                background-color: #995500;
            }
        """
        self.manual_chars_button.setStyleSheet(reset_button_style)
        self.manual_words_button.setStyleSheet(reset_button_style)
        self.manual_special_button.setStyleSheet(reset_button_style)

        self.manual_chars_button.clicked.connect(
            lambda: self._set_all_manual_to_false("chars", "字表")
        )
        self.manual_words_button.clicked.connect(
            lambda: self._set_all_manual_to_false("words", "词表")
        )
        self.manual_special_button.clicked.connect(
            lambda: self._set_all_manual_to_false("special", "特殊字符表")
        )

        self._main_layout.addWidget(self.manual_chars_button)
        self._main_layout.addWidget(self.manual_words_button)
        self._main_layout.addWidget(self.manual_special_button)

        # 说明信息
        info_label = QLabel("说明: '手动全部为否'会将所有词条的manual标记重置为False，但不会删除数据。")
        info_label.setStyleSheet("color: gray; font-size: 11px; margin-top: 8px;")
        info_label.setWordWrap(True)
        self._main_layout.addWidget(info_label)

    def _connect_signals(self):
        # 危险操作面板不需要连接配置信号
        pass

    def _get_progress_bar(self):
        """获取进度条组件"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'progress_bar'):
                return parent.progress_bar
            if hasattr(parent, 'progress_bar_widget'):
                return parent.progress_bar_widget
            parent = parent.parent() if hasattr(parent, 'parent') else None
        return None

    def _refresh_tab(self, table_name):
        """刷新指定的标签页"""
        tab_map = {
            "chars": ("chars_tab", "refresh_data"),
            "words": ("words_tab", "refresh_data"),
            "special": ("special_tab", "refresh_data")
        }

        if table_name not in tab_map:
            return

        tab_attr, method_name = tab_map[table_name]
        parent = self.parent()
        while parent:
            if hasattr(parent, tab_attr):
                tab = getattr(parent, tab_attr)
                if hasattr(tab, method_name):
                    getattr(tab, method_name)()
                break
            parent = parent.parent() if hasattr(parent, 'parent') else None

    def _delete_table(self, table_name, table_display_name):
        """删除表（异步）"""
        if not self.dict_service:
            QMessageBox.warning(self, "警告", "词典服务未初始化")
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除{table_display_name}吗？此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 获取进度条
            progress_bar = self._get_progress_bar()
            if progress_bar:
                progress_bar.start_progress(f"正在删除{table_display_name}...")

            # 创建并启动线程
            thread = DeleteTableThread(self.dict_service, table_name, table_display_name)

            def on_progress(progress, message):
                if progress_bar:
                    progress_bar.update_progress(progress, message)

            def on_finished(result):
                if progress_bar:
                    progress_bar.finish_progress(f"删除成功，共删除 {result.get('deleted', 0)} 条记录")
                QMessageBox.information(self, "成功", f"{table_display_name}删除成功")
                # 刷新相关标签页
                self._refresh_tab(table_name)
                # 清理线程
                thread.deleteLater()

            def on_error(error_msg):
                if progress_bar:
                    progress_bar.error_progress(f"删除失败: {error_msg}")
                QMessageBox.critical(self, "错误", f"删除{table_display_name}失败: {error_msg}")
                # 清理线程
                thread.deleteLater()

            thread.progress.connect(on_progress)
            thread.finished.connect(on_finished)
            thread.error.connect(on_error)
            thread.start()

    def _set_all_manual_to_false(self, table_name, table_display_name):
        """将指定表的所有词条的manual设置为False（异步）"""
        if not self.dict_service:
            QMessageBox.warning(self, "警告", "词典服务未初始化")
            return

        reply = QMessageBox.question(
            self,
            "确认操作",
            f"确定要将{table_display_name}的所有词条设置为非手动吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 获取进度条
            progress_bar = self._get_progress_bar()
            if progress_bar:
                progress_bar.start_progress(f"正在更新{table_display_name}...")

            # 创建并启动线程
            thread = SetAllManualToFalseThread(self.dict_service, table_name, table_display_name)

            def on_progress(progress, message):
                if progress_bar:
                    progress_bar.update_progress(progress, message)

            def on_finished(result):
                if progress_bar:
                    progress_bar.finish_progress(f"更新成功，共更新 {result.get('updated', 0)} 条记录")
                QMessageBox.information(self, "成功", f"{table_display_name}更新成功，共更新 {result.get('updated', 0)} 条记录")
                # 刷新相关标签页
                self._refresh_tab(table_name)
                # 清理线程
                thread.deleteLater()

            def on_error(error_msg):
                if progress_bar:
                    progress_bar.error_progress(f"更新失败: {error_msg}")
                QMessageBox.critical(self, "错误", f"更新{table_display_name}失败: {error_msg}")
                # 清理线程
                thread.deleteLater()

            thread.progress.connect(on_progress)
            thread.finished.connect(on_finished)
            thread.error.connect(on_error)
            thread.start()

    def reload(self):
        """危险操作面板不需要重新加载"""
        pass
