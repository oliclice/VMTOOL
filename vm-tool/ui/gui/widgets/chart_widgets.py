"""图表封装组件 — 基于 Qt Charts 的柱状图和饼图"""
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCharts import (
    QChart,
    QChartView,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis,
    QPieSeries,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter

from ui.gui.theme_colors import _is_dark_mode, _is_linear_theme


# ── 图表调色板 ──────────────────────────────────────────────
_DARK_PALETTE = [
    "#7170ff", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
    "#06b6d4", "#f97316", "#ec4899", "#14b8a6", "#6366f1",
]
_LIGHT_PALETTE = [
    "#5e6ad2", "#27a644", "#d97706", "#ef4444", "#7c3aed",
    "#0891b2", "#ea580c", "#db2777", "#0d9488", "#4f46e5",
]


def _chart_colors() -> Tuple[str, str, str, str]:
    """返回当前主题的 (背景, 文字, 网格, 边框) 颜色"""
    is_dark = _is_dark_mode()
    is_linear = _is_linear_theme()
    if is_linear:
        if is_dark:
            bg = "#0f1011"
            text = "#d0d6e0"
            grid = "rgba(255,255,255,0.04)"
            border = "rgba(255,255,255,0.06)"
            return bg, text, grid, border
        return (
            "#f7f8f8", "#1a1a2e",
            "rgba(0,0,0,0.04)", "rgba(0,0,0,0.06)",
        )
    if is_dark:
        return (
            "#1e1e1e", "#e0e0e0",
            "rgba(255,255,255,0.08)", "rgba(255,255,255,0.1)",
        )
    return (
        "#ffffff", "#333333",
        "rgba(0,0,0,0.06)", "rgba(0,0,0,0.08)",
    )


def _palette() -> List[str]:
    return _DARK_PALETTE if _is_dark_mode() else _LIGHT_PALETTE


def _contrast_text_color(bg_hex: str) -> QColor:
    """根据背景色返回高对比度文字色（纯白或纯黑）

    使用 WCAG 2.0 相对亮度公式：
    L = 0.2126*R + 0.7152*G + 0.0722*B
    亮度 > 0.179 用黑字，否则用白字。
    """
    c = QColor(bg_hex)
    r, g, b = c.redF(), c.greenF(), c.blueF()
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return QColor("#000000") if luminance > 0.179 else QColor("#ffffff")


def _configure_chart(chart: QChart):
    """通用图表配置"""
    bg, text, grid, border = _chart_colors()
    chart.setBackgroundVisible(False)
    chart.setPlotAreaBackgroundVisible(False)
    chart.setTitleBrush(QBrush(QColor(text)))
    chart.legend().setLabelColor(QColor(text))
    chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
    chart.setAnimationOptions(
        QChart.AnimationOption.SeriesAnimations
    )
    chart.setDropShadowEnabled(False)
    # 设置图表边距，让数据标签有空间显示
    chart.setContentsMargins(-5, -5, -5, -5)


class BarChartWidget(QChartView):
    """柱状图组件 — 每个柱子顶部显示数值

    用于展示: 词长分布、编码长度分布、编码频次 Top N
    """

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._chart = QChart()
        self._chart.setTitle(title)
        _configure_chart(self._chart)
        self.setChart(self._chart)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._series: Optional[QBarSeries] = None
        self._categories: List[str] = []
        self._axis_x: Optional[QBarCategoryAxis] = None
        self._axis_y: Optional[QValueAxis] = None

    def update_data(
        self, data: Dict[str, int], color_index: int = 0
    ):
        """更新柱状图数据

        Args:
            data: {标签: 数值} 字典，如 {"1": 120, "2": 340}
            color_index: 调色板起始索引
        """
        if not data:
            return

        # 清除旧系列
        self._chart.removeAllSeries()
        if self._axis_x:
            self._chart.removeAxis(self._axis_x)
        if self._axis_y:
            self._chart.removeAxis(self._axis_y)

        # 排序
        sorted_items = sorted(
            data.items(), key=lambda x: (x[0], x[1])
        )
        self._categories = [str(k) for k, _ in sorted_items]
        values = [v for _, v in sorted_items]

        # 创建 BarSet — 高饱和度颜色
        palette = _palette()
        color = QColor(palette[color_index % len(palette)])
        bar_set = QBarSet("")
        bar_set.setColor(color)
        bar_set.setBorderColor(color.darker(130))
        for v in values:
            bar_set.append(v)

        self._series = QBarSeries()
        self._series.append(bar_set)
        self._series.setBarWidth(0.65)
        # 在柱子顶部显示数值标签
        self._series.setLabelsVisible(True)
        self._series.setLabelsPosition(
            QBarSeries.LabelsPosition.LabelsOutsideEnd
        )
        label_font = QFont()
        label_font.setPixelSize(10)
        label_font.setBold(True)
        bar_set.setLabelFont(label_font)
        # 柱子上的文字用高对比度色（根据柱子背景色自动选白/黑）
        bar_set.setLabelColor(_contrast_text_color(
            palette[color_index % len(palette)]
        ))

        self._chart.addSeries(self._series)

        # 获取主题色用于坐标轴
        _, text, grid, _ = _chart_colors()

        # X 轴 — 分类
        self._axis_x = QBarCategoryAxis()
        self._axis_x.append(self._categories)
        axis_font = QFont()
        axis_font.setPixelSize(10)
        self._axis_x.setLabelsColor(QColor(text))
        self._axis_x.setLabelsFont(axis_font)
        self._axis_x.setGridLineColor(QColor(grid))
        self._chart.addAxis(
            self._axis_x, Qt.AlignmentFlag.AlignBottom
        )
        self._series.attachAxis(self._axis_x)

        # Y 轴 — 数值
        self._axis_y = QValueAxis()
        self._axis_y.setLabelsColor(QColor(text))
        self._axis_y.setLabelsFont(axis_font)
        self._axis_y.setGridLineColor(QColor(grid))
        self._axis_y.setMinorGridLineVisible(False)
        if values:
            self._axis_y.setRange(0, max(values) * 1.25)
        self._chart.addAxis(
            self._axis_y, Qt.AlignmentFlag.AlignLeft
        )
        self._series.attachAxis(self._axis_y)

    def set_title(self, title: str):
        self._chart.setTitle(title)


class PieChartWidget(QChartView):
    """饼图组件 — 环形图 + 百分比标签

    用于展示: 权重区间分布
    """

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._chart = QChart()
        self._chart.setTitle(title)
        _configure_chart(self._chart)
        self.setChart(self._chart)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._series: Optional[QPieSeries] = None

    def update_data(
        self, data: Dict[str, int], color_index: int = 0
    ):
        """更新饼图数据

        Args:
            data: {标签: 数值} 字典，如 {"0-10": 500, "10-20": 300}
            color_index: 调色板起始索引
        """
        if not data:
            return

        self._chart.removeAllSeries()

        palette = _palette()
        self._series = QPieSeries()
        self._series.setHoleSize(0.40)  # 环形图
        self._series.setPieSize(0.92)   # 充满图表区域

        total = sum(data.values())
        bg = _chart_colors()[0]
        label_font = QFont()
        label_font.setPixelSize(11)
        label_font.setBold(True)

        for i, (label, value) in enumerate(data.items()):
            if value <= 0:
                continue
            color = QColor(
                palette[(color_index + i) % len(palette)]
            )
            slice_ = self._series.append(
                f"{label}: {value}", value
            )
            slice_.setColor(color)
            slice_.setBorderColor(QColor(bg))

            # 百分比标签 — 高对比度文字
            pct = (value / total * 100) if total > 0 else 0
            slice_.setLabelFont(label_font)
            slice_.setLabelColor(_contrast_text_color(
                palette[(color_index + i) % len(palette)]
            ))
            if pct >= 4:
                slice_.setLabel(f"{label}\n{pct:.1f}%")
                slice_.setLabelVisible(True)
            else:
                slice_.setLabel(f"{pct:.1f}%")
                slice_.setLabelVisible(True)

        self._chart.addSeries(self._series)

    def set_title(self, title: str):
        self._chart.setTitle(title)
