from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QLabel, QComboBox, QMessageBox, QFileDialog,
                             QGroupBox, QFormLayout, QRadioButton, QButtonGroup, QFrame, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from app.services.filter import FilterService
from app.core.config_manager import config_manager
import os
from ..threads import ImportThread
from ..theme_colors import get_hint_color, get_info_box_style, get_button_style

class ImportExportTab(QWidget):
    """导入导出标签页"""
    def __init__(self, parent=None, filter_service=None, dict_service=None):
        super().__init__(parent)
        self.filter_service = filter_service
        self.dict_service = dict_service
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 创建标题
        title_label = QLabel("导入导出管理")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 创建分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)
        
        # 导出部分（上侧）
        export_group = QGroupBox("📤 数据导出")
        export_layout = QVBoxLayout(export_group)
        export_layout.setSpacing(12)
        
        # 导出路径
        export_path_form = QFormLayout()
        export_path_form.setSpacing(8)
        
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setText(config_manager.get("default_export_path", "./"))
        self.export_path_edit.setPlaceholderText("选择导出目录")
        self.export_path_edit.setMinimumWidth(350)
        
        def on_export_path_changed(text):
            config_manager.set("default_export_path", text)
            self.update_export_full_path()
        
        self.export_path_edit.textChanged.connect(on_export_path_changed)
        
        export_browse_button = QPushButton("📁 浏览")
        export_browse_button.clicked.connect(self.browse_export_path)
        export_browse_button.setMaximumWidth(100)
        
        export_path_widget = QHBoxLayout()
        export_path_widget.addWidget(self.export_path_edit)
        export_path_widget.addWidget(export_browse_button)
        export_path_form.addRow(QLabel("导出目录:"), export_path_widget)
        
        # 导出格式
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["TXT 文本文件", "CSV 表格文件", "JSON 数据文件"])
        current_format = config_manager.get("default_export_format", "txt")
        format_map = {"txt": "TXT 文本文件", "csv": "CSV 表格文件", "json": "JSON 数据文件"}
        self.export_format_combo.setCurrentText(format_map.get(current_format, "TXT 文本文件"))
        self.export_format_combo.setMinimumWidth(200)
        
        def on_export_format_changed():
            format_text = self.export_format_combo.currentText()
            reverse_map = {"TXT 文本文件": "txt", "CSV 表格文件": "csv", "JSON 数据文件": "json"}
            config_manager.set("default_export_format", reverse_map.get(format_text, "txt"))
            self.update_export_full_path()
        
        self.export_format_combo.currentTextChanged.connect(on_export_format_changed)
        export_path_form.addRow(QLabel("导出格式:"), self.export_format_combo)
        
        export_layout.addLayout(export_path_form)

        # 导出表选择
        export_tables_group = QGroupBox("📋 导出表选择")
        export_tables_layout = QVBoxLayout(export_tables_group)

        tables_tip_label = QLabel("选择要导出的表（不勾选则不导出该表）:")
        hint_color = get_hint_color()
        tables_tip_label.setStyleSheet(f"QLabel {{ color: {hint_color}; }}")
        export_tables_layout.addWidget(tables_tip_label)

        # 从配置加载已选表，默认全选
        saved_tables = config_manager.get("export_tables", ["words", "chars", "special"])

        tables_checkbox_layout = QHBoxLayout()
        self.words_checkbox = QCheckBox("词表 (words)")
        self.chars_checkbox = QCheckBox("字表 (chars)")
        self.special_checkbox = QCheckBox("特殊字符表 (special)")

        self.words_checkbox.setChecked("words" in saved_tables)
        self.chars_checkbox.setChecked("chars" in saved_tables)
        self.special_checkbox.setChecked("special" in saved_tables)

        def on_table_checkbox_changed():
            selected = []
            if self.words_checkbox.isChecked():
                selected.append("words")
            if self.chars_checkbox.isChecked():
                selected.append("chars")
            if self.special_checkbox.isChecked():
                selected.append("special")
            config_manager.set("export_tables", selected)
            self.update_export_full_path()

        self.words_checkbox.stateChanged.connect(on_table_checkbox_changed)
        self.chars_checkbox.stateChanged.connect(on_table_checkbox_changed)
        self.special_checkbox.stateChanged.connect(on_table_checkbox_changed)

        tables_checkbox_layout.addWidget(self.words_checkbox)
        tables_checkbox_layout.addWidget(self.chars_checkbox)
        tables_checkbox_layout.addWidget(self.special_checkbox)
        tables_checkbox_layout.addStretch()

        export_tables_layout.addLayout(tables_checkbox_layout)
        export_layout.addWidget(export_tables_group)

        # 完整导出路径显示
        path_display_group = QGroupBox("📍 完整导出路径")
        path_display_layout = QVBoxLayout(path_display_group)
        
        self.full_export_path_value = QLabel("")
        self.full_export_path_value.setWordWrap(True)
        info_style = get_info_box_style()
        self.full_export_path_value.setStyleSheet(info_style)
        self.full_export_path_value.setMinimumHeight(40)
        path_display_layout.addWidget(self.full_export_path_value)
        
        export_layout.addWidget(path_display_group)
        
        # 导出按钮
        export_button = QPushButton("🚀 开始导出")
        export_style = get_button_style("success")
        export_button.setStyleSheet(export_style)
        export_button.setMinimumHeight(40)
        export_button.clicked.connect(self.export_data)
        export_layout.addWidget(export_button)
        
        export_layout.addStretch()
        
        main_layout.addWidget(export_group)
        
        # 导入部分（下侧）
        import_group = QGroupBox("📥 数据导入")
        import_layout = QVBoxLayout(import_group)
        import_layout.setSpacing(12)
        
        # 导入路径
        import_path_form = QFormLayout()
        import_path_form.setSpacing(8)
        
        self.import_path_edit = QLineEdit()
        self.import_path_edit.setText(config_manager.get("import_path", "./"))
        self.import_path_edit.setPlaceholderText("选择导入文件")
        self.import_path_edit.setMinimumWidth(350)
        
        def on_import_path_changed(text):
            config_manager.set("import_path", text)
        
        self.import_path_edit.textChanged.connect(on_import_path_changed)
        
        import_browse_button = QPushButton("📁 浏览")
        import_browse_button.clicked.connect(self.browse_import_path)
        import_browse_button.setMaximumWidth(100)
        
        import_path_widget = QHBoxLayout()
        import_path_widget.addWidget(self.import_path_edit)
        import_path_widget.addWidget(import_browse_button)
        import_path_form.addRow(QLabel("导入文件:"), import_path_widget)
        
        # 导入格式
        self.import_format_combo = QComboBox()
        self.import_format_combo.addItems(["TXT 文本文件", "CSV 表格文件", "JSON 数据文件"])
        current_import_format = config_manager.get("default_import_format", "txt")
        import_format_map = {"txt": "TXT 文本文件", "csv": "CSV 表格文件", "json": "JSON 数据文件"}
        self.import_format_combo.setCurrentText(import_format_map.get(current_import_format, "TXT 文本文件"))
        self.import_format_combo.setMinimumWidth(200)
        
        def on_import_format_changed():
            format_text = self.import_format_combo.currentText()
            reverse_map = {"TXT 文本文件": "txt", "CSV 表格文件": "csv", "JSON 数据文件": "json"}
            config_manager.set("default_import_format", reverse_map.get(format_text, "txt"))
        
        self.import_format_combo.currentTextChanged.connect(on_import_format_changed)
        import_path_form.addRow(QLabel("导入格式:"), self.import_format_combo)
        
        import_layout.addLayout(import_path_form)
        
        # 导入选项
        import_options_group = QGroupBox("导入选项")
        import_options_layout = QVBoxLayout(import_options_group)
        
        self.overwrite_radio = QRadioButton("覆盖现有数据")
        self.merge_radio = QRadioButton("合并现有数据")
        self.overwrite_radio.setChecked(True)
        
        import_options_layout.addWidget(self.overwrite_radio)
        import_options_layout.addWidget(self.merge_radio)
        import_layout.addWidget(import_options_group)
        
        # 导入按钮
        import_button = QPushButton("🚀 开始导入")
        import_style = get_button_style("primary")
        import_button.setStyleSheet(import_style)
        import_button.setMinimumHeight(40)
        import_button.clicked.connect(self.import_data)
        import_layout.addWidget(import_button)
        
        import_layout.addStretch()
        
        main_layout.addWidget(import_group)
        
        # 初始更新完整导出路径
        self.update_export_full_path()
    
    def browse_import_path(self):
        """浏览导入路径"""
        # 使用Qt内置对话框
        dialog = QFileDialog(self, "选择导入文件", "./")
        dialog.setNameFilter("文本文件 (*.txt);;CSV文件 (*.csv);;JSON文件 (*.json)")
        
        # 调整对话框大小为 1/2 屏幕高，3/5 屏幕宽
        screen = self.screen().geometry()
        dialog.setGeometry(
            screen.width() // 2 - (screen.width() * 3 // 10),
            screen.height() // 2 - (screen.height() // 4),
            screen.width() * 3 // 5,
            screen.height() // 2
        )
        
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            file_path = dialog.selectedFiles()[0]
            self.import_path_edit.setText(file_path)
            config_manager.set("import_path", file_path)
    
    def browse_export_path(self):
        """浏览导出路径"""
        # 使用Qt内置对话框
        dialog = QFileDialog(self, "选择导出目录", "./")
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        # 调整对话框大小为 1/2 屏幕高，3/5 屏幕宽
        screen = self.screen().geometry()
        dialog.setGeometry(
            screen.width() // 2 - (screen.width() * 3 // 10),
            screen.height() // 2 - (screen.height() // 4),
            screen.width() * 3 // 5,
            screen.height() // 2
        )
        
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            directory = dialog.selectedFiles()[0]
            self.export_path_edit.setText(directory)
            config_manager.set("default_export_path", directory)
    
    def import_data(self):
        """导入数据"""
        if not self.filter_service:
            QMessageBox.warning(self, "警告", "过滤服务未初始化")
            return
        
        file_path = self.import_path_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请输入导入路径")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", f"文件不存在：{file_path}")
            return
        
        # 将用户界面选择的格式转换为实际格式（txt/csv/json）
        format_text = self.import_format_combo.currentText()
        format_map = {"TXT 文本文件": "txt", "CSV 表格文件": "csv", "JSON 数据文件": "json"}
        format = format_map.get(format_text, "txt")
        
        # 使用统一的进度条
        if self.parent and hasattr(self.parent, 'progress_bar'):
            progress_bar = self.parent.progress_bar
            progress_bar.start_progress("正在导入数据...")
        else:
            progress_bar = None
        
        # 创建并启动线程（保存为实例变量，防止被垃圾回收）
        self.import_thread = ImportThread(self.filter_service, file_path, format)
        
        def update_progress(progress, message):
            if progress_bar:
                progress_bar.update_progress(progress, message)
        
        def on_finished(result):
            if progress_bar:
                progress_bar.finish_progress(f"导入成功，共导入 {result.get('imported', 0)} 条数据", success=True)
            else:
                if hasattr(self.parent, 'show_toast'):
                    self.parent.show_toast(f"导入成功，共导入 {result.get('imported', 0)} 条数据")
            # 刷新所有表视图
            if self.parent and hasattr(self.parent, 'refresh_chars'):
                self.parent.refresh_chars()
                self.parent.refresh_special()
                self.parent.refresh_words()
        
        def on_error(error):
            if progress_bar:
                progress_bar.error_progress(f"导入失败：{error}")
            else:
                if hasattr(self.parent, 'show_toast'):
                    self.parent.show_toast(f"导入失败：{error}")
        
        self.import_thread.progress.connect(update_progress)
        self.import_thread.finished.connect(on_finished)
        self.import_thread.error.connect(on_error)
        self.import_thread.start()
    
    def _export_table(self, export_path, export_format, table, export_name):
        """导出单个表的数据"""
        file_path = os.path.join(export_path, f"{export_name}.{export_format}")
        return self.dict_service.export_data(file_path, export_format, table=table), file_path
    
    def _export_to_rime(self, file_path):
        """导出到 Rime 目录"""
        import shutil
        
        # 导出到 ibus/rime
        if config_manager.get("auto_export_ibus_rime", False):
            ibus_rime_path = os.path.expanduser("~/.config/ibus/rime")
            if os.path.exists(ibus_rime_path):
                shutil.copy(file_path, ibus_rime_path)
        
        # 导出到 fcitx5/rime
        if config_manager.get("auto_export_fcitx5_rime", False):
            fcitx5_rime_path = os.path.expanduser("~/.local/share/fcitx5/rime")
            if os.path.exists(fcitx5_rime_path):
                shutil.copy(file_path, fcitx5_rime_path)
    
    def export_data(self):
        """导出数据"""
        if not self.dict_service:
            QMessageBox.warning(self, "警告", "词典服务未初始化")
            return

        # 获取导出路径和格式
        export_path = self.export_path_edit.text().strip()
        if not export_path:
            QMessageBox.warning(self, "警告", "请输入导出路径")
            return

        # 确保导出路径存在
        if not os.path.exists(export_path):
            try:
                os.makedirs(export_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建导出目录失败: {e}")
                return

        format_text = self.export_format_combo.currentText()
        # 映射显示文本到实际格式代码
        format_map = {"TXT 文本文件": "txt", "CSV 表格文件": "csv", "JSON 数据文件": "json"}
        export_format = format_map.get(format_text, "txt")

        # 获取用户选择的导出表
        export_tables = config_manager.get("export_tables", ["words", "chars", "special"])
        if not export_tables:
            QMessageBox.warning(self, "警告", "请至少选择一个要导出的表")
            return

        try:
            total_exported = 0
            export_names = []  # 用于记录导出的文件路径

            # 分表导出模式：每个表单独导出为一个文件
            # 或者：合并导出模式：选中的表合并到一个文件
            split_export = config_manager.get("split_export_enabled", False)

            if split_export and len(export_tables) > 1:
                # 分表导出（选中的表各自导出为单独文件）
                for table in export_tables:
                    table_names = {"words": "词表", "chars": "字表", "special": "特殊字符表"}
                    export_name_key = f"{table}_export_name"
                    default_names = {"words": "vmtool_words", "chars": "vmtool_chars", "special": "vmtool_special"}
                    export_name = config_manager.get(export_name_key, default_names[table])

                    result, file_path = self._export_table(export_path, export_format, table, export_name)
                    total_exported += result
                    export_names.append(file_path)

                # 导出到 Rime 目录（取第一个文件）
                if export_names:
                    self._export_to_rime(export_names[0])

                QMessageBox.information(self, "成功", f"分表导出成功，共导出 {total_exported} 条数据")
            else:
                # 合并导出模式：将选中的表合并导出到一个文件
                default_export_name = config_manager.get("default_export_name", "vmtool_export")
                file_path = os.path.join(export_path, f"{default_export_name}.{export_format}")

                # 使用 tables 参数一次性合并导出
                result = self.dict_service.export_data(file_path, export_format, tables=export_tables)

                # 导出到 Rime 目录
                self._export_to_rime(file_path)

                QMessageBox.information(self, "成功", f"导出成功，共导出 {result} 条数据")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")
    
    def _add_rime_paths(self, all_paths, export_format, use_words_name=False):
        """添加 Rime 导出路径"""
        # 添加 ibus/rime 导出路径
        if config_manager.get("auto_export_ibus_rime", False):
            ibus_rime_path = os.path.expanduser("~/.config/ibus/rime")
            if os.path.exists(ibus_rime_path):
                if use_words_name:
                    # 只导出词表
                    words_export_name = config_manager.get("words_export_name", "vmtool_words")
                    ibus_full_path = os.path.join(ibus_rime_path, f"{words_export_name}.{export_format}")
                    all_paths.append(f"☁️ ibus/rime (词表): {ibus_full_path}")
                else:
                    # 导出所有数据
                    default_export_name = config_manager.get("default_export_name", "vmtool_export")
                    ibus_full_path = os.path.join(ibus_rime_path, f"{default_export_name}.{export_format}")
                    all_paths.append(f"☁️ ibus/rime: {ibus_full_path}")
            else:
                all_paths.append(f"⚠️ ibus/rime 目录不存在：{ibus_rime_path}")
        
        # 添加 fcitx5/rime 导出路径
        if config_manager.get("auto_export_fcitx5_rime", False):
            fcitx5_rime_path = os.path.expanduser("~/.local/share/fcitx5/rime")
            if os.path.exists(fcitx5_rime_path):
                if use_words_name:
                    # 只导出词表
                    words_export_name = config_manager.get("words_export_name", "vmtool_words")
                    fcitx5_full_path = os.path.join(fcitx5_rime_path, f"{words_export_name}.{export_format}")
                    all_paths.append(f"☁️ fcitx5/rime (词表): {fcitx5_full_path}")
                else:
                    # 导出所有数据
                    default_export_name = config_manager.get("default_export_name", "vmtool_export")
                    fcitx5_full_path = os.path.join(fcitx5_rime_path, f"{default_export_name}.{export_format}")
                    all_paths.append(f"☁️ fcitx5/rime: {fcitx5_full_path}")
            else:
                all_paths.append(f"⚠️ fcitx5/rime 目录不存在：{fcitx5_rime_path}")
    
    def update_export_full_path(self):
        """更新导出界面中的完整路径"""
        # 构造完整导出路径
        export_path = self.export_path_edit.text().strip()
        format_text = self.export_format_combo.currentText()
        format_map = {"TXT 文本文件": "txt", "CSV 表格文件": "csv", "JSON 数据文件": "json"}
        export_format = format_map.get(format_text, "txt")

        # 获取用户选择的导出表
        export_tables = config_manager.get("export_tables", ["words", "chars", "special"])

        # 收集所有导出路径
        all_paths = []

        table_names = {"words": "词表", "chars": "字表", "special": "特殊字符表"}
        default_names = {"words": "vmtool_words", "chars": "vmtool_chars", "special": "vmtool_special"}

        # 检查是否启用分表导出
        split_export = config_manager.get("split_export_enabled", False)

        if split_export and len(export_tables) > 1:
            # 分表导出路径（只显示选中的表）
            if config_manager.get("export_path_enabled", True):
                for table in export_tables:
                    export_name_key = f"{table}_export_name"
                    export_name = config_manager.get(export_name_key, default_names[table])
                    full_path = os.path.join(export_path, f"{export_name}.{export_format}")
                    all_paths.append(f"📁 {table_names[table]}导出：{full_path}")
            else:
                all_paths.append("⚠️ 默认导出路径已禁用")

            # 添加 Rime 导出路径
            self._add_rime_paths(all_paths, export_format, use_words_name=False)
        else:
            # 合并导出路径
            default_export_name = config_manager.get("default_export_name", "vmtool_export")

            # 显示选中的表
            selected_names = " + ".join([table_names.get(t, t) for t in export_tables])

            # 添加默认导出路径（如果启用）
            if config_manager.get("export_path_enabled", True):
                full_path = os.path.join(export_path, f"{default_export_name}.{export_format}")
                all_paths.append(f"📁 默认导出 ({selected_names})：{full_path}")
            else:
                all_paths.append("⚠️ 默认导出路径已禁用")

            # 添加 Rime 导出路径
            self._add_rime_paths(all_paths, export_format, use_words_name=False)

        # 显示所有导出路径
        paths_text = "\n".join(all_paths)
        self.full_export_path_value.setText(paths_text)
    
    def showEvent(self, event):
        """当标签页显示时自动更新导出路径"""
        super().showEvent(event)
        self.update_export_full_path()