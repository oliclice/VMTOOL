"""统计设置面板"""

from PyQt6.QtWidgets import QFormLayout, QComboBox, QCheckBox
from PyQt6.QtCore import Qt

from .base_panel import SettingsPanel
from app.core.config_manager import config_manager


class StatsPanel(SettingsPanel):
    """统计设置面板 - 启用统计、统计周期"""

    panel_name = "统计设置"
    panel_description = "配置统计数据收集和统计周期"

    def _setup_ui(self):
        layout = QFormLayout()
        layout.setSpacing(12)

        # 启用统计
        self.stats_enabled_checkbox = QCheckBox()
        layout.addRow("启用统计:", self.stats_enabled_checkbox)

        # 统计周期
        self.stats_period_combo = QComboBox()
        self.stats_period_combo.addItems(["每日", "每周", "每月"])
        layout.addRow("统计周期:", self.stats_period_combo)

        self._main_layout.addLayout(layout)

        # 加载当前值
        self._load_current_values()

    def _connect_signals(self):
        # 启用统计
        self.stats_enabled_checkbox.stateChanged.connect(
            lambda state: self._set_config("stats_enabled", state == Qt.CheckState.Checked.value)
        )

        # 统计周期
        self.stats_period_combo.currentTextChanged.connect(
            lambda text: self._set_config("stats_period", text)
        )

    def _load_current_values(self):
        """从 config_manager 加载当前值"""
        # 启用统计
        stats_enabled = self._get_config("stats_enabled", True)
        self.stats_enabled_checkbox.setChecked(stats_enabled)

        # 统计周期
        stats_period = self._get_config("stats_period", "每日")
        self.stats_period_combo.setCurrentText(stats_period)

    def reload(self):
        """重新加载设置值"""
        self._load_current_values()
