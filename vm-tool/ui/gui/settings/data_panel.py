"""数据设置面板 - 合并配置目录和数据库路径设置"""

import os
from PyQt6.QtWidgets import QFormLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtWidgets import QFileDialog

from .base_panel import SettingsPanel
from app.core.config_manager import config_manager


class DataPanel(SettingsPanel):
    """数据设置面板 - 配置目录和数据库路径"""

    panel_name = "数据设置"
    panel_description = "配置文件目录和数据库存储路径"

    def _setup_ui(self):
        layout = QFormLayout()
        layout.setSpacing(12)

        # 配置目录
        self.config_dir_edit = QLineEdit()
        self.config_dir_button = QPushButton("浏览")
        self.config_dir_button.clicked.connect(self._browse_config_dir)

        config_dir_layout = QHBoxLayout()
        config_dir_layout.addWidget(self.config_dir_edit)
        config_dir_layout.addWidget(self.config_dir_button)
        layout.addRow("配置目录:", config_dir_layout)

        # 数据库路径
        self.db_path_edit = QLineEdit()
        self.db_path_button = QPushButton("浏览")
        self.db_path_button.clicked.connect(self._browse_database_path)

        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_edit)
        db_path_layout.addWidget(self.db_path_button)
        layout.addRow("数据库路径:", db_path_layout)

        self._main_layout.addLayout(layout)

        # 加载当前值
        self._load_current_values()

    def _connect_signals(self):
        # 配置目录变更
        self.config_dir_edit.textChanged.connect(
            lambda text: self._set_config("config_dir", text)
        )

        # 数据库路径变更（使用 editingFinished 避免频繁触发）
        self.db_path_edit.editingFinished.connect(self._on_db_path_changed)

    def _load_current_values(self):
        """从 config_manager 加载当前值"""
        # 配置目录
        config_dir = self._get_config("config_dir", "~/.config/vm-tool")
        self.config_dir_edit.setText(config_dir)

        # 数据库路径
        config_dir_expanded = os.path.expanduser(config_dir)
        default_db_path = os.path.join(config_dir_expanded, "vm_tool.db")
        db_path = self._get_config("database_path", default_db_path)
        self.db_path_edit.setText(db_path)

    def _browse_config_dir(self):
        """浏览选择配置目录"""
        # 尝试使用 zenity
        try:
            import subprocess
            result = subprocess.run(
                ["zenity", "--file-selection", "--directory",
                 "--title=选择配置目录", "--filename=~/.config/"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                directory = result.stdout.strip()
                if directory:
                    self.config_dir_edit.setText(directory)
                    self._set_config("config_dir", directory)
                return
        except Exception:
            pass

        # 回退到 Qt 内置对话框
        directory = QFileDialog.getExistingDirectory(
            self, "选择配置目录", "~/.config"
        )
        if directory:
            self.config_dir_edit.setText(directory)
            self._set_config("config_dir", directory)

    def _browse_database_path(self):
        """浏览选择数据库文件"""
        # 尝试使用 zenity
        try:
            import subprocess
            result = subprocess.run(
                ["zenity", "--file-selection", "--save",
                 "--title=选择数据库文件",
                 "--file-filter=SQLite数据库文件 (*.db)|*.db"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                file_path = result.stdout.strip()
                if file_path:
                    self.db_path_edit.setText(file_path)
                    self._set_config("database_path", file_path)
                    self._recreate_engine()
                return
        except Exception:
            pass

        # 回退到 Qt 内置对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择数据库文件", "", "SQLite数据库文件 (*.db)"
        )
        if file_path:
            self.db_path_edit.setText(file_path)
            self._set_config("database_path", file_path)
            self._recreate_engine()

    def _on_db_path_changed(self):
        """数据库路径变更处理"""
        self._set_config("database_path", self.db_path_edit.text())
        self._recreate_engine()

    def _recreate_engine(self):
        """重建数据库引擎"""
        from app.dal.database import recreate_engine
        recreate_engine()

    def reload(self):
        """重新加载设置值"""
        self._load_current_values()
