"""统计分析标签页 — Dashboard 仪表盘风格"""
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QGroupBox,
    QHeaderView, QMessageBox, QSizePolicy,
)
from PyQt6.QtCore import Qt

from app.core.config_manager import config_manager
from ui.gui.widgets.stat_card import StatCard
from ui.gui.widgets.chart_widgets import BarChartWidget, PieChartWidget


logger = logging.getLogger(__name__)


class StatsTab(QWidget):
    """统计分析标签页 — Dashboard 仪表盘风格"""

    def __init__(self, parent=None, stats_service=None):
        super().__init__(parent)
        self.stats_service = stats_service
        self._init_ui()
        self.refresh_stats()

    # ── UI 构建 ──────────────────────────────────────────

    def _init_ui(self):
        """初始化 Dashboard 布局"""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 可滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # ── 顶部: 关键指标卡片 ──
        layout.addWidget(self._create_stats_cards_section())

        # ── 中间: 图表区 (2×2 网格) ──
        layout.addWidget(self._create_charts_section())

        # ── 底部: 详细数据表格 ──
        layout.addWidget(self._create_tables_section())

        # ── 刷新按钮 ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._refresh_btn = QPushButton("🔄 刷新统计")
        self._refresh_btn.clicked.connect(self.refresh_stats)
        btn_row.addWidget(self._refresh_btn)
        layout.addLayout(btn_row)

        scroll.setWidget(container)
        root_layout.addWidget(scroll)

    def _create_stats_cards_section(self) -> QWidget:
        """创建顶部指标卡片区域"""
        group = QGroupBox("关键指标")
        group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        layout = QHBoxLayout(group)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self._card_total_words = StatCard("总词条数", "0", "📝")
        self._card_total_chars = StatCard("总字符数", "0", "🔤")
        self._card_conflicts = StatCard("编码冲突", "0", "⚠️")
        self._card_avg_word_len = StatCard("平均词长", "0", "📏")
        self._card_avg_code_len = StatCard("平均编码长度", "0", "⌨️")

        for card in (
            self._card_total_words,
            self._card_total_chars,
            self._card_conflicts,
            self._card_avg_word_len,
            self._card_avg_code_len,
        ):
            layout.addWidget(card)

        return group

    def _create_charts_section(self) -> QWidget:
        """创建中间图表区域 (2×2 网格)"""
        group = QGroupBox("数据可视化")
        group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        grid = QGridLayout(group)
        grid.setContentsMargins(12, 8, 12, 8)
        grid.setSpacing(12)

        # 词长分布柱状图
        self._chart_word_length = BarChartWidget("词长分布")
        self._chart_word_length.setMinimumHeight(280)
        self._chart_word_length.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        grid.addWidget(self._chart_word_length, 0, 0)

        # 编码长度分布柱状图
        self._chart_code_length = BarChartWidget("编码长度分布")
        self._chart_code_length.setMinimumHeight(280)
        self._chart_code_length.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        grid.addWidget(self._chart_code_length, 0, 1)

        # 权重分布饼图
        self._chart_weight = PieChartWidget("权重分布")
        self._chart_weight.setMinimumHeight(280)
        self._chart_weight.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        grid.addWidget(self._chart_weight, 1, 0)

        # 编码频次 Top 10 柱状图
        self._chart_code_freq = BarChartWidget("编码频次 Top 10")
        self._chart_code_freq.setMinimumHeight(280)
        self._chart_code_freq.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        grid.addWidget(self._chart_code_freq, 1, 1)

        return group

    def _create_tables_section(self) -> QWidget:
        """创建底部详细数据表格区域"""
        group = QGroupBox("详细数据")
        group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # 编码频次分布表格
        freq_label = QLabel("编码频次分布（按频次降序）")
        freq_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        layout.addWidget(freq_label)

        self._code_freq_table = QTableWidget()
        self._code_freq_table.setColumnCount(3)
        self._code_freq_table.setHorizontalHeaderLabels(
            ["编码", "频次", "词条示例"]
        )
        self._code_freq_table.setAlternatingRowColors(True)
        self._code_freq_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._code_freq_table.verticalHeader().setVisible(False)
        self._code_freq_table.setSortingEnabled(True)
        header = self._code_freq_table.horizontalHeader()
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        # 给表格一个合理的最小高度
        self._code_freq_table.setMinimumHeight(200)
        self._code_freq_table.setMaximumHeight(350)
        layout.addWidget(self._code_freq_table)

        # 词长分布表格
        len_label = QLabel("词长分布")
        len_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        layout.addWidget(len_label)

        self._word_len_table = QTableWidget()
        self._word_len_table.setColumnCount(2)
        self._word_len_table.setHorizontalHeaderLabels(["词长", "数量"])
        self._word_len_table.setAlternatingRowColors(True)
        self._word_len_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._word_len_table.verticalHeader().setVisible(False)
        self._word_len_table.setSortingEnabled(True)
        self._word_len_table.setMinimumHeight(120)
        self._word_len_table.setMaximumHeight(200)
        layout.addWidget(self._word_len_table)

        return group

    # ── 数据刷新 ────────────────────────────────────────

    def refresh_stats(self):
        """刷新统计数据"""
        if not self.stats_service:
            return

        try:
            stats = self.stats_service.get_stats()
            word_length_stats = stats.get("word_length_stats", {})
            code_stats = stats.get("code_stats", {})
            weight_stats = stats.get("weight_stats", {})

            logger.debug(
                "统计数据: words=%s, codes=%s, weights=%s",
                bool(word_length_stats),
                bool(code_stats),
                bool(weight_stats),
            )

            # 1. 更新指标卡片
            self._update_cards(word_length_stats, code_stats)

            # 2. 更新图表
            self._update_charts(word_length_stats, code_stats, weight_stats)

            # 3. 更新表格
            self._update_tables(word_length_stats, code_stats)

        except Exception as e:
            logger.error("刷新统计数据失败: %s", e, exc_info=True)
            QMessageBox.critical(
                self, "错误", f"刷新统计数据失败: {e}"
            )

    def _update_cards(
        self, word_length_stats: dict, code_stats: dict
    ):
        """更新顶部指标卡片"""
        total_words = word_length_stats.get("total_words", 0)
        total_chars = word_length_stats.get("total_chars", 0)
        conflict_count = code_stats.get("conflict_count", 0)
        avg_word_len = word_length_stats.get("average_length", 0)

        self._card_total_words.set_value(f"{total_words:,}")
        self._card_total_chars.set_value(f"{total_chars:,}")
        self._card_conflicts.set_value(f"{conflict_count:,}")
        avg_word_text = (
            f"{avg_word_len:.2f}" if avg_word_len else "0"
        )
        self._card_avg_word_len.set_value(avg_word_text)

        # 平均编码长度
        code_length_dist = code_stats.get(
            "code_length_distribution", {}
        )
        if code_length_dist:
            total_codes = sum(code_length_dist.values())
            total_length = sum(
                int(length) * count
                for length, count in code_length_dist.items()
            )
            avg_code_len = (
                total_length / total_codes if total_codes > 0 else 0
            )
            self._card_avg_code_len.set_value(
                f"{avg_code_len:.2f}"
            )
        else:
            self._card_avg_code_len.set_value("0")

        # 冲突数趋势指示
        if conflict_count > 0:
            self._card_conflicts.set_trend(
                "存在冲突", positive=False
            )
        else:
            self._card_conflicts.set_trend("无冲突", positive=True)

    def _update_charts(
        self,
        word_length_stats: dict,
        code_stats: dict,
        weight_stats: dict,
    ):
        """更新图表数据"""
        # 词长分布柱状图
        length_dist = word_length_stats.get(
            "length_distribution", {}
        )
        if length_dist:
            self._chart_word_length.update_data(
                length_dist, color_index=0
            )

        # 编码长度分布柱状图
        code_length_dist = code_stats.get(
            "code_length_distribution", {}
        )
        if code_length_dist:
            self._chart_code_length.update_data(
                code_length_dist, color_index=1
            )

        # 权重分布饼图
        weight_dist = weight_stats.get("weight_distribution", {})
        if weight_dist:
            self._chart_weight.update_data(
                weight_dist, color_index=2
            )

        # 编码频次 Top 10 柱状图
        code_frequency = code_stats.get("code_frequency", {})
        if code_frequency:
            top_items = sorted(
                code_frequency.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]
            top_10 = dict(top_items)
            self._chart_code_freq.update_data(
                top_10, color_index=4
            )

    def _update_tables(
        self, word_length_stats: dict, code_stats: dict
    ):
        """更新表格数据"""
        # 编码频次分布表格
        code_frequency = code_stats.get("code_frequency", {})
        code_to_words = code_stats.get("code_to_words", {})
        sorted_codes = sorted(
            code_frequency.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:100]

        self._code_freq_table.setSortingEnabled(False)
        self._code_freq_table.setRowCount(len(sorted_codes))
        for i, (code, count) in enumerate(sorted_codes):
            self._code_freq_table.setItem(
                i, 0, QTableWidgetItem(code)
            )
            self._code_freq_table.setItem(
                i, 1, QTableWidgetItem(str(count))
            )
            example_words = code_to_words.get(code, [])
            if example_words:
                example_limit = config_manager.get(
                    "stats_example_limit", 20
                )
                example_text = ", ".join(
                    example_words[:example_limit]
                )
                self._code_freq_table.setItem(
                    i, 2, QTableWidgetItem(example_text)
                )
            else:
                self._code_freq_table.setItem(
                    i, 2, QTableWidgetItem("-")
                )
        self._code_freq_table.setSortingEnabled(True)

        # 词长分布表格
        length_dist = word_length_stats.get(
            "length_distribution", {}
        )
        self._word_len_table.setSortingEnabled(False)
        self._word_len_table.setRowCount(len(length_dist))
        for i, (length, count) in enumerate(
            length_dist.items()
        ):
            self._word_len_table.setItem(
                i, 0, QTableWidgetItem(str(length))
            )
            self._word_len_table.setItem(
                i, 1, QTableWidgetItem(str(count))
            )
        self._word_len_table.setSortingEnabled(True)
