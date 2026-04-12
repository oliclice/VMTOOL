"""主题相关工具函数"""
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog
from typing import Set

from app.core.theme_constants import (
    THEME_MODE_DARK, THEME_MODE_LIGHT, THEME_MODE_AUTO,
    THEME_COLOR_BLUE, THEME_COLOR_GREEN, THEME_COLOR_RED,
    THEME_COLOR_PURPLE, THEME_COLOR_ORANGE, COLOR_RGB_MAP
)


def create_palette_from_theme(theme_mode: str, theme_color: str) -> QPalette:
    """根据主题模式和颜色创建调色板"""
    # 根据主题模式设置基础颜色
    if theme_mode == THEME_MODE_DARK:
        # 深色模式
        background_color = QColor(30, 30, 30)
        text_color = QColor(240, 240, 240)
        widget_color = QColor(40, 40, 40)
        accent_color = QColor(*COLOR_RGB_MAP.get(THEME_COLOR_BLUE, (50, 150, 250)))
    else:
        # 浅色模式（包括auto和light）
        background_color = QColor(240, 240, 240)
        text_color = QColor(30, 30, 30)
        widget_color = QColor(250, 250, 250)
        accent_color = QColor(*COLOR_RGB_MAP.get(THEME_COLOR_BLUE, (50, 150, 250)))

    # 根据主题颜色调整强调色
    if theme_color == THEME_COLOR_GREEN:
        accent_color = QColor(*COLOR_RGB_MAP.get(THEME_COLOR_GREEN, (50, 150, 100)))
    elif theme_color == THEME_COLOR_RED:
        accent_color = QColor(*COLOR_RGB_MAP.get(THEME_COLOR_RED, (200, 50, 50)))
    elif theme_color == THEME_COLOR_PURPLE:
        accent_color = QColor(*COLOR_RGB_MAP.get(THEME_COLOR_PURPLE, (150, 50, 200)))
    elif theme_color == THEME_COLOR_ORANGE:
        accent_color = QColor(*COLOR_RGB_MAP.get(THEME_COLOR_ORANGE, (200, 100, 50)))

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
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, accent_color)
    palette.setColor(QPalette.ColorRole.Highlight, accent_color)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

    return palette


def apply_theme_to_widget(widget, palette: QPalette, processed_widgets: Set[int] = None) -> Set[int]:
    """递归应用调色板到控件及其子控件"""
    if processed_widgets is None:
        processed_widgets = set()

    if not widget or id(widget) in processed_widgets:
        return processed_widgets

    processed_widgets.add(id(widget))

    # 应用调色板到支持它的控件
    if hasattr(widget, 'setPalette'):
        widget.setPalette(palette)
        # 只在顶级窗口或特定类型控件上刷新样式，避免性能开销
        if widget.isWindow() or isinstance(widget, (QMainWindow, QDialog)):
            try:
                style = widget.style()
                if style:
                    style.unpolish(widget)
                    style.polish(widget)
            except Exception:
                pass  # 样式刷新失败不影响主题应用

    # 递归处理所有子控件
    for child in widget.children():
        apply_theme_to_widget(child, palette, processed_widgets)

    return processed_widgets


def get_accent_color(theme_color: str) -> QColor:
    """根据颜色名称返回QColor对象"""
    rgb = COLOR_RGB_MAP.get(theme_color, COLOR_RGB_MAP[THEME_COLOR_BLUE])
    return QColor(*rgb)