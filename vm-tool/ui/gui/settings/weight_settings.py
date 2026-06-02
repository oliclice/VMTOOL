from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QFormLayout, QLabel, QCheckBox)
from PyQt6.QtCore import Qt
from app.core.config_manager import config_manager

def load_weight_settings(settings_content_layout, section_widgets, parent):
    """加载权重计算设置"""
    section_widget = QGroupBox("权重计算")
    section_layout = QVBoxLayout()

    # 权重计算设置
    weight_layout = QFormLayout()

    # 标题说明
    title_label = QLabel("自动计算权重时的码表范围:")
    title_label.setStyleSheet("font-weight: bold;")

    # 词表选项（默认勾选）
    words_checkbox = QCheckBox("词表 (常用词汇)")
    words_checkbox.setChecked(config_manager.get("weight_calc_words", True))
    words_checkbox.stateChanged.connect(lambda state: config_manager.set("weight_calc_words", state == 2))

    # 字表选项（默认不勾选）
    chars_checkbox = QCheckBox("字表 (单字)")
    chars_checkbox.setChecked(config_manager.get("weight_calc_chars", False))
    chars_checkbox.stateChanged.connect(lambda state: config_manager.set("weight_calc_chars", state == 2))

    # 特殊表选项（默认不勾选）
    special_checkbox = QCheckBox("特殊表 (特殊字符)")
    special_checkbox.setChecked(config_manager.get("weight_calc_special", False))
    special_checkbox.stateChanged.connect(lambda state: config_manager.set("weight_calc_special", state == 2))

    # 说明信息
    info_label = QLabel("说明: 勾选的码表类型将在自动计算权重时被处理。手动设置权重的词条会被跳过。")
    info_label.setStyleSheet("color: gray; font-size: 11px;")
    info_label.setWordWrap(True)

    weight_layout.addRow(title_label)
    weight_layout.addRow(words_checkbox)
    weight_layout.addRow(chars_checkbox)
    weight_layout.addRow(special_checkbox)
    weight_layout.addRow(info_label)

    section_layout.addLayout(weight_layout)
    section_widget.setLayout(section_layout)

    settings_content_layout.addWidget(section_widget)
    section_widgets["权重计算"] = section_widget
