"""缓存设置面板"""

from PyQt6.QtWidgets import QFormLayout, QLabel, QComboBox, QCheckBox
from PyQt6.QtCore import Qt

from .base_panel import SettingsPanel
from app.core.config_manager import config_manager


class CachePanel(SettingsPanel):
    """缓存设置面板 - 缓存启用、大小、过期时间"""

    panel_name = "缓存设置"
    panel_description = "配置缓存大小和过期时间"

    def _setup_ui(self):
        layout = QFormLayout()
        layout.setSpacing(12)

        # 启用缓存
        self.cache_enabled_checkbox = QCheckBox()
        layout.addRow("启用缓存:", self.cache_enabled_checkbox)

        # 缓存大小
        self.cache_size_combo = QComboBox()
        self.cache_size_combo.addItems(["10", "50", "100", "200", "500"])
        layout.addRow("缓存大小 (MB):", self.cache_size_combo)

        # 缓存过期时间
        self.cache_expiry_combo = QComboBox()
        self.cache_expiry_combo.addItems(["1h", "6h", "12h", "24h", "48h", "7d", "30d"])
        layout.addRow("缓存过期时间:", self.cache_expiry_combo)

        self._main_layout.addLayout(layout)

        # 加载当前值
        self._load_current_values()

    def _connect_signals(self):
        # 启用缓存
        self.cache_enabled_checkbox.stateChanged.connect(
            lambda state: self._set_config("cache_enabled", state == Qt.CheckState.Checked.value)
        )

        # 缓存大小
        self.cache_size_combo.currentTextChanged.connect(
            lambda text: self._set_config("cache_size", int(text))
        )

        # 缓存过期时间
        self.cache_expiry_combo.currentTextChanged.connect(self._on_expiry_changed)

    def _load_current_values(self):
        """从 config_manager 加载当前值"""
        # 启用缓存
        cache_enabled = self._get_config("cache_enabled", True)
        self.cache_enabled_checkbox.setChecked(cache_enabled)

        # 缓存大小
        cache_size = self._get_config("cache_size", 100)
        self.cache_size_combo.setCurrentText(str(cache_size))

        # 缓存过期时间
        current_expiry = self._get_config("cache_expiry", 24)
        if current_expiry == 168:  # 7天
            current_option = "7d"
        elif current_expiry == 720:  # 30天
            current_option = "30d"
        else:
            current_option = f"{current_expiry}h"

        # 找到对应的选项，如果不存在则使用默认值
        if current_option not in ["1h", "6h", "12h", "24h", "48h", "7d", "30d"]:
            current_option = "24h"

        self.cache_expiry_combo.setCurrentText(current_option)

    def _on_expiry_changed(self, text):
        """过期时间变更处理"""
        if text.endswith("d"):
            # 天数转换为小时
            hours = int(text[:-1]) * 24
        else:
            # 直接使用小时
            hours = int(text[:-1])
        self._set_config("cache_expiry", hours)

    def reload(self):
        """重新加载设置值"""
        self._load_current_values()
