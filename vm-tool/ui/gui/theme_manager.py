"""主题管理器，统一处理主题变更和应用"""
import logging
import os
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from typing import Tuple

from app.core.theme_constants import (
    THEME_MODE_AUTO, THEME_MODE_LIGHT, THEME_MODE_DARK,
    THEME_NAME_CLASSIC, THEME_NAME_LINEAR, THEME_NAME_MATERIAL3,
    THEME_COLOR_BLUE
)
from app.core.theme_config import ThemeConfig
from .theme_utils import get_theme_stylesheet

logger = logging.getLogger(__name__)


class ThemeManager(QObject):
    """主题管理器，负责主题变更信号和应用"""

    theme_changed = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.current_theme_mode = THEME_MODE_AUTO
        self.current_theme_name = THEME_NAME_CLASSIC
        self.current_theme_color = THEME_COLOR_BLUE

        # 延迟导入避免循环依赖
        self._theme_sync = None

    def _get_theme_sync(self):
        """获取 ThemeSync 实例（延迟初始化）"""
        if self._theme_sync is None:
            from .theme_sync import theme_sync
            self._theme_sync = theme_sync
            theme_sync.set_theme_manager(self)
        return self._theme_sync

    def get_current_theme(self) -> Tuple[str, str, str]:
        """获取当前主题设置"""
        return (
            self.current_theme_mode,
            self.current_theme_name,
            self.current_theme_color
        )

    def set_theme(self, theme_mode: str, theme_name: str, theme_color: str) -> None:
        """设置主题并发出信号"""
        if (theme_mode != self.current_theme_mode or
            theme_name != self.current_theme_name or
            theme_color != self.current_theme_color):

            self.current_theme_mode = theme_mode
            self.current_theme_name = theme_name
            self.current_theme_color = theme_color

            logger.info(f"Theme changed: mode={theme_mode}, name={theme_name}, color={theme_color}")

            self.theme_changed.emit(theme_mode, theme_name, theme_color)
            self.apply_theme_to_application()

    def apply_theme_to_application(self) -> None:
        """将当前主题应用到整个应用程序"""
        app = QApplication.instance()
        if not app:
            return

        # 使用 ThemeConfig 创建调色板
        palette = ThemeConfig.get_qpalette(
            self.current_theme_name,
            self.current_theme_mode,
            self.current_theme_color
        )

        app.setPalette(palette)

        # 根据主题名称选择 QSS 样式表
        if self.current_theme_name == THEME_NAME_LINEAR:
            qss = get_theme_stylesheet(
                self.current_theme_mode,
                self.current_theme_color,
                self.current_theme_name
            )
            if qss:
                app.setStyleSheet(qss)
        elif self.current_theme_name == THEME_NAME_MATERIAL3:
            # Material3 主题使用 QSS
            palette_obj = ThemeConfig.get_palette(
                self.current_theme_name,
                self.current_theme_mode,
                self.current_theme_color
            )
            from .styles.theme_variables import resolve_qss_variables
            qss_path = os.path.join(os.path.dirname(__file__), "styles", "material_theme.qss")
            with open(qss_path, "r", encoding="utf-8") as f:
                qss = f.read()
            qss = resolve_qss_variables(qss, palette_obj)
            app.setStyleSheet(qss)
        else:
            # 经典主题不使用 QSS，仅依赖 QPalette
            app.setStyleSheet("")

        # 更新所有顶级窗口
        for window in app.topLevelWidgets():
            if hasattr(window, 'setPalette'):
                window.setPalette(palette)
                if hasattr(window, 'update'):
                    window.update()

    def register_widget(self, widget, callback=None) -> None:
        """注册窗口部件以自动更新主题

        Args:
            widget: 要注册的 QWidget
            callback: 可选的回调函数
        """
        theme_sync = self._get_theme_sync()
        theme_sync.register_widget(widget, callback)

    def unregister_widget(self, widget) -> None:
        """取消注册窗口部件"""
        theme_sync = self._get_theme_sync()
        theme_sync.unregister_widget(widget)


theme_manager = ThemeManager()
