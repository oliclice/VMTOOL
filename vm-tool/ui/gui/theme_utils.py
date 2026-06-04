"""主题相关工具函数"""
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog
from typing import Set

from app.core.theme_constants import (
    THEME_MODE_DARK, THEME_MODE_LIGHT, THEME_MODE_AUTO,
    THEME_COLOR_BLUE, THEME_COLOR_GREEN, THEME_COLOR_RED,
    THEME_COLOR_PURPLE, THEME_COLOR_ORANGE, COLOR_RGB_MAP,
    THEME_NAME_LINEAR
)
from .styles import load_linear_theme_qss

# Linear 设计系统专属强调色 RGB 映射
_LINEAR_COLOR_RGB = {
    THEME_COLOR_BLUE: (94, 106, 210),     # #5e6ad2 Brand Indigo
    THEME_COLOR_GREEN: (39, 166, 68),     # #27a644
    THEME_COLOR_RED: (239, 68, 68),       # #ef4444
    THEME_COLOR_PURPLE: (113, 112, 255),  # #7170ff
    THEME_COLOR_ORANGE: (249, 115, 22),   # #f97316
}


def create_palette_from_theme(theme_mode: str, theme_color: str, theme_name: str = None) -> QPalette:
    """根据主题模式、颜色和名称创建调色板"""
    # 根据主题模式设置基础颜色
    if theme_name == THEME_NAME_LINEAR:
        # Linear 设计系统：近黑画布 + 品牌靛蓝
        if theme_mode == THEME_MODE_DARK:
            background_color = QColor(8, 9, 10)         # #08090a Marketing Black
            text_color = QColor(247, 248, 248)          # #f7f8f8 Primary Text
            widget_color = QColor(15, 16, 17)           # #0f1011 Panel Dark
            accent_color = QColor(94, 106, 210)         # #5e6ad2 Brand Indigo
        else:
            background_color = QColor(247, 248, 248)    # #f7f8f8 Light Background
            text_color = QColor(26, 27, 30)             # #1a1b1e Near Black
            widget_color = QColor(255, 255, 255)        # #ffffff Pure White
            accent_color = QColor(94, 106, 210)         # #5e6ad2 Brand Indigo
    elif theme_mode == THEME_MODE_DARK:
        # 经典/Material3 深色模式
        background_color = QColor(30, 30, 30)
        text_color = QColor(240, 240, 240)
        widget_color = QColor(40, 40, 40)
        accent_color = QColor(*COLOR_RGB_MAP.get(THEME_COLOR_BLUE, (50, 150, 250)))
    else:
        # 经典/Material3 浅色模式（包括auto和light）
        background_color = QColor(240, 240, 240)
        text_color = QColor(30, 30, 30)
        widget_color = QColor(250, 250, 250)
        accent_color = QColor(*COLOR_RGB_MAP.get(THEME_COLOR_BLUE, (50, 150, 250)))

    # 根据主题颜色调整强调色
    color_map = _LINEAR_COLOR_RGB if theme_name == THEME_NAME_LINEAR else COLOR_RGB_MAP
    if theme_color == THEME_COLOR_GREEN:
        accent_color = QColor(*color_map.get(THEME_COLOR_GREEN, (50, 150, 100)))
    elif theme_color == THEME_COLOR_RED:
        accent_color = QColor(*color_map.get(THEME_COLOR_RED, (200, 50, 50)))
    elif theme_color == THEME_COLOR_PURPLE:
        accent_color = QColor(*color_map.get(THEME_COLOR_PURPLE, (150, 50, 200)))
    elif theme_color == THEME_COLOR_ORANGE:
        accent_color = QColor(*color_map.get(THEME_COLOR_ORANGE, (200, 100, 50)))

    # 创建并配置调色板
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, background_color)
    palette.setColor(QPalette.ColorRole.WindowText, text_color)
    palette.setColor(QPalette.ColorRole.Base, widget_color)
    palette.setColor(QPalette.ColorRole.AlternateBase, background_color)
    palette.setColor(QPalette.ColorRole.ToolTipBase, text_color)
    palette.setColor(QPalette.ColorRole.ToolTipText, background_color)
    palette.setColor(QPalette.ColorRole.Text, text_color)
    palette.setColor(QPalette.ColorRole.Button, widget_color)
    palette.setColor(QPalette.ColorRole.ButtonText, text_color)
    palette.setColor(QPalette.ColorRole.BrightText, QColor(239, 68, 68))
    palette.setColor(QPalette.ColorRole.Link, accent_color)
    palette.setColor(QPalette.ColorRole.Highlight, accent_color)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(247, 248, 248))

    return palette


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
        if any(color_def in stylesheet for color_def in ['#4CAF50', '#FF0000', '#0000FF', '#1976D2', '#FF5722']):
            if not hasattr(widget, '_original_styleSheet'):
                widget._original_styleSheet = stylesheet
            widget.setStyleSheet("")

    for child in widget.children():
        clear_hardcoded_stylesheets(child, processed_widgets)

    return processed_widgets


def get_accent_color(theme_color: str) -> QColor:
    """根据颜色名称返回QColor对象"""
    rgb = COLOR_RGB_MAP.get(theme_color, COLOR_RGB_MAP[THEME_COLOR_BLUE])
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