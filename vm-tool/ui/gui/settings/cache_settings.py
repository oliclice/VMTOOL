from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QFormLayout, QLabel, QComboBox, QCheckBox) 
from PyQt6.QtCore import Qt
from app.core.config_manager import config_manager

def load_cache_settings(settings_content_layout, section_widgets, parent):
    """加载缓存设置"""
    section_widget = QGroupBox("缓存设置")
    section_layout = QVBoxLayout()
    
    # 缓存设置
    cache_layout = QFormLayout()
    
    # 启用缓存
    cache_enabled_label = QLabel("启用缓存:")
    cache_enabled_checkbox = QCheckBox()
    cache_enabled_checkbox.setChecked(config_manager.get("cache_enabled", True))
    # 连接信号，自动保存
    cache_enabled_checkbox.stateChanged.connect(lambda state: config_manager.set("cache_enabled", state == 2))
    
    # 缓存大小
    cache_size_label = QLabel("缓存大小 (MB):")
    cache_size_combo = QComboBox()
    cache_size_combo.addItems(["10", "50", "100", "200", "500"])
    cache_size_combo.setCurrentText(str(config_manager.get("cache_size", 100)))
    # 连接信号，自动保存
    cache_size_combo.currentTextChanged.connect(lambda text: config_manager.set("cache_size", int(text)))
    
    # 缓存过期时间
    cache_expiry_label = QLabel("缓存过期时间:")
    cache_expiry_combo = QComboBox()
    cache_expiry_combo.addItems(["1h", "6h", "12h", "24h", "48h", "7d", "30d"])
    
    # 转换当前值为对应选项
    current_expiry = config_manager.get("cache_expiry", 24)
    if current_expiry == 168:  # 7天
        current_option = "7d"
    elif current_expiry == 720:  # 30天
        current_option = "30d"
    else:
        current_option = f"{current_expiry}h"
    
    # 找到对应的选项，如果不存在则使用默认值
    if current_option not in ["1h", "6h", "12h", "24h", "48h", "7d", "30d"]:
        current_option = "24h"
    
    cache_expiry_combo.setCurrentText(current_option)
    
    # 连接信号，自动保存
    def on_cache_expiry_changed(text):
        if text.endswith("d"):
            # 天数转换为小时
            hours = int(text[:-1]) * 24
        else:
            # 直接使用小时
            hours = int(text[:-1])
        config_manager.set("cache_expiry", hours)
    
    cache_expiry_combo.currentTextChanged.connect(on_cache_expiry_changed)
    
    cache_layout.addRow(cache_enabled_label, cache_enabled_checkbox)
    cache_layout.addRow(cache_size_label, cache_size_combo)
    cache_layout.addRow(cache_expiry_label, cache_expiry_combo)
    
    section_layout.addLayout(cache_layout)
    section_widget.setLayout(section_layout)
    
    settings_content_layout.addWidget(section_widget)
    section_widgets["缓存设置"] = section_widget
