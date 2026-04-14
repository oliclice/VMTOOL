from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QFormLayout, QLabel, QComboBox, QCheckBox) 
from PyQt6.QtCore import Qt
from app.core.config_manager import config_manager

def load_stats_settings(settings_content_layout, section_widgets, parent):
    """加载统计设置"""
    section_widget = QGroupBox("统计设置")
    section_layout = QVBoxLayout()
    
    # 统计设置
    stats_layout = QFormLayout()
    
    # 启用统计
    stats_enabled_label = QLabel("启用统计:")
    stats_enabled_checkbox = QCheckBox()
    stats_enabled_checkbox.setChecked(config_manager.get("stats_enabled", True))
    # 连接信号，自动保存
    stats_enabled_checkbox.stateChanged.connect(lambda state: config_manager.set("stats_enabled", state == 2))
    
    # 统计周期
    stats_period_label = QLabel("统计周期:")
    stats_period_combo = QComboBox()
    stats_period_combo.addItems(["每日", "每周", "每月"])
    current_period = config_manager.get("stats_period", "每日")
    stats_period_combo.setCurrentText(current_period)
    # 连接信号，自动保存
    stats_period_combo.currentTextChanged.connect(lambda text: config_manager.set("stats_period", text))
    
    stats_layout.addRow(stats_enabled_label, stats_enabled_checkbox)
    stats_layout.addRow(stats_period_label, stats_period_combo)
    
    section_layout.addLayout(stats_layout)
    section_widget.setLayout(section_layout)
    
    settings_content_layout.addWidget(section_widget)
    section_widgets["统计设置"] = section_widget
