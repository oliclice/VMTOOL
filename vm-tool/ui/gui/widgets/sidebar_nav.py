"""侧边栏导航组件

提供 Finder-like 的导航体验，支持分组、选中态、主题响应。
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class NavItem(QWidget):
    """单个导航项

    结构: [3px indicator] [icon] [label]
    - 未选中: indicator 透明, 文字 muted
    - 选中: indicator accent 色, 文字 primary, 背景 rgba_selection
    - hover: 背景 rgba_surface_hover
    """
    clicked = pyqtSignal(int)  # page_index

    def __init__(self, icon: str, label: str, page_index: int, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        self._active = False
        self._setup_ui(icon, label)

    def _setup_ui(self, icon: str, label: str):
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        # 左侧指示器
        self.indicator = QFrame()
        self.indicator.setFixedWidth(3)
        self.indicator.setFixedHeight(16)
        self.indicator.setVisible(False)
        layout.addWidget(self.indicator)

        # 图标
        self.icon_label = QLabel(icon)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedWidth(20)
        layout.addWidget(self.icon_label)

        # 文字
        self.text_label = QLabel(label)
        layout.addWidget(self.text_label, 1)

        self.setObjectName("NavItem")

    def set_active(self, active: bool):
        """设置选中态"""
        self._active = active
        self.setProperty("active", active)
        self.indicator.setVisible(active)
        # 强制刷新样式
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.page_index)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if not self._active:
            self.setStyleSheet("background-color: rgba(255,255,255,0.04);")
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._active:
            self.setStyleSheet("")
        super().leaveEvent(event)


class GroupLabel(QWidget):
    """导航分组标签

    - 全大写/字间距
    - 11px (Linear) / 12px (M3)
    - muted 色
    """

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._setup_ui(text)

    def _setup_ui(self, text: str):
        self.setFixedHeight(28)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 4)
        layout.setSpacing(0)

        self.label = QLabel(text.upper())
        font = QFont()
        font.setPixelSize(11)
        font.setWeight(QFont.Weight.DemiBold)
        self.label.setFont(font)
        layout.addWidget(self.label)

        self.setObjectName("GroupLabel")


class SidebarNav(QWidget):
    """侧边栏导航容器

    信号:
        nav_changed(int)  # page_index

    公开方法:
        add_group(label: str)
        add_item(icon: str, label: str, page_index: int)
        add_separator()
        set_active(page_index: int)
        add_bottom_widget(widget: QWidget)
    """
    nav_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[NavItem] = []
        self._current_index = -1
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("SidebarNav")

        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Brand header
        self.brand_header = QLabel("VMtool")
        self.brand_header.setFixedHeight(40)
        self.brand_header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.main_layout.addWidget(self.brand_header)

        # 内容区域 (可滚动)
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(2)

        # 弹性 spacer
        self.content_layout.addStretch(1)

        self.main_layout.addLayout(self.content_layout, 1)

    def add_group(self, label: str):
        """添加导航分组标签"""
        group = GroupLabel(label)
        self.content_layout.insertWidget(self.content_layout.count() - 1, group)

    def add_item(self, icon: str, label: str, page_index: int):
        """添加导航项"""
        item = NavItem(icon, label, page_index)
        item.clicked.connect(self._on_item_clicked)
        self._items.append(item)
        self.content_layout.insertWidget(self.content_layout.count() - 1, item)

    def add_separator(self):
        """添加分隔线"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(255,255,255,0.06); margin: 8px 14px;")
        self.content_layout.insertWidget(self.content_layout.count() - 1, separator)

    def add_bottom_widget(self, widget: QWidget):
        """添加底部 widget (如版本号)"""
        self.main_layout.addWidget(widget)

    def set_active(self, page_index: int):
        """设置选中态"""
        if self._current_index == page_index:
            return

        # 取消旧选中
        for item in self._items:
            item.set_active(False)

        # 设置新选中
        for item in self._items:
            if item.page_index == page_index:
                item.set_active(True)
                self._current_index = page_index
                break

    def _on_item_clicked(self, page_index: int):
        self.set_active(page_index)
        self.nav_changed.emit(page_index)
