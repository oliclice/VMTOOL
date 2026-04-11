from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
                             QLabel, QComboBox, QProgressDialog, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt
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
        """初始化UI"""
        layout = QVBoxLayout(self)
        # 设置布局间距，减少空白
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 导出部分（上侧）
        export_group = QWidget()
        export_layout = QVBoxLayout(export_group)
        # 设置内部布局间距，确保标题与配置和按钮之间的距离不超过400px
        export_layout.setSpacing(10)
        
        export_title = QLabel("导出")
        export_title.setFont(self.parent.font() if self.parent else None)
        export_layout.addWidget(export_title)
        
        # 导出路径
        export_path_layout = QHBoxLayout()
        export_path_label = QLabel("导出路径:")
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setText(config_manager.get("default_export_path", "./"))
        # 设置输入框的最小宽度
        self.export_path_edit.setMinimumWidth(300)
        
        # 连接信号，自动保存
        def on_export_path_changed(text):
            config_manager.set("default_export_path", text)
            # 更新导出界面中的完整路径
            if hasattr(self, 'update_export_full_path'):
                self.update_export_full_path()
        
        self.export_path_edit.textChanged.connect(on_export_path_changed)
        
        export_browse_button = QPushButton("浏览")
        export_browse_button.clicked.connect(self.browse_export_path)
        
        export_path_layout.addWidget(export_path_label)
        export_path_layout.addWidget(self.export_path_edit)
        export_path_layout.addWidget(export_browse_button)
        export_layout.addLayout(export_path_layout)
        
        # 导出格式
        export_format_layout = QHBoxLayout()
        export_format_label = QLabel("导出格式:")
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["txt", "csv", "json"])
        self.export_format_combo.setCurrentText(config_manager.get("default_export_format", "txt"))
        export_format_layout.addWidget(export_format_label)
        export_format_layout.addWidget(self.export_format_combo)
        export_layout.addLayout(export_format_layout)
        
        # 完整导出路径显示
        self.full_export_path_label = QLabel("完整导出路径:")
        self.full_export_path_value = QLabel("")
        # 设置标签的最小宽度，确保文本能够完整显示
        self.full_export_path_value.setMinimumWidth(300)
        export_layout.addWidget(self.full_export_path_label)
        export_layout.addWidget(self.full_export_path_value)
        
        # 导出按钮
        export_button = QPushButton("导出")
        export_button.clicked.connect(self.export_data)
        export_layout.addWidget(export_button)
        
        layout.addWidget(export_group)
        
        # 导入部分（下侧）
        import_group = QWidget()
        import_layout = QVBoxLayout(import_group)
        # 设置内部布局间距，确保标题与配置和按钮之间的距离不超过400px
        import_layout.setSpacing(10)
        
        import_title = QLabel("导入")
        import_title.setFont(self.parent.font() if self.parent else None)
        import_layout.addWidget(import_title)
        
        # 导入路径
        import_path_layout = QHBoxLayout()
        import_path_label = QLabel("导入路径:")
        self.import_path_edit = QLineEdit()
        self.import_path_edit.setText(config_manager.get("import_path", "./"))
        # 设置输入框的最小宽度
        self.import_path_edit.setMinimumWidth(300)
        
        # 连接信号，自动保存
        def on_import_path_changed(text):
            config_manager.set("import_path", text)
        
        self.import_path_edit.textChanged.connect(on_import_path_changed)
        
        import_browse_button = QPushButton("浏览")
        import_browse_button.clicked.connect(self.browse_import_path)
        
        import_path_layout.addWidget(import_path_label)
        import_path_layout.addWidget(self.import_path_edit)
        import_path_layout.addWidget(import_browse_button)
        import_layout.addLayout(import_path_layout)
        
        # 导入格式
        import_format_layout = QHBoxLayout()
        import_format_label = QLabel("导入格式:")
        self.import_format_combo = QComboBox()
        self.import_format_combo.addItems(["txt", "csv", "json"])
        self.import_format_combo.setCurrentText(config_manager.get("default_import_format", "txt"))
        import_format_layout.addWidget(import_format_label)
        import_format_layout.addWidget(self.import_format_combo)
        import_layout.addLayout(import_format_layout)
        
        # 导入按钮
        import_button = QPushButton("导入")
        import_button.clicked.connect(self.import_data)
        import_layout.addWidget(import_button)
        
        layout.addWidget(import_group)
        
        # 初始更新完整导出路径
        self.update_export_full_path()
        
        # 连接信号，当导出格式改变时更新完整导出路径
        self.export_format_combo.currentTextChanged.connect(self.update_export_full_path)
    
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
        export_format = self.export_format_combo.currentText()
        default_export_name = config_manager.get("default_export_name", "vmtool_export")
        full_path = os.path.join(export_path, f"{default_export_name}.{export_format}")
        
        # 显示完整导出路径
        self.full_export_path_value.setText(full_path)
        
        # 检查是否启用了默认导出路径
        if not config_manager.get("export_path_enabled", True):
            self.full_export_path_value.setText("默认导出路径已禁用")
        
        # 检查是否启用了 Rime 自动导出
        rime_paths = []
        if config_manager.get("auto_export_ibus_rime", False):
            ibus_rime_path = os.path.expanduser("~/.config/ibus/rime")
            if os.path.exists(ibus_rime_path):
                rime_paths.append(f"ibus/rime: {os.path.join(ibus_rime_path, f'{default_export_name}.{export_format}')}")
        
        if config_manager.get("auto_export_fcitx5_rime", False):
            fcitx5_rime_path = os.path.expanduser("~/.local/share/fcitx5/rime")
            if os.path.exists(fcitx5_rime_path):
                rime_paths.append(f"fcitx5/rime: {os.path.join(fcitx5_rime_path, f'{default_export_name}.{export_format}')}")
        
        # 如果有 Rime 导出路径，添加到显示中
        if rime_paths:
            rime_paths_text = "\n".join(rime_paths)
            self.full_export_path_value.setText(f"{full_path}\n\nRime 自动导出路径:\n{rime_paths_text}")