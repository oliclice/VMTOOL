"""主题感知的颜色辅助函数

重构后使用 ThemeConfig 作为单一真相源。
"""
from typing import Optional

from app.core.theme_constants import (
    THEME_MODE_DARK, THEME_MODE_LIGHT, THEME_MODE_AUTO,
    THEME_NAME_LINEAR, THEME_COLOR_BLUE
)
from app.core.theme_config import ThemeConfig


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
    from .theme_manager import theme_manager

    if theme_color is None:
        theme_color = theme_manager.current_theme_color

    return ThemeConfig.get_status_color(
        status,
        theme_manager.current_theme_name,
        theme_manager.current_theme_mode,
        theme_color
    )


def get_hint_color() -> str:
    """获取提示文字颜色"""
    from .theme_manager import theme_manager
    return ThemeConfig.get_hint_color(
        theme_manager.current_theme_name,
        theme_manager.current_theme_mode
    )


def get_info_box_style() -> str:
    """获取信息框样式"""
    from .theme_manager import theme_manager
    return ThemeConfig.get_info_box_style(
        theme_manager.current_theme_name,
        theme_manager.current_theme_mode,
        theme_manager.current_theme_color
    )


def get_button_style(button_type: str = "primary") -> str:
    """获取按钮样式

    Args:
        button_type: 按钮类型 (primary, success, default)
    """
    from .theme_manager import theme_manager
    return ThemeConfig.get_button_style(
        button_type,
        theme_manager.current_theme_name,
        theme_manager.current_theme_mode,
        theme_manager.current_theme_color
    )
