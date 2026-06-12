"""主题相关工具函数

重构后使用 ThemeConfig 作为单一真相源。
"""
from PyQt6.QtGui import QPalette, QColor
from typing import Set

from app.core.theme_constants import (
    THEME_MODE_DARK, THEME_MODE_LIGHT, THEME_MODE_AUTO,
    THEME_NAME_LINEAR
)
from app.core.theme_config import ThemeConfig
from .styles import load_linear_theme_qss


def create_palette_from_theme(theme_mode: str, theme_color: str, theme_name: str = None) -> QPalette:
    """根据主题模式、颜色和名称创建调色板

    Args:
        theme_mode: 主题模式 (light/dark/auto)
        theme_color: 主题颜色
        theme_name: 主题名称
    """
    if theme_name is None:
        from .theme_manager import theme_manager
        theme_name = theme_manager.current_theme_name

    return ThemeConfig.get_qpalette(theme_name, theme_mode, theme_color)


def apply_theme_to_widget(widget, palette: QPalette, processed_widgets: Set[int] = None) -> Set[int]:
    """递归应用调色板到控件及其子控件"""
    if processed_widgets is None:
        processed_widgets = set()

    if not widget or id(widget) in processed_widgets:
        return processed_widgets

    processed_widgets.add(id(widget))

    if hasattr(widget, 'setPalette'):
        widget.setPalette(palette)
        try:
            style = widget.style()
            if style:
                style.unpolish(widget)
                style.polish(widget)
        except Exception:
            pass

    if hasattr(widget, 'styleSheet') and widget.styleSheet():
        if not hasattr(widget, '_original_styleSheet'):
            widget._original_styleSheet = widget.styleSheet()
        widget.setStyleSheet("")

    for child in widget.children():
        apply_theme_to_widget(child, palette, processed_widgets)

    return processed_widgets


def clear_hardcoded_stylesheets(widget, processed_widgets: Set[int] = None) -> Set[int]:
    """清理硬编码的样式表，这些可能覆盖主题设置"""
    if processed_widgets is None:
        processed_widgets = set()

    if not widget or id(widget) in processed_widgets:
        return processed_widgets

    processed_widgets.add(id(widget))

    if hasattr(widget, 'styleSheet') and widget.styleSheet():
        stylesheet = widget.styleSheet()
        # 检测常见的硬编码颜色
        hardcoded_colors = [
            '#4CAF50', '#FF0000', '#0000FF', '#1976D2', '#FF5722',
            '#ff4444', '#ff8800', '#ccc', '#gray'
        ]
        if any(color_def.lower() in stylesheet.lower() for color_def in hardcoded_colors):
            if not hasattr(widget, '_original_styleSheet'):
                widget._original_styleSheet = stylesheet
            widget.setStyleSheet("")

    for child in widget.children():
        clear_hardcoded_stylesheets(child, processed_widgets)

    return processed_widgets


def get_accent_color(theme_color: str) -> QColor:
    """根据颜色名称返回QColor对象"""
    from app.core.theme_config import _ACCENT_RGB, _CLASSIC_ACCENT_RGB
    from .theme_manager import theme_manager

    if theme_manager.current_theme_name == THEME_NAME_LINEAR:
        rgb = _ACCENT_RGB.get(theme_color, _ACCENT_RGB.get("蓝色", (94, 106, 210)))
    else:
        rgb = _CLASSIC_ACCENT_RGB.get(theme_color, _CLASSIC_ACCENT_RGB.get("蓝色", (50, 150, 250)))
    return QColor(*rgb)


def get_theme_stylesheet(theme_mode: str, theme_color: str, theme_name: str = None) -> str:
    """获取主题的 QSS 样式表

    Args:
        theme_mode: 主题模式 (light/dark/auto)
        theme_color: 主题颜色
        theme_name: 主题名称

    Returns:
        QSS 字符串，非 Linear 主题返回空字符串
    """
    if theme_name == THEME_NAME_LINEAR:
        # 将 auto 映射为 light
        effective_mode = THEME_MODE_LIGHT if theme_mode == THEME_MODE_AUTO else theme_mode
        return load_linear_theme_qss(effective_mode, theme_color)
    return ""
