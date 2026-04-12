from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
                             QLabel, QComboBox, QProgressDialog, QMessageBox, QFileDialog,
                             QGroupBox, QFormLayout, QRadioButton, QButtonGroup, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from app.services.filter import FilterService
from app.core.config_manager import config_manager
import os
from ..threads import ImportThread

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
        
        # 完整导出路径显示
        path_display_group = QGroupBox("📍 完整导出路径")
        path_display_layout = QVBoxLayout(path_display_group)
        
        self.full_export_path_value = QLabel("")
        self.full_export_path_value.setWordWrap(True)
        self.full_export_path_value.setStyleSheet("QLabel { color: #1976D2; padding: 8px; background-color: #E3F2FD; border-radius: 4px; }")
        self.full_export_path_value.setMinimumHeight(40)
        path_display_layout.addWidget(self.full_export_path_value)
        
        export_layout.addWidget(path_display_group)
        
        # 导出按钮
        export_button = QPushButton("🚀 开始导出")
        export_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; border-radius: 5px; } QPushButton:hover { background-color: #45a049; }")
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
        import_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 10px; border-radius: 5px; } QPushButton:hover { background-color: #0b7dda; }")
        import_button.setMinimumHeight(40)
        import_button.clicked.connect(self.import_data)
        import_layout.addWidget(import_button)
        
        import_layout.addStretch()
        
        main_layout.addWidget(import_group)
        
        # 初始更新完整导出路径
        self.update_export_full_path()
    
    def browse_import_path(self):
        """浏览导入路径"""
        # 尝试使用 zenity 打开文件选择对话框
        try:
            import subprocess
            
            # 使用 zenity 打开文件选择对话框
            result = subprocess.run(
                ["zenity", "--file-selection", "--title=选择导入文件", "--file-filter=文本文件 (*.txt)|*.txt|CSV文件 (*.csv)|*.csv|JSON文件 (*.json)|*.json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 如果 zenity 成功执行（无论是否选择了文件），都不再使用Qt内置对话框
            # 即使用户取消选择，也不再打开内置对话框
            file_path = result.stdout.strip()
            if file_path:
                self.import_path_edit.setText(file_path)
                config_manager.set("import_path", file_path)
            return
        except Exception:
            pass
        
        # 如果 zenity 失败，使用Qt内置对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择导入文件", "./", "文本文件 (*.txt);;CSV文件 (*.csv);;JSON文件 (*.json)"
        )
        if file_path:
            self.import_path_edit.setText(file_path)
            config_manager.set("import_path", file_path)
    
    def browse_export_path(self):
        """浏览导出路径"""
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
            # 即使用户取消选择，也不再打开内置对话框
            directory = result.stdout.strip()
            if directory:
                self.export_path_edit.setText(directory)
                config_manager.set("default_export_path", directory)
            return
        except Exception:
            pass
        
        # 如果 zenity 失败，使用Qt内置对话框
        directory = QFileDialog.getExistingDirectory(
            self, "选择导出目录", "./"
        )
        if directory:
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
            QMessageBox.warning(self, "警告", f"文件不存在: {file_path}")
            return
        
        format = self.import_format_combo.currentText()
        
        # 显示进度对话框
        progress_dialog = QProgressDialog("正在导入数据...", "取消", 0, 100, self)
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.show()
        
        # 创建并启动线程
        thread = ImportThread(self.filter_service, file_path, format)
        
        def update_progress(progress, message):
            progress_dialog.setValue(progress)
            progress_dialog.setLabelText(message)
        
        def on_finished(result):
            progress_dialog.close()
            QMessageBox.information(self, "成功", f"导入成功，共导入 {result.get('imported', 0)} 条数据")
            # 刷新所有表视图
            if self.parent and hasattr(self.parent, 'refresh_chars'):
                self.parent.refresh_chars()
                self.parent.refresh_special()
                self.parent.refresh_words()
        
        def on_error(error):
            progress_dialog.close()
            QMessageBox.critical(self, "错误", f"导入失败: {error}")
        
        thread.progress.connect(update_progress)
        thread.finished.connect(on_finished)
        thread.error.connect(on_error)
        thread.start()
    
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
        
        export_format = self.export_format_combo.currentText()
        
        # 构造默认导出文件名
        default_export_name = config_manager.get("default_export_name", "vmtool_export")
        file_path = os.path.join(export_path, f"{default_export_name}.{export_format}")
        
        try:
            # 导出数据
            result = self.dict_service.export_data(file_path, export_format)
            
            # 检查是否需要自动导出到 Rime 目录
            if config_manager.get("auto_export_ibus_rime", False):
                ibus_rime_path = os.path.expanduser("~/.config/ibus/rime")
                if os.path.exists(ibus_rime_path):
                    # 复制文件到 ibus/rime 目录
                    import shutil
                    shutil.copy(file_path, ibus_rime_path)
            
            if config_manager.get("auto_export_fcitx5_rime", False):
                fcitx5_rime_path = os.path.expanduser("~/.local/share/fcitx5/rime")
                if os.path.exists(fcitx5_rime_path):
                    # 复制文件到 fcitx5/rime 目录
                    import shutil
                    shutil.copy(file_path, fcitx5_rime_path)
            
            QMessageBox.information(self, "成功", f"导出成功，共导出 {result.get('exported', 0)} 条数据")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")
    
    def update_export_full_path(self):
        """更新导出界面中的完整路径"""
        # 构造完整导出路径
        export_path = self.export_path_edit.text().strip()
        format_text = self.export_format_combo.currentText()
        format_map = {"TXT 文本文件": "txt", "CSV 表格文件": "csv", "JSON 数据文件": "json"}
        export_format = format_map.get(format_text, "txt")
        default_export_name = config_manager.get("default_export_name", "vmtool_export")
        
        # 收集所有导出路径
        all_paths = []
        
        # 添加默认导出路径（如果启用）
        if config_manager.get("export_path_enabled", True):
            full_path = os.path.join(export_path, f"{default_export_name}.{export_format}")
            all_paths.append(f"📁 默认导出：{full_path}")
        else:
            all_paths.append("⚠️ 默认导出路径已禁用")
        
        # 添加 ibus/rime 导出路径
        if config_manager.get("auto_export_ibus_rime", False):
            ibus_rime_path = os.path.expanduser("~/.config/ibus/rime")
            if os.path.exists(ibus_rime_path):
                ibus_full_path = os.path.join(ibus_rime_path, f"{default_export_name}.{export_format}")
                all_paths.append(f"☁️ ibus/rime: {ibus_full_path}")
            else:
                all_paths.append(f"⚠️ ibus/rime 目录不存在：{ibus_rime_path}")
        
        # 添加 fcitx5/rime 导出路径
        if config_manager.get("auto_export_fcitx5_rime", False):
            fcitx5_rime_path = os.path.expanduser("~/.local/share/fcitx5/rime")
            if os.path.exists(fcitx5_rime_path):
                fcitx5_full_path = os.path.join(fcitx5_rime_path, f"{default_export_name}.{export_format}")
                all_paths.append(f"☁️ fcitx5/rime: {fcitx5_full_path}")
            else:
                all_paths.append(f"⚠️ fcitx5/rime 目录不存在：{fcitx5_rime_path}")
        
        # 显示所有导出路径
        paths_text = "\n".join(all_paths)
        self.full_export_path_value.setText(paths_text)