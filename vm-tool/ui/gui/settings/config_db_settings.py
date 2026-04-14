from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout) 
from PyQt6.QtCore import Qt
import os
from app.core.config_manager import config_manager

def load_config_dir_settings(settings_content_layout, section_widgets, parent):
    """加载配置目录设置"""
    section_widget = QGroupBox("配置目录")
    section_layout = QVBoxLayout()
    
    # 配置目录设置
    config_dir_layout = QFormLayout()
    
    dir_label = QLabel("配置目录:")
    dir_edit = QLineEdit()
    dir_edit.setText(config_manager.get("config_dir", "~/.config/vm-tool"))
    # 连接信号，自动保存
    dir_edit.textChanged.connect(lambda text: config_manager.set("config_dir", text))
    
    # 连接浏览按钮点击事件
    def browse_config_dir():
        # 尝试使用 zenity 打开目录选择对话框
        try:
            import subprocess
            
            # 使用 zenity 打开目录选择对话框
            result = subprocess.run(
                ["zenity", "--file-selection", "--directory", "--title=选择配置目录", "--filename=~/.config/"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 如果 zenity 成功执行（无论是否选择了目录），都不再使用Qt内置对话框
            if result.returncode == 0:
                directory = result.stdout.strip()
                if directory:
                    dir_edit.setText(directory)
                    config_manager.set("config_dir", directory)
                return
        except Exception:
            pass
        
        # 如果 zenity 失败，使用Qt内置对话框
        from PyQt6.QtWidgets import QFileDialog
        directory = QFileDialog.getExistingDirectory(
            parent, "选择配置目录", "~/.config"
        )
        if directory:
            dir_edit.setText(directory)
            config_manager.set("config_dir", directory)
    
    browse_button = QPushButton("浏览")
    browse_button.clicked.connect(browse_config_dir)
    
    browse_layout = QHBoxLayout()
    browse_layout.addWidget(dir_edit)
    browse_layout.addWidget(browse_button)
    
    config_dir_layout.addRow(dir_label, browse_layout)
    section_layout.addLayout(config_dir_layout)
    section_widget.setLayout(section_layout)
    
    settings_content_layout.addWidget(section_widget)
    section_widgets["配置目录"] = section_widget

def load_database_path_settings(settings_content_layout, section_widgets, parent):
    """加载数据库路径设置"""
    section_widget = QGroupBox("数据库路径")
    section_layout = QVBoxLayout()
    
    # 数据库路径设置
    database_path_layout = QFormLayout()
    
    path_label = QLabel("数据库路径:")
    path_edit = QLineEdit()
    
    # 计算默认数据库路径
    config_dir = config_manager.get("config_dir", "~/.config/vm-tool")
    # 展开波浪号
    config_dir = os.path.expanduser(config_dir)
    default_db_path = os.path.join(config_dir, "vm_tool.db")
    
    path_edit.setText(config_manager.get("database_path", default_db_path))
    # 连接信号，自动保存
    path_edit.textChanged.connect(lambda text: config_manager.set("database_path", text))
    
    # 连接浏览按钮点击事件
    def browse_database_path():
        # 尝试使用 zenity 打开保存文件对话框
        try:
            import subprocess
            
            # 使用 zenity 打开保存文件对话框
            result = subprocess.run(
                ["zenity", "--file-selection", "--save", "--title=选择数据库文件", "--file-filter=SQLite数据库文件 (*.db)|*.db"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 如果 zenity 成功执行（无论是否选择了文件），都不再使用Qt内置对话框
            if result.returncode == 0:
                file_path = result.stdout.strip()
                if file_path:
                    path_edit.setText(file_path)
                    config_manager.set("database_path", file_path)
                return
        except Exception:
            pass
        
        # 如果 zenity 失败，使用Qt内置对话框
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            parent, "选择数据库文件", "", "SQLite数据库文件 (*.db)"
        )
        if file_path:
            path_edit.setText(file_path)
            config_manager.set("database_path", file_path)
    
    browse_button = QPushButton("浏览")
    browse_button.clicked.connect(browse_database_path)
    
    browse_layout = QHBoxLayout()
    browse_layout.addWidget(path_edit)
    browse_layout.addWidget(browse_button)
    
    database_path_layout.addRow(path_label, browse_layout)
    section_layout.addLayout(database_path_layout)
    section_widget.setLayout(section_layout)
    
    settings_content_layout.addWidget(section_widget)
    section_widgets["数据库路径"] = section_widget
