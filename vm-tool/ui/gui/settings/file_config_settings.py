from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt
from app.core.config_manager import config_manager

def load_file_config_settings(settings_content_layout, section_widgets, parent):
    """加载文件配置设置"""
    section_widget = QGroupBox("文件配置")
    section_layout = QVBoxLayout()

    # 导出路径设置
    export_path_layout = QFormLayout()

    export_path_label = QLabel("默认导出路径:")
    export_path_edit = QLineEdit()
    export_path_edit.setText(config_manager.get("default_export_path", "./"))

    # 连接信号，自动保存
    def on_export_path_changed(text):
        config_manager.set("default_export_path", text)
        # 更新导入导出标签页中的路径
        if hasattr(parent, 'export_path_edit'):
            parent.export_path_edit.setText(text)
            # 更新导出界面中的完整路径
            if hasattr(parent, 'update_export_full_path'):
                parent.update_export_full_path()

    export_path_edit.textChanged.connect(on_export_path_changed)

    # 连接浏览按钮点击事件
    def browse_export_path():
        # 尝试使用 zenity 打开目录选择对话框
        try:
            import subprocess

            # 使用 zenity 打开目录选择对话框
            result = subprocess.run(
                ["zenity", "--file-selection", "--directory", "--title=选择导出目录", "--filename=./"],
                capture_output=True,
                text=True,
                timeout=30
            )

            # 如果 zenity 成功执行（无论是否选择了目录），都不再使用Qt内置对话框
            if result.returncode == 0:
                directory = result.stdout.strip()
                if directory:
                    export_path_edit.setText(directory)
                    config_manager.set("default_export_path", directory)
                return
        except Exception:
            pass

        # 如果 zenity 失败，使用Qt内置对话框
        from PyQt6.QtWidgets import QFileDialog
        directory = QFileDialog.getExistingDirectory(
            parent, "选择导出目录", "./"
        )
        if directory:
            export_path_edit.setText(directory)
            config_manager.set("default_export_path", directory)

    export_browse_button = QPushButton("浏览")
    export_browse_button.clicked.connect(browse_export_path)

    export_browse_layout = QHBoxLayout()
    export_browse_layout.addWidget(export_path_edit)
    export_browse_layout.addWidget(export_browse_button)

    export_path_layout.addRow(export_path_label, export_browse_layout)

    # 默认导出名称设置
    export_name_label = QLabel("默认导出名称:")
    export_name_edit = QLineEdit()
    export_name_edit.setText(config_manager.get("default_export_name", "vmtool_export"))

    # 连接信号，自动保存
    def on_export_name_changed(text):
        config_manager.set("default_export_name", text)
        # 更新导出界面中的完整路径
        if hasattr(parent, 'update_export_full_path'):
            parent.update_export_full_path()

    export_name_edit.textChanged.connect(on_export_name_changed)
    export_path_layout.addRow(export_name_label, export_name_edit)

    # 默认导出表设置（与导入导出标签页同步）
    export_tables_layout = QHBoxLayout()
    export_tables_label = QLabel("默认导出表:")
    saved_tables = config_manager.get("export_tables", ["words", "chars", "special"])

    words_cb = QCheckBox("词表")
    chars_cb = QCheckBox("字表")
    special_cb = QCheckBox("特殊字符表")
    words_cb.setChecked("words" in saved_tables)
    chars_cb.setChecked("chars" in saved_tables)
    special_cb.setChecked("special" in saved_tables)

    def on_export_tables_changed():
        selected = []
        if words_cb.isChecked():
            selected.append("words")
        if chars_cb.isChecked():
            selected.append("chars")
        if special_cb.isChecked():
            selected.append("special")
        config_manager.set("export_tables", selected)
        # 同步更新导入导出标签页的复选框
        import_export_tab = None
        if hasattr(parent, 'tab_widget'):
            tab_widget = parent.tab_widget
            for i in range(tab_widget.count()):
                if tab_widget.tabText(i) == "导入导出":
                    import_export_tab = tab_widget.widget(i)
                    break
        if import_export_tab is not None:
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

    words_cb.stateChanged.connect(on_export_tables_changed)
    chars_cb.stateChanged.connect(on_export_tables_changed)
    special_cb.stateChanged.connect(on_export_tables_changed)

    export_tables_row = QHBoxLayout()
    export_tables_row.addWidget(export_tables_label)
    export_tables_row.addWidget(words_cb)
    export_tables_row.addWidget(chars_cb)
    export_tables_row.addWidget(special_cb)
    export_tables_row.addStretch()
    export_path_layout.addRow(export_tables_row)

    # 分隔符设置
    delimiter_layout = QFormLayout()

    # 词条和编码分隔符
    word_code_delimiter_label = QLabel("词条和编码分隔符:")
    word_code_delimiter_combo = QComboBox()
    word_code_delimiter_combo.addItems(["Tab", ",", "|", "空格"])
    current_delimiter = config_manager.get("word_code_delimiter", "\t")
    if current_delimiter == "\t":
        word_code_delimiter_combo.setCurrentText("Tab")
    elif current_delimiter == ",":
        word_code_delimiter_combo.setCurrentText(",")
    elif current_delimiter == "|":
        word_code_delimiter_combo.setCurrentText("|")
    elif current_delimiter == " ":
        word_code_delimiter_combo.setCurrentText("空格")

    # 连接信号，自动保存
    def on_word_code_delimiter_changed(text):
        if text == "Tab":
            delimiter = "\t"
        elif text == ",":
            delimiter = ","
        elif text == "|":
            delimiter = "|"
        elif text == "空格":
            delimiter = " "
        config_manager.set("word_code_delimiter", delimiter)

    word_code_delimiter_combo.currentTextChanged.connect(on_word_code_delimiter_changed)

    # 编码和权重分隔符
    code_weight_delimiter_label = QLabel("编码和权重分隔符:")
    code_weight_delimiter_combo = QComboBox()
    code_weight_delimiter_combo.addItems(["Tab", ",", "|", "空格"])
    current_delimiter = config_manager.get("code_weight_delimiter", "\t")
    if current_delimiter == "\t":
        code_weight_delimiter_combo.setCurrentText("Tab")
    elif current_delimiter == ",":
        code_weight_delimiter_combo.setCurrentText(",")
    elif current_delimiter == "|":
        code_weight_delimiter_combo.setCurrentText("|")
    elif current_delimiter == " ":
        code_weight_delimiter_combo.setCurrentText("空格")

    # 连接信号，自动保存
    def on_code_weight_delimiter_changed(text):
        if text == "Tab":
            delimiter = "\t"
        elif text == ",":
            delimiter = ","
        elif text == "|":
            delimiter = "|"
        elif text == "空格":
            delimiter = " "
        config_manager.set("code_weight_delimiter", delimiter)

    code_weight_delimiter_combo.currentTextChanged.connect(on_code_weight_delimiter_changed)

    delimiter_layout.addRow(word_code_delimiter_label, word_code_delimiter_combo)
    delimiter_layout.addRow(code_weight_delimiter_label, code_weight_delimiter_combo)

    section_layout.addLayout(export_path_layout)
    section_layout.addLayout(delimiter_layout)
    section_widget.setLayout(section_layout)

    settings_content_layout.addWidget(section_widget)
    section_widgets["文件配置"] = section_widget
