"""外观设置面板 - 合并主题、语言、字体设置"""

from PyQt6.QtWidgets import QFormLayout, QLabel, QComboBox
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication

from .base_panel import SettingsPanel
from app.core.config_manager import config_manager
from app.core.theme_constants import (
    THEME_MODE_AUTO, THEME_MODE_LIGHT, THEME_MODE_DARK,
    THEME_NAME_CLASSIC, THEME_NAME_MATERIAL3, THEME_NAME_LINEAR,
    THEME_COLOR_BLUE, THEME_COLOR_GREEN,
    THEME_COLOR_RED, THEME_COLOR_PURPLE, THEME_COLOR_ORANGE,
    MODE_DISPLAY_MAP, MODE_DISPLAY_REVERSE_MAP
)


class AppearancePanel(SettingsPanel):
    """外观设置面板 - 主题、模式、颜色、语言、字体"""

    panel_name = "外观设置"
    panel_description = "主题风格、显示模式、语言和字体"

    def _setup_ui(self):
        layout = QFormLayout()
        layout.setSpacing(12)

        # 主题选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            THEME_NAME_CLASSIC,
            THEME_NAME_MATERIAL3,
            THEME_NAME_LINEAR
        ])
        layout.addRow("主题:", self.theme_combo)

        # 模式选择
        self.mode_combo = QComboBox()
        mode_display_names = [
            MODE_DISPLAY_MAP[THEME_MODE_AUTO],
            MODE_DISPLAY_MAP[THEME_MODE_LIGHT],
            MODE_DISPLAY_MAP[THEME_MODE_DARK]
        ]
        self.mode_combo.addItems(mode_display_names)
        layout.addRow("模式:", self.mode_combo)

        # 主题颜色
        self.color_combo = QComboBox()
        self.color_combo.addItems([
            THEME_COLOR_BLUE, THEME_COLOR_GREEN, THEME_COLOR_RED,
            THEME_COLOR_PURPLE, THEME_COLOR_ORANGE
        ])
        layout.addRow("主题颜色:", self.color_combo)

        # 分隔线（通过添加一个空行模拟）
        separator_label = QLabel("")
        separator_label.setFixedHeight(1)
        layout.addRow("", separator_label)

        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "English"])
        layout.addRow("语言:", self.language_combo)

        # 字体选择
        self.font_combo = QComboBox()
        font_families = QFontDatabase.families()
        self.font_combo.addItems(font_families)
        layout.addRow("字体:", self.font_combo)

        self._main_layout.addLayout(layout)

        # 加载当前值
        self._load_current_values()

    def _connect_signals(self):
        # 主题相关信号
        self.theme_combo.currentTextChanged.connect(self._on_theme_selection_changed)
        self.mode_combo.currentTextChanged.connect(self._on_theme_selection_changed)
        self.color_combo.currentTextChanged.connect(self._on_theme_selection_changed)

        # 语言信号
        self.language_combo.currentTextChanged.connect(
            lambda text: self._set_config("language", text)
        )

        # 字体信号
        self.font_combo.currentTextChanged.connect(self._on_font_changed)

    def _load_current_values(self):
        """从 config_manager 加载当前值"""
        # 主题
        current_theme = self._get_config("theme_name", THEME_NAME_CLASSIC)
        self.theme_combo.setCurrentText(current_theme)

        # 模式
        current_mode = self._get_config("theme_mode", THEME_MODE_AUTO)
        display_mode = MODE_DISPLAY_MAP.get(current_mode, MODE_DISPLAY_MAP[THEME_MODE_AUTO])
        self.mode_combo.setCurrentText(display_mode)

        # 颜色
        current_color = self._get_config("theme_color", THEME_COLOR_BLUE)
        self.color_combo.setCurrentText(current_color)

        # 语言
        current_language = self._get_config("language", "中文")
        self.language_combo.setCurrentText(current_language)

        # 字体
        current_font = self._get_config("font_family", "")
        if current_font:
            self.font_combo.setCurrentText(current_font)

    def _on_theme_selection_changed(self):
        """主题选择变更处理（UI 交互）"""
        # 阻塞信号以防止循环调用
        self.theme_combo.blockSignals(True)
        self.mode_combo.blockSignals(True)
        self.color_combo.blockSignals(True)

        try:
            theme = self.theme_combo.currentText()
            mode_display = self.mode_combo.currentText()
            color = self.color_combo.currentText()

            # 映射模式显示名称到内部值
            internal_mode = MODE_DISPLAY_REVERSE_MAP.get(mode_display, THEME_MODE_AUTO)

            # 保存设置
            self._set_config("theme_name", theme)
            self._set_config("theme_mode", internal_mode)
            self._set_config("theme_color", color)

            # 应用主题
            from ..theme_manager import theme_manager
            theme_manager.set_theme(internal_mode, theme, color)

            # 显示提示
            parent = self.parent()
            while parent and not hasattr(parent, 'show_toast'):
                parent = parent.parent() if hasattr(parent, 'parent') else None
            if parent and hasattr(parent, 'show_toast'):
                parent.show_toast(f"主题已更改为：{theme} - {mode_display} - {color}")
        finally:
            # 恢复信号
            self.theme_combo.blockSignals(False)
            self.mode_combo.blockSignals(False)
            self.color_combo.blockSignals(False)

    def _on_font_changed(self, font_family):
        """字体变更处理"""
        self._set_config("font_family", font_family)

        # 应用字体到整个应用
        font = QFont(font_family)
        QApplication.instance().setFont(font)

        # 显示提示
        parent = self.parent()
        while parent and not hasattr(parent, 'show_toast'):
            parent = parent.parent() if hasattr(parent, 'parent') else None
        if parent and hasattr(parent, 'show_toast'):
            parent.show_toast(f"字体已更改为: {font_family}")

    def _on_theme_changed(self, mode, name, color):
        """主题变更通知回调"""
        # 重新加载当前值以反映外部主题变更
        self._load_current_values()

    def reload(self):
        """重新加载设置值"""
        self._load_current_values()
