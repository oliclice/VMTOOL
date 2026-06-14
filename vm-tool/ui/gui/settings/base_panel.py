"""设置面板基类"""

from PyQt6.QtWidgets import QGroupBox, QVBoxLayout
from PyQt6.QtCore import pyqtSignal
from app.core.config_manager import config_manager
from app.core.theme_config import ThemeConfig


class SettingsPanel(QGroupBox):
    """
    设置面板基类

    所有设置面板都应继承此类，并实现以下方法：
    - _setup_ui(): 构建 UI 布局
    - _connect_signals(): 连接信号到 config_manager
    - reload(): 从 config_manager 重新加载设置值
    """

    # 类属性：子类必须定义
    panel_name: str = ""
    panel_description: str = ""

    # 信号：设置变更时发出
    settings_changed = pyqtSignal(str, object)  # (key, value)

    def __init__(self, parent=None):
        if not self.panel_name:
            raise ValueError("子类必须定义 panel_name")
        super().__init__(parent)
        self.setObjectName(self.panel_name)
        self.setTitle(self.panel_name)
        self.setCheckable(False)

        # 主布局
        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(12, 16, 12, 12)
        self._main_layout.setSpacing(8)
        self.setLayout(self._main_layout)

        # 初始化
        self._setup_ui()
        self._connect_signals()

        # 注册到主题同步
        from ..theme_manager import theme_manager
        theme_manager.register_widget(self, self._on_theme_changed)

    def _setup_ui(self):
        """
        子类实现：构建 UI 布局

        应将所有 UI 控件添加到 self._main_layout 中
        """
        raise NotImplementedError

    def _connect_signals(self):
        """
        子类实现：连接信号到 config_manager

        在此方法中将控件的信号连接到 config_manager.set()
        """
        raise NotImplementedError

    def reload(self):
        """
        子类实现：从 config_manager 重新加载设置值

        当需要刷新界面以反映配置变化时调用
        """
        raise NotImplementedError

    def _on_theme_changed(self, _mode, _name, _color):
        """
        主题变更时调用，子类可以覆盖此方法以更新样式
        默认实现为空
        """
        pass

    def _clear_layout(self, layout):
        """递归清理布局中的所有子控件（深度优先，确保嵌套控件被删除）"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _get_config(self, key, default=None):
        """从 config_manager 获取配置值"""
        return config_manager.get(key, default)

    def _set_config(self, key, value):
        """设置 config_manager 值"""
        config_manager.set(key, value)
        self.settings_changed.emit(key, value)

    def _add_row(self, layout, label_text, widget):
        """向表单布局添加一行"""
        from PyQt6.QtWidgets import QLabel
        label = QLabel(label_text)
        layout.addRow(label, widget)
