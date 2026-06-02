from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QFormLayout, QLabel, QComboBox) 
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from app.core.config_manager import config_manager
from app.core.theme_constants import (
    THEME_MODE_AUTO, THEME_MODE_LIGHT, THEME_MODE_DARK,
    THEME_NAME_CLASSIC, THEME_NAME_MATERIAL3, THEME_NAME_LINEAR,
    THEME_COLOR_BLUE, THEME_COLOR_GREEN,
    THEME_COLOR_RED, THEME_COLOR_PURPLE, THEME_COLOR_ORANGE,
    MODE_DISPLAY_MAP, MODE_DISPLAY_REVERSE_MAP
)

def load_theme_settings(settings_content_layout, section_widgets, parent):
    """加载主题设置"""
    section_widget = QGroupBox("主题设置")
    section_layout = QVBoxLayout()
    
    # 主题设置
    theme_layout = QFormLayout()
    
    theme_label = QLabel("主题:")
    theme_combo = QComboBox()
    theme_combo.addItems([THEME_NAME_CLASSIC, THEME_NAME_MATERIAL3, THEME_NAME_LINEAR])

    # 模式设置
    mode_label = QLabel("模式:")
    mode_combo = QComboBox()
    # 按顺序添加模式显示名称
    mode_display_names = [
        MODE_DISPLAY_MAP[THEME_MODE_AUTO],
        MODE_DISPLAY_MAP[THEME_MODE_LIGHT],
        MODE_DISPLAY_MAP[THEME_MODE_DARK]
    ]
    mode_combo.addItems(mode_display_names)

    # 主题颜色设置（仅对Material3有效）
    color_label = QLabel("主题颜色:")
    color_combo = QComboBox()
    color_combo.addItems([
        THEME_COLOR_BLUE, THEME_COLOR_GREEN, THEME_COLOR_RED,
        THEME_COLOR_PURPLE, THEME_COLOR_ORANGE
    ])
    
    # 加载当前设置
    current_theme = config_manager.get("theme_name", THEME_NAME_CLASSIC)
    current_mode = config_manager.get("theme_mode", THEME_MODE_AUTO)
    current_color = config_manager.get("theme_color", THEME_COLOR_BLUE)
    
    theme_combo.setCurrentText(current_theme)
    
    # 映射内部模式值到显示名称（使用常量映射）
    display_mode = MODE_DISPLAY_MAP.get(current_mode, MODE_DISPLAY_MAP[THEME_MODE_AUTO])
    mode_combo.setCurrentText(display_mode)
    
    color_combo.setCurrentText(current_color)
    
    # 连接信号
    def on_theme_changed():
        theme = theme_combo.currentText()
        mode = mode_combo.currentText()
        color = color_combo.currentText()
        
        # 映射模式显示名称到内部值（使用常量映射）
        internal_mode = MODE_DISPLAY_REVERSE_MAP.get(mode, THEME_MODE_AUTO)
        
        # 保存设置
        config_manager.set("theme_name", theme)
        config_manager.set("theme_mode", internal_mode)
        config_manager.set("theme_color", color)
        
        # 使用主题管理器应用主题
        from ..theme_manager import theme_manager
        theme_manager.set_theme(internal_mode, theme, color)
        
        # 显示提示
        if hasattr(parent, 'show_toast'):
            parent.show_toast(f"主题已更改为：{theme} - {mode} - {color}")
    
    theme_combo.currentTextChanged.connect(on_theme_changed)
    mode_combo.currentTextChanged.connect(on_theme_changed)
    color_combo.currentTextChanged.connect(on_theme_changed)
    
    theme_layout.addRow(theme_label, theme_combo)
    theme_layout.addRow(mode_label, mode_combo)
    theme_layout.addRow(color_label, color_combo)
    
    section_layout.addLayout(theme_layout)
    section_widget.setLayout(section_layout)
    
    settings_content_layout.addWidget(section_widget)
    section_widgets["主题设置"] = section_widget
