"""主题感知的颜色辅助函数"""
from typing import Optional

from app.core.theme_constants import (
    THEME_MODE_DARK, THEME_MODE_LIGHT, THEME_MODE_AUTO,
    THEME_NAME_LINEAR, THEME_COLOR_BLUE
)


def _is_linear_theme(theme_name: Optional[str] = None) -> bool:
    """检查是否为 Linear 主题"""
    if theme_name is None:
        from .theme_manager import theme_manager
        theme_name = theme_manager.current_theme_name
    return theme_name == THEME_NAME_LINEAR


def _is_dark_mode(theme_mode: Optional[str] = None) -> bool:
    """检查是否为深色模式"""
    if theme_mode is None:
        from .theme_manager import theme_manager
        theme_mode = theme_manager.current_theme_mode
    if theme_mode == THEME_MODE_AUTO:
        # 简单的自动检测，实际应该检测系统主题
        return False
    return theme_mode == THEME_MODE_DARK


def get_status_color(status: str, theme_color: Optional[str] = None) -> str:
    """获取状态颜色

    Args:
        status: 状态类型 (info, success, error, warning)
        theme_color: 主题颜色，None 则使用当前主题

    Returns:
        hex 颜色字符串
    """
    if theme_color is None:
        from .theme_manager import theme_manager
        theme_color = theme_manager.current_theme_color

    is_linear = _is_linear_theme()
    is_dark = _is_dark_mode()

    if is_linear:
        # Linear 主题使用更柔和的颜色
        colors = {
            "info": {
                "light": "#3b82f6",
                "dark": "#60a5fa",
            },
            "success": {
                "light": "#16a34a",
                "dark": "#4ade80",
            },
            "error": {
                "light": "#dc2626",
                "dark": "#f87171",
            },
            "warning": {
                "light": "#d97706",
                "dark": "#fbbf24",
            },
        }
    else:
        # 经典/Material3 主题
        colors = {
            "info": {
                "light": "#1976D2",
                "dark": "#2196F3",
            },
            "success": {
                "light": "#4CAF50",
                "dark": "#66BB6A",
            },
            "error": {
                "light": "#F44336",
                "dark": "#EF5350",
            },
            "warning": {
                "light": "#FF9800",
                "dark": "#FFA726",
            },
        }

    mode = "dark" if is_dark else "light"
    return colors.get(status, colors["info"])[mode]


def get_hint_color() -> str:
    """获取提示文字颜色"""
    if _is_linear_theme():
        if _is_dark_mode():
            return "#a1a1aa"
        return "#71717a"
    return "#666666"


def get_info_box_style() -> str:
    """获取信息框样式"""
    if _is_linear_theme():
        if _is_dark_mode():
            return "QLabel { color: #60a5fa; padding: 8px; background-color: #1e293b; border-radius: 4px; }"
        return "QLabel { color: #3b82f6; padding: 8px; background-color: #eff6ff; border-radius: 4px; }"
    return "QLabel { color: #1976D2; padding: 8px; background-color: #E3F2FD; border-radius: 4px; }"


def get_button_style(button_type: str = "primary") -> str:
    """获取按钮样式

    Args:
        button_type: 按钮类型 (primary, success, default)
    """
    if _is_linear_theme():
        if button_type == "primary":
            if _is_dark_mode():
                return ("QPushButton { background-color: #3b82f6; color: white; font-weight: 600; "
                        "padding: 10px; border-radius: 4px; border: none; } "
                        "QPushButton:hover { background-color: #2563eb; }")
            return ("QPushButton { background-color: #3b82f6; color: white; font-weight: 600; "
                    "padding: 10px; border-radius: 4px; border: none; } "
                    "QPushButton:hover { background-color: #2563eb; }")
        elif button_type == "success":
            if _is_dark_mode():
                return ("QPushButton { background-color: #22c55e; color: white; font-weight: 600; "
                        "padding: 10px; border-radius: 4px; border: none; } "
                        "QPushButton:hover { background-color: #16a34a; }")
            return ("QPushButton { background-color: #22c55e; color: white; font-weight: 600; "
                    "padding: 10px; border-radius: 4px; border: none; } "
                    "QPushButton:hover { background-color: #16a34a; }")
    else:
        if button_type == "primary":
            return ("QPushButton { background-color: #2196F3; color: white; font-weight: bold; "
                    "padding: 10px; border-radius: 5px; } "
                    "QPushButton:hover { background-color: #0b7dda; }")
        elif button_type == "success":
            return ("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; "
                    "padding: 10px; border-radius: 5px; } "
                    "QPushButton:hover { background-color: #45a049; }")
    return ""
