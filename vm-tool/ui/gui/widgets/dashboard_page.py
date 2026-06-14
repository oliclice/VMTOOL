"""首页仪表盘组件

展示数据概览、统计卡片、图表和最近活动记录。
"""
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QSizePolicy, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton
)
from PyQt6.QtCore import Qt

from ui.gui.theme_manager import theme_manager
from ui.gui.widgets.chart_widgets import BarChartWidget, PieChartWidget
from app.core.theme_config import ThemeConfig

logger = logging.getLogger(__name__)


class DashboardPage(QWidget):
    """首页仪表盘

    布局 (从上到下):
    - Header row: 标题 "仪表盘" + 刷新按钮
    - StatCard row: 4 个统计卡片 (总字数/总词数/总字符数/编码规则数)
    - Chart row: 2 个图表 (词长分布 BarChart / 权重区间 PieChart)
    - Activity row: 最近导入/导出记录
    """

    def __init__(self, parent=None, dict_service=None, stats_service=None):
        super().__init__(parent)
        self.dict_service = dict_service
        self.stats_service = stats_service
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        # Header row
        header_layout = QHBoxLayout()
        title = QLabel("仪表盘")
        title.setStyleSheet("font-size: 22px; font-weight: 600; border: none; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setProperty("cssClass", "primary")
        self.refresh_btn.setFixedWidth(80)
        self.refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(self.refresh_btn)

        main_layout.addLayout(header_layout)

        # StatCard row
        stat_cards_layout = self._create_stat_cards()
        main_layout.addLayout(stat_cards_layout)

        # Chart row
        charts_layout = self._create_charts()
        main_layout.addLayout(charts_layout)

        # Activity row
        activity_widget = self._create_recent_activity()
        main_layout.addWidget(activity_widget, 1)

    def _create_stat_cards(self) -> QHBoxLayout:
        """创建统计卡片行"""
        layout = QHBoxLayout()
        layout.setSpacing(16)

        # 导入 StatCard
        from ui.gui.widgets.stat_card import StatCard

        self.card_total_words = StatCard("总词数", "0", "词")
        self.card_total_chars = StatCard("总字符数", "0", "字")
        self.card_special = StatCard("特殊表", "0", "◆")
        self.card_avg_length = StatCard("平均码长", "0", "📏")

        layout.addWidget(self.card_total_words, 1)
        layout.addWidget(self.card_total_chars, 1)
        layout.addWidget(self.card_special, 1)
        layout.addWidget(self.card_avg_length, 1)

        return layout

    def _create_charts(self) -> QHBoxLayout:
        """创建图表行"""
        layout = QHBoxLayout()
        layout.setSpacing(16)

        # 词长分布柱状图
        left_chart = QGroupBox("词长分布")
        left_chart.setMinimumHeight(280)
        left_layout = QVBoxLayout(left_chart)
        self.chart_word_length = BarChartWidget("词长分布")
        left_layout.addWidget(self.chart_word_length)

        # 权重区间分布饼图
        right_chart = QGroupBox("权重区间分布")
        right_chart.setMinimumHeight(280)
        right_layout = QVBoxLayout(right_chart)
        self.chart_weight_dist = PieChartWidget("权重区间分布")
        right_layout.addWidget(self.chart_weight_dist)

        layout.addWidget(left_chart, 1)
        layout.addWidget(right_chart, 1)

        return layout

    def _create_recent_activity(self) -> QGroupBox:
        """创建最近活动记录"""
        group = QGroupBox("最近活动")
        group.setMinimumHeight(200)

        layout = QVBoxLayout(group)

        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["时间", "操作", "详情", "状态"])
        self.activity_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.activity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.activity_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.activity_table.verticalHeader().setVisible(False)
        self._show_activity_placeholder()
        layout.addWidget(self.activity_table)

        return group

    def _show_activity_placeholder(self):
        """在活动表格中显示占位提示"""
        self.activity_table.setRowCount(1)
        placeholder = QTableWidgetItem("暂无活动记录")
        placeholder.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setFlags(Qt.ItemFlag.NoItemFlags)  # 不可选中/编辑
        self.activity_table.setItem(0, 0, placeholder)
        # 合并整行显示提示文字
        self.activity_table.setSpan(0, 0, 1, 4)

    def refresh(self):
        """从 dict_service / stats_service 获取数据并更新显示"""
        if not self.dict_service:
            return

        try:
            # ── 统计卡片（来自 dict_service） ──
            chars = self.dict_service.get_characters()
            self.card_total_chars.set_value(str(len(chars) if chars else 0))

            words = self.dict_service.get_all_words()
            self.card_total_words.set_value(str(len(words) if words else 0))

            special = self.dict_service.get_special_chars()
            self.card_special.set_value(str(len(special) if special else 0))

            if words:
                total_length = sum(len(w.get("code", "")) for w in words if w.get("code"))
                avg_length = total_length / len(words) if words else 0
                self.card_avg_length.set_value(f"{avg_length:.1f}")
            else:
                self.card_avg_length.set_value("0")

            # ── 图表数据（来自 stats_service） ──
            if self.stats_service:
                stats = self.stats_service.get_stats()
                word_length_stats = stats.get("word_length_stats", {})
                weight_stats = stats.get("weight_stats", {})

                # 词长分布柱状图
                length_dist = word_length_stats.get("length_distribution", {})
                if length_dist:
                    # 按键（词长）排序
                    sorted_dist = dict(sorted(length_dist.items(), key=lambda x: int(x[0])))
                    self.chart_word_length.update_data(sorted_dist, color_index=0)

                # 权重区间分布饼图
                weight_dist = weight_stats.get("weight_distribution", {})
                if weight_dist:
                    self.chart_weight_dist.update_data(weight_dist, color_index=2)

        except Exception as e:
            logger.error("Dashboard refresh error: %s", e, exc_info=True)

    def _apply_style(self):
        """应用主题感知的样式"""
        palette = ThemeConfig.get_palette(
            theme_manager.current_theme_name,
            theme_manager.current_theme_mode,
            theme_manager.current_theme_color
        )

        self.setStyleSheet(f"""
            DashboardPage {{
                background-color: {palette.bg_primary};
            }}
        """)


class DashboardActivityItem(QWidget):
    """单个活动记录项"""

    def __init__(self, time: str, action: str, detail: str, status: str, parent=None):
        super().__init__(parent)
        self._setup_ui(time, action, detail, status)

    def _setup_ui(self, time: str, action: str, detail: str, status: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        time_label = QLabel(time)
        time_label.setFixedWidth(120)
        layout.addWidget(time_label)

        action_label = QLabel(action)
        action_label.setFixedWidth(80)
        layout.addWidget(action_label)

        detail_label = QLabel(detail)
        layout.addWidget(detail_label, 1)

        status_label = QLabel(status)
        layout.addWidget(status_label)
