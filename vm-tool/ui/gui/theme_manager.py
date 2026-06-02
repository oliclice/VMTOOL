"""主题管理器，统一处理主题变更和应用"""
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from typing import Tuple

from app.core.theme_constants import (
    THEME_MODE_AUTO, THEME_MODE_LIGHT, THEME_MODE_DARK,
    THEME_NAME_CLASSIC, THEME_NAME_LINEAR, THEME_COLOR_BLUE
)
from .theme_utils import create_palette_from_theme, get_theme_stylesheet


class ThemeManager(QObject):
    """主题管理器，负责主题变更信号和应用"""
    
    theme_changed = pyqtSignal(str, str, str)
    
    def __init__(self):
        super().__init__()
        self.current_theme_mode = THEME_MODE_AUTO
        self.current_theme_name = THEME_NAME_CLASSIC
        self.current_theme_color = THEME_COLOR_BLUE
    
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
            
            self.theme_changed.emit(theme_mode, theme_name, theme_color)
            self.apply_theme_to_application()
    
    def apply_theme_to_application(self) -> None:
        """将当前主题应用到整个应用程序"""
        app = QApplication.instance()
        if not app:
            return

        palette = create_palette_from_theme(
            self.current_theme_mode,
            self.current_theme_color,
            self.current_theme_name
        )

        app.setPalette(palette)

        # Linear 主题使用 QSS 样式表
        qss = get_theme_stylesheet(
            self.current_theme_mode,
            self.current_theme_color,
            self.current_theme_name
        )
        app.setStyleSheet(qss)

        for window in app.topLevelWidgets():
            if hasattr(window, 'setPalette'):
                window.setPalette(palette)
                if hasattr(window, 'update'):
                    window.update()
    
    def register_widget(self, widget) -> None:
        """注册窗口部件（占位符，当前实现不需要额外逻辑）"""
        pass
    
    def unregister_widget(self, widget) -> None:
        """取消注册窗口部件（占位符，当前实现不需要额外逻辑）"""
        pass


theme_manager = ThemeManager()
