"""导出设置面板 - 合并文件配置和权重计算设置"""

import os

from PyQt6.QtWidgets import QFormLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtWidgets import QComboBox, QCheckBox, QFileDialog
from PyQt6.QtCore import Qt

from .base_panel import SettingsPanel
from app.core.config_manager import config_manager
from app.core.theme_config import ThemeConfig
from ..theme_manager import theme_manager


class ExportPanel(SettingsPanel):
    """导出设置面板 - 导出路径、名称、表选择、分隔符、权重范围"""

    panel_name = "导出设置"
    panel_description = "文件导出路径、格式和权重计算范围"

    def _setup_ui(self):
        # 递归清理旧的子控件
        self._clear_layout(self._main_layout)

        # 主布局使用垂直布局
        main_form = QFormLayout()
        main_form.setSpacing(12)

        # 导出路径
        self.export_path_edit = QLineEdit()
        self.export_path_button = QPushButton("浏览")
        self.export_path_button.clicked.connect(self._browse_export_path)
        self.export_path_button.setMaximumWidth(80)

        export_path_layout = QHBoxLayout()
        export_path_layout.addWidget(self.export_path_edit)
        export_path_layout.addWidget(self.export_path_button)
        main_form.addRow("默认导出路径:", export_path_layout)

        # 导出名称
        self.export_name_edit = QLineEdit()
        main_form.addRow("默认导出名称:", self.export_name_edit)

        # 分隔符设置
        self.word_code_delimiter_combo = QComboBox()
        self.word_code_delimiter_combo.addItems(["Tab", ",", "|", "空格"])
        main_form.addRow("词条和编码分隔符:", self.word_code_delimiter_combo)

        self.code_weight_delimiter_combo = QComboBox()
        self.code_weight_delimiter_combo.addItems(["Tab", ",", "|", "空格"])
        main_form.addRow("编码和权重分隔符:", self.code_weight_delimiter_combo)

        self._main_layout.addLayout(main_form)

        # 获取主题颜色
        palette = ThemeConfig.get_palette(
            theme_manager.current_theme_name,
            theme_manager.current_theme_mode,
            theme_manager.current_theme_color
        )

        # 默认导出表（使用水平布局）
        export_tables_label = QLabel("默认导出表:")
        export_tables_label.setStyleSheet(f"font-weight: bold; color: {palette.text_primary};")
        self._main_layout.addWidget(export_tables_label)

        tables_layout = QHBoxLayout()
        self.words_checkbox = QCheckBox("词表")
        self.chars_checkbox = QCheckBox("字表")
        self.special_checkbox = QCheckBox("特殊字符表")
        tables_layout.addWidget(self.words_checkbox)
        tables_layout.addWidget(self.chars_checkbox)
        tables_layout.addWidget(self.special_checkbox)
        tables_layout.addStretch()
        self._main_layout.addLayout(tables_layout)

        # 分隔线
        separator = QLabel("")
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {palette.border_default};")
        self._main_layout.addWidget(separator)

        # 权重计算范围
        weight_label = QLabel("自动计算权重时的码表范围:")
        weight_label.setStyleSheet(f"font-weight: bold; color: {palette.text_primary};")
        self._main_layout.addWidget(weight_label)

        self.weight_words_checkbox = QCheckBox("词表 (常用词汇)")
        self.weight_chars_checkbox = QCheckBox("字表 (单字)")
        self.weight_special_checkbox = QCheckBox("特殊表 (特殊字符)")
        self._main_layout.addWidget(self.weight_words_checkbox)
        self._main_layout.addWidget(self.weight_chars_checkbox)
        self._main_layout.addWidget(self.weight_special_checkbox)

        # 说明信息
        info_label = QLabel("说明: 勾选的码表类型将在自动计算权重时被处理。手动设置权重的词条会被跳过。")
        info_label.setStyleSheet(f"color: {palette.text_secondary}; font-size: 11px;")
        info_label.setWordWrap(True)
        self._main_layout.addWidget(info_label)

        # Rime 自动导出设置
        self._setup_rime_auto_export(palette)

        # 加载当前值
        self._load_current_values()

    def _connect_signals(self):
        # 导出路径
        self.export_path_edit.textChanged.connect(
            lambda text: self._set_config("default_export_path", text)
        )

        # 导出名称
        self.export_name_edit.textChanged.connect(
            lambda text: self._set_config("default_export_name", text)
        )

        # 分隔符
        self.word_code_delimiter_combo.currentTextChanged.connect(
            lambda text: self._set_config("word_code_delimiter", self._delimiter_to_internal(text))
        )
        self.code_weight_delimiter_combo.currentTextChanged.connect(
            lambda text: self._set_config("code_weight_delimiter", self._delimiter_to_internal(text))
        )

        # 导出表
        self.words_checkbox.stateChanged.connect(self._on_export_tables_changed)
        self.chars_checkbox.stateChanged.connect(self._on_export_tables_changed)
        self.special_checkbox.stateChanged.connect(self._on_export_tables_changed)

        # 权重范围
        self.weight_words_checkbox.stateChanged.connect(
            lambda state: self._set_config("weight_calc_words", state == Qt.CheckState.Checked.value)
        )
        self.weight_chars_checkbox.stateChanged.connect(
            lambda state: self._set_config("weight_calc_chars", state == Qt.CheckState.Checked.value)
        )
        self.weight_special_checkbox.stateChanged.connect(
            lambda state: self._set_config("weight_calc_special", state == Qt.CheckState.Checked.value)
        )

    def _load_current_values(self):
        """从 config_manager 加载当前值"""
        # 导出路径
        export_path = self._get_config("default_export_path", "./")
        self.export_path_edit.setText(export_path)

        # 导出名称
        export_name = self._get_config("default_export_name", "vmtool_export")
        self.export_name_edit.setText(export_name)

        # 分隔符
        word_code_delimiter = self._get_config("word_code_delimiter", "\t")
        self.word_code_delimiter_combo.setCurrentText(self._delimiter_to_display(word_code_delimiter))

        code_weight_delimiter = self._get_config("code_weight_delimiter", "\t")
        self.code_weight_delimiter_combo.setCurrentText(self._delimiter_to_display(code_weight_delimiter))

        # 导出表
        saved_tables = self._get_config("export_tables", ["words", "chars", "special"])
        self.words_checkbox.setChecked("words" in saved_tables)
        self.chars_checkbox.setChecked("chars" in saved_tables)
        self.special_checkbox.setChecked("special" in saved_tables)

        # 权重范围
        self.weight_words_checkbox.setChecked(self._get_config("weight_calc_words", True))
        self.weight_chars_checkbox.setChecked(self._get_config("weight_calc_chars", False))
        self.weight_special_checkbox.setChecked(self._get_config("weight_calc_special", False))

        # Rime 自动导出
        self._load_rime_auto_export()

    def _setup_rime_auto_export(self, palette):
        """设置 Rime 自动导出开关（ibus/fcitx5）"""
        ibus_rime_path = os.path.expanduser("~/.config/ibus/rime")
        fcitx5_rime_path = os.path.expanduser("~/.local/share/fcitx5/rime")

        ibus_exists = os.path.exists(ibus_rime_path)
        fcitx5_exists = os.path.exists(fcitx5_rime_path)

        if not ibus_exists and not fcitx5_exists:
            # 两个路径都不存在，不显示此部分
            return

        # 分隔线
        separator = QLabel("")
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {palette.border_default};")
        self._main_layout.addWidget(separator)

        # Rime 自动导出标题
        rime_label = QLabel("Rime 自动导出:")
        rime_label.setStyleSheet(f"font-weight: bold; color: {palette.text_primary};")
        self._main_layout.addWidget(rime_label)

        # ibus/rime 开关
        if ibus_exists:
            self.ibus_rime_checkbox = QCheckBox(f"自动导出到 ibus/rime 目录 ({ibus_rime_path})")
            self.ibus_rime_checkbox.stateChanged.connect(
                lambda state: self._set_config(
                    "auto_export_ibus_rime", state == Qt.CheckState.Checked.value
                )
            )
            self._main_layout.addWidget(self.ibus_rime_checkbox)

        # fcitx5/rime 开关
        if fcitx5_exists:
            self.fcitx5_rime_checkbox = QCheckBox(f"自动导出到 fcitx5/rime 目录 ({fcitx5_rime_path})")
            self.fcitx5_rime_checkbox.stateChanged.connect(
                lambda state: self._set_config(
                    "auto_export_fcitx5_rime", state == Qt.CheckState.Checked.value
                )
            )
            self._main_layout.addWidget(self.fcitx5_rime_checkbox)

        # 提示信息
        rime_info = QLabel("勾选后，导出词表时将自动复制到对应 Rime 目录，无需手动操作。")
        rime_info.setStyleSheet(f"color: {palette.text_secondary}; font-size: 11px;")
        rime_info.setWordWrap(True)
        self._main_layout.addWidget(rime_info)

    def _load_rime_auto_export(self):
        """加载 Rime 自动导出开关状态"""
        if hasattr(self, 'ibus_rime_checkbox'):
            self.ibus_rime_checkbox.setChecked(
                self._get_config("auto_export_ibus_rime", False)
            )
        if hasattr(self, 'fcitx5_rime_checkbox'):
            self.fcitx5_rime_checkbox.setChecked(
                self._get_config("auto_export_fcitx5_rime", False)
            )

    def _browse_export_path(self):
        """浏览选择导出目录"""
        # 尝试使用 zenity
        try:
            import subprocess
            result = subprocess.run(
                ["zenity", "--file-selection", "--directory",
                 "--title=选择导出目录", "--filename=./"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                directory = result.stdout.strip()
                if directory:
                    self.export_path_edit.setText(directory)
                    self._set_config("default_export_path", directory)
                return
        except Exception:
            pass

        # 回退到 Qt 内置对话框
        directory = QFileDialog.getExistingDirectory(
            self, "选择导出目录", "./"
        )
        if directory:
            self.export_path_edit.setText(directory)
            self._set_config("default_export_path", directory)

    def _on_export_tables_changed(self):
        """导出表选择变更"""
        selected = []
        if self.words_checkbox.isChecked():
            selected.append("words")
        if self.chars_checkbox.isChecked():
            selected.append("chars")
        if self.special_checkbox.isChecked():
            selected.append("special")
        self._set_config("export_tables", selected)

        # 同步更新导入导出标签页（通过信号机制）
        self._sync_import_export_tab(selected)

    def _sync_import_export_tab(self, selected):
        """同步更新导入导出标签页的复选框"""
        # 向上查找主窗口
        parent = self.parent()
        while parent and not hasattr(parent, 'tab_widget'):
            parent = parent.parent() if hasattr(parent, 'parent') else None

        if parent and hasattr(parent, 'tab_widget'):
            tab_widget = parent.tab_widget
            for i in range(tab_widget.count()):
                if tab_widget.tabText(i) == "导入导出":
                    import_export_tab = tab_widget.widget(i)
                    if hasattr(import_export_tab, 'words_checkbox'):
                        import_export_tab.words_checkbox.blockSignals(True)
                        import_export_tab.words_checkbox.setChecked("words" in selected)
                        import_export_tab.words_checkbox.blockSignals(False)
                    if hasattr(import_export_tab, 'chars_checkbox'):
                        import_export_tab.chars_checkbox.blockSignals(True)
                        import_export_tab.chars_checkbox.setChecked("chars" in selected)
                        import_export_tab.chars_checkbox.blockSignals(False)
                    if hasattr(import_export_tab, 'special_checkbox'):
                        import_export_tab.special_checkbox.blockSignals(True)
                        import_export_tab.special_checkbox.setChecked("special" in selected)
                        import_export_tab.special_checkbox.blockSignals(False)
                    if hasattr(import_export_tab, 'update_export_full_path'):
                        import_export_tab.update_export_full_path()
                    break

    def _delimiter_to_internal(self, display_text):
        """将显示文本转换为内部值"""
        mapping = {"Tab": "\t", ",": ",", "|": "|", "空格": " "}
        return mapping.get(display_text, "\t")

    def _delimiter_to_display(self, internal_value):
        """将内部值转换为显示文本"""
        mapping = {"\t": "Tab", ",": ",", "|": "|", " ": "空格"}
        return mapping.get(internal_value, "Tab")

    def reload(self):
        """重新加载设置值"""
        self._load_current_values()

    def _on_theme_changed(self, _mode, _name, _color):
        """主题变更时更新样式"""
        # 重新设置 UI 以更新颜色
        self._setup_ui()
