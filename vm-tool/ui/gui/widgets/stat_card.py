"""统计指标卡片组件 — 用于 Dashboard 仪表盘顶部的关键指标展示"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

from ui.gui.theme_manager import theme_manager
from ui.gui.theme_colors import _is_dark_mode, _is_linear_theme


class StatCard(QWidget):
    """单个统计指标卡片

    布局:
    ┌─────────────────────┐
    │  📊 标题             │  ← 小字，secondary 色
    │  12,345             │  ← 大字，primary 色
    │  ▲ +2.3% 较上周     │  ← 可选趋势
    └─────────────────────┘
    """

    def __init__(self, title: str, value: str = "0", icon: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._setup_ui()
        self.set_value(value)
        self._apply_style()
        # 监听主题变更
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        # 标题行: 图标 + 标题
        title_text = f"{self._icon}  {self._title}" if self._icon else self._title
        self._title_label = QLabel(title_text)
        self._title_label.setObjectName("stat_card_title")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._title_label)

        # 数值
        self._value_label = QLabel("0")
        self._value_label.setObjectName("stat_card_value")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._value_label)

        # 趋势（可选）
        self._trend_label = QLabel("")
        self._trend_label.setObjectName("stat_card_trend")
        self._trend_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._trend_label)

        self.setMinimumWidth(140)
        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            self.sizePolicy().verticalPolicy(),
        )

    def set_value(self, value: str):
        """设置显示数值"""
        self._value_label.setText(str(value))

    def set_trend(self, text: str, positive: bool = True):
        """设置趋势指示

        Args:
            text: 趋势文字，如 "+2.3% 较上周"
            positive: True 为正向（绿色），False 为负向（红色）
        """
        if text:
            prefix = "▲ " if positive else "▼ "
            self._trend_label.setText(f"{prefix}{text}")
            self._trend_label.setProperty("positive", positive)
            self._trend_label.setVisible(True)
        else:
            self._trend_label.setVisible(False)

    def _apply_style(self):
        """应用主题感知的样式"""
        is_dark = _is_dark_mode()
        is_linear = _is_linear_theme()

        if is_linear:
            if is_dark:
                bg = "#191a1b"
                border = "rgba(255, 255, 255, 0.06)"
                title_color = "#8a8f98"
                value_color = "#f7f8f8"
                trend_pos_color = "#10b981"
                trend_neg_color = "#f87171"
            else:
                bg = "#ffffff"
                border = "rgba(0, 0, 0, 0.06)"
                title_color = "#62666d"
                value_color = "#1a1a2e"
                trend_pos_color = "#27a644"
                trend_neg_color = "#ef4444"
        else:
            if is_dark:
                bg = "#2d2d2d"
                border = "rgba(255, 255, 255, 0.1)"
                title_color = "#aaaaaa"
                value_color = "#ffffff"
                trend_pos_color = "#66BB6A"
                trend_neg_color = "#EF5350"
            else:
                bg = "#ffffff"
                border = "rgba(0, 0, 0, 0.08)"
                title_color = "#666666"
                value_color = "#333333"
                trend_pos_color = "#4CAF50"
                trend_neg_color = "#F44336"

        self.setStyleSheet(f"""
            StatCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            StatCard:hover {{
                border-color: rgba(94, 106, 210, 0.3);
            }}
            #stat_card_title {{
                color: {title_color};
                font-size: 12px;
                font-weight: 500;
                border: none;
                background: transparent;
            }}
            #stat_card_value {{
                color: {value_color};
                font-size: 26px;
                font-weight: 700;
                border: none;
                background: transparent;
            }}
            #stat_card_trend {{
                color: {trend_pos_color};
                font-size: 11px;
                border: none;
                background: transparent;
            }}
            #stat_card_trend[positive="false"] {{
                color: {trend_neg_color};
            }}
        """)

    def _on_theme_changed(self, _mode, _name, _color):
        """主题变更时重新应用样式"""
        self._apply_style()
