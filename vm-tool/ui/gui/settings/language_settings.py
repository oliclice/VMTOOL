from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QFormLayout, QLabel, QComboBox) 
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication
from app.core.config_manager import config_manager

def load_language_settings(settings_content_layout, section_widgets, parent):
    """加载语言设置"""
    section_widget = QGroupBox("语言设置")
    section_layout = QVBoxLayout()
    
    # 语言设置
    language_layout = QFormLayout()
    
    language_label = QLabel("语言:")
    language_combo = QComboBox()
    language_combo.addItems(["中文", "English"])
    language_combo.setCurrentText(config_manager.get("language", "中文"))
    
    # 连接信号，自动保存
    language_combo.currentTextChanged.connect(lambda text: config_manager.set("language", text))
    
    language_layout.addRow(language_label, language_combo)
    
    # 字体设置
    font_label = QLabel("字体:")
    font_combo = QComboBox()
    
    # 获取系统字体列表
    font_families = QFontDatabase.families()
    font_combo.addItems(font_families)
    
    # 加载当前字体设置
    current_font = config_manager.get("font_family", "")
    if current_font and current_font in font_families:
        font_combo.setCurrentText(current_font)
    
    # 连接信号，自动保存并应用
    def on_font_changed(font_family):
        config_manager.set("font_family", font_family)
        # 应用字体到整个应用
        font = QFont(font_family)
        QApplication.instance().setFont(font)
        if hasattr(parent, 'show_toast'):
            parent.show_toast(f"字体已更改为: {font_family}")
    
    font_combo.currentTextChanged.connect(on_font_changed)
    
    language_layout.addRow(font_label, font_combo)
    
    section_layout.addLayout(language_layout)
    section_widget.setLayout(section_layout)
    
    settings_content_layout.addWidget(section_widget)
    section_widgets["语言设置"] = section_widget
