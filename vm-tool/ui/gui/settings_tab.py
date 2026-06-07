"""设置标签页 - 侧边栏列表 + 卡片式内容"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QScrollArea, QLabel)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from app.core.config_manager import config_manager
from .settings import PANEL_MAP, DEFAULT_PANEL_ORDER


class SettingsTab(QWidget):
    """设置标签页 - 侧边栏列表 + 卡片式内容布局"""

    def __init__(self, parent=None, dict_service=None):
        super().__init__(parent)
        self.dict_service = dict_service
        self.panel_widgets = {}  # 面板名称 -> 面板实例
        self.init_ui()

    def init_ui(self):
        """初始化 UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧导航栏
        left_widget = QWidget()
        left_widget.setObjectName("settings_sidebar")
        left_widget.setStyleSheet("""
            #settings_sidebar {
                background-color: #f5f5f5;
                border-right: 1px solid #ddd;
            }
        """)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 8, 0, 8)
        left_layout.setSpacing(0)

        # 导航标题
        nav_title = QLabel("设置")
        nav_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        nav_title.setContentsMargins(16, 12, 16, 12)
        left_layout.addWidget(nav_title)

        # 导航列表
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("settings_nav_list")
        self.nav_list.setStyleSheet("""
            #settings_nav_list {
                border: none;
                background-color: transparent;
            }
            #settings_nav_list::item {
                padding: 10px 16px;
                border-left: 3px solid transparent;
            }
            #settings_nav_list::item:selected {
                background-color: #e0e0e0;
                border-left: 3px solid #1976d2;
            }
            #settings_nav_list::item:hover {
                background-color: #eeeeee;
            }
        """)
        self.nav_list.setDragEnabled(True)
        self.nav_list.setDropIndicatorShown(True)
        self.nav_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)

        # 从配置中加载面板顺序
        panel_order = config_manager.get("settings_order", DEFAULT_PANEL_ORDER)
        # 验证并过滤有效的面板名称
        valid_order = [name for name in panel_order if name in PANEL_MAP]
        # 添加缺失的面板
        for name in DEFAULT_PANEL_ORDER:
            if name not in valid_order:
                valid_order.append(name)

        for panel_name in valid_order:
            item = QListWidgetItem(panel_name)
            item.setSizeHint(QSize(0, 40))
            self.nav_list.addItem(item)

        # 连接拖动结束信号
        self.nav_list.model().rowsInserted.connect(self._on_nav_order_changed)
        self.nav_list.model().rowsRemoved.connect(self._on_nav_order_changed)

        left_layout.addWidget(self.nav_list)

        # 右侧内容区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 标题
        self.content_title = QLabel("设置")
        self.content_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.content_title.setContentsMargins(24, 16, 24, 8)
        right_layout.addWidget(self.content_title)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(24, 8, 24, 24)
        self.content_layout.setSpacing(16)

        # 加载所有面板
        self._load_all_panels(valid_order)

        self.content_layout.addStretch()

        self.scroll_area.setWidget(self.content_widget)
        right_layout.addWidget(self.scroll_area)

        # 添加到分割布局
        layout.addWidget(left_widget, 1)
        layout.addWidget(right_widget, 3)

        # 连接信号
        self.nav_list.currentItemChanged.connect(self._on_nav_item_changed)

        # 默认选中第一个
        if self.nav_list.count() > 0:
            self.nav_list.setCurrentRow(0)

    def _load_all_panels(self, panel_order):
        """加载所有面板"""
        for panel_name in panel_order:
            if panel_name in PANEL_MAP:
                panel_class = PANEL_MAP[panel_name]
                # 危险操作面板需要特殊处理（需要 dict_service）
                if panel_name == "危险操作":
                    panel = panel_class(parent=self, dict_service=self.dict_service)
                else:
                    panel = panel_class(parent=self)
                self.panel_widgets[panel_name] = panel
                self.content_layout.addWidget(panel)

    def _on_nav_item_changed(self, current, previous):
        """导航项选中变更"""
        if current:
            panel_name = current.text()
            self.content_title.setText(panel_name)

            # 滚动到对应的面板
            if panel_name in self.panel_widgets:
                panel = self.panel_widgets[panel_name]
                # 滚动到面板位置
                self.scroll_area.ensureWidgetVisible(panel, 0, 50)

    def _on_nav_order_changed(self, *args):
        """导航顺序改变"""
        # 获取当前的面板顺序
        order = []
        for i in range(self.nav_list.count()):
            item = self.nav_list.item(i)
            order.append(item.text())

        # 保存到配置文件
        config_manager.set("settings_order", order)

        # 重新加载面板（按新顺序）
        self._reload_panels(order)

    def _reload_panels(self, panel_order):
        """重新加载面板（按新顺序）"""
        # 移除所有现有面板
        for panel in self.panel_widgets.values():
            self.content_layout.removeWidget(panel)
            panel.deleteLater()
        self.panel_widgets.clear()

        # 按新顺序加载面板
        self._load_all_panels(panel_order)

    def save_settings(self):
        """保存设置"""
        # 配置会在修改时自动保存，这里只是显示一个提示
        parent = self.parent()
        while parent and not hasattr(parent, 'show_toast'):
            parent = parent.parent() if hasattr(parent, 'parent') else None
        if parent and hasattr(parent, 'show_toast'):
            parent.show_toast("设置已保存")
