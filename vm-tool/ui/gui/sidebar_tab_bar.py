"""侧边栏 TabBar — QSS 驱动、主题感知、分组标题"""
from PyQt6.QtWidgets import QTabBar, QStylePainter, QStyleOptionTab, QStyle
from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QPainter, QFont, QColor, QPen

from app.core.theme_constants import TAB_GROUPS


class SidebarTabBar(QTabBar):
    """左侧垂直 TabBar
    - 通过 dynamicStylesheet 属性注入主题色 CSS 变量
    - paintEvent 中额外绘制分组标题
    - tabSizeHint 为分组第一个 tab 预留标题高度
    """

    GROUP_HEADER_HEIGHT = 22
    GROUP_HEADER_MARGIN_TOP = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setExpanding(False)
        self.setDrawBase(False)
        self._dynamic_stylesheet = ""
        self.setObjectName("sidebarTabBar")

    # ---- dynamic stylesheet property ----

    @property
    def dynamicStylesheet(self) -> str:
        return self._dynamic_stylesheet

    @dynamicStylesheet.setter
    def dynamicStylesheet(self, css: str):
        self._dynamic_stylesheet = css
        self.setStyleSheet(css)

    # ---- sizing ----

    def tabSizeHint(self, index: int) -> QSize:
        base = super().tabSizeHint(index)
        height = base.height()
        # 分组第一个 tab 预留标题高度
        if index in TAB_GROUPS:
            height += self.GROUP_HEADER_HEIGHT + self.GROUP_HEADER_MARGIN_TOP
        return QSize(base.width(), height)

    def minimumTabSizeHint(self, index: int) -> QSize:
        return self.tabSizeHint(index)

    # ---- paint ----

    def paintEvent(self, event):
        """绘制 tab + 分组标题"""
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        tab_count = self.count()
        if tab_count == 0:
            return

        # 绘制每个 tab
        for i in range(tab_count):
            self._paint_group_header(painter, i)
            self._paint_tab(painter, i)

    def _paint_group_header(self, painter: QStylePainter, index: int):
        """在分组第一个 tab 上方绘制标题"""
        if index not in TAB_GROUPS:
            return

        label = TAB_GROUPS[index]
        opt = QStyleOptionTab()
        self.initStyleOption(opt, index)
        tab_rect = self.tabRect(index)

        header_rect = QRect(
            tab_rect.x() + 14,
            tab_rect.y() + self.GROUP_HEADER_MARGIN_TOP,
            tab_rect.width() - 28,
            self.GROUP_HEADER_HEIGHT,
        )

        font = QFont(self.font())
        font.setPointSizeF(font.pointSizeF() * 0.75)
        font.setBold(True)
        font.setCapitalization(QFont.CapitalizeAllUppercase)
        painter.save()
        painter.setFont(font)
        # 使用与未选中文字一致的颜色 (从 palette 的 placeholder 色近似)
        c = self.palette().color(self.palette().ColorRole.PlaceholderText)
        painter.setPen(QPen(c))
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
        painter.restore()

    def _paint_tab(self, painter: QStylePainter, index: int):
        """绘制单个 tab（利用 QStyle 标准绘制 + 手动调整 rect 抵消标题偏移）"""
        opt = QStyleOptionTab()
        self.initStyleOption(opt, index)

        # 如果有分组标题，调整 tab 绘制区域向下偏移，标题绘制在偏移上方
        if index in TAB_GROUPS:
            offset = self.GROUP_HEADER_HEIGHT + self.GROUP_HEADER_MARGIN_TOP
            tab_rect = self.tabRect(index)
            adjusted_rect = QRect(
                tab_rect.x(), tab_rect.y() + offset,
                tab_rect.width(), tab_rect.height() - offset,
            )
            opt.rect = adjusted_rect

        painter.drawControl(QStyle.ControlElement.CE_TabBarTab, opt)
