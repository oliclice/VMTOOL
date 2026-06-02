"""Linear 主题样式加载器"""
import os
from typing import Dict, Tuple

from app.core.theme_constants import (
    THEME_MODE_DARK, THEME_MODE_LIGHT,
    THEME_COLOR_BLUE, THEME_COLOR_GREEN, THEME_COLOR_RED,
    THEME_COLOR_PURPLE, THEME_COLOR_ORANGE
)

# QSS 文件路径
_QSS_DIR = os.path.dirname(os.path.abspath(__file__))
_LINEAR_QSS_PATH = os.path.join(_QSS_DIR, "linear_theme.qss")

# 强调色 RGB 映射
_ACCENT_RGB: Dict[str, Tuple[int, int, int]] = {
    THEME_COLOR_BLUE: (59, 130, 246),
    THEME_COLOR_GREEN: (34, 197, 94),
    THEME_COLOR_RED: (239, 68, 68),
    THEME_COLOR_PURPLE: (168, 85, 247),
    THEME_COLOR_ORANGE: (249, 115, 22),
}


def _hex(r: int, g: int, b: int) -> str:
    """RGB 转 hex 颜色字符串"""
    return f"#{r:02x}{g:02x}{b:02x}"


def _lighten(r: int, g: int, b: int, factor: float = 0.15) -> Tuple[int, int, int]:
    """颜色变亮"""
    return (
        min(255, int(r + (255 - r) * factor)),
        min(255, int(g + (255 - g) * factor)),
        min(255, int(b + (255 - b) * factor)),
    )


def _darken(r: int, g: int, b: int, factor: float = 0.15) -> Tuple[int, int, int]:
    """颜色变暗"""
    return (
        max(0, int(r * (1 - factor))),
        max(0, int(g * (1 - factor))),
        max(0, int(b * (1 - factor))),
    )


def _get_color_variables(theme_mode: str, theme_color: str) -> Dict[str, str]:
    """获取 Linear 主题的颜色变量"""
    accent_rgb = _ACCENT_RGB.get(theme_color, _ACCENT_RGB[THEME_COLOR_BLUE])
    accent = _hex(*accent_rgb)
    accent_hover = _hex(*_darken(*accent_rgb, 0.1))
    success_rgb = (34, 197, 94)
    danger_rgb = (239, 68, 68)

    if theme_mode == THEME_MODE_DARK:
        return {
            # 背景色
            "@bg_primary": "#18181b",
            "@bg_secondary": "#1e1e22",
            "@bg_elevated": "#202024",
            "@bg_hover": "#2a2a2e",
            "@bg_pressed": "#323236",
            "@bg_disabled": "#27272a",
            "@bg_selection": "#2e3a5c",
            "@bg_alternate": "#1c1c20",
            "@bg_tooltip": "#27272a",
            "@bg_info": "#1e293b",
            # 文字色
            "@text_primary": "#e4e4e7",
            "@text_secondary": "#a1a1aa",
            "@text_disabled": "#52525b",
            "@text_tooltip": "#e4e4e7",
            # 边框色
            "@border_default": "#3f3f46",
            "@border_hover": "#52525b",
            "@border_disabled": "#27272a",
            "@border_light": "#27272a",
            # 强调色
            "@accent": accent,
            "@accent_hover": accent_hover,
            # 状态色
            "@success": _hex(*success_rgb),
            "@danger": _hex(*danger_rgb),
            "@danger_hover": _hex(*_darken(*danger_rgb, 0.1)),
        }
    else:
        return {
            # 背景色
            "@bg_primary": "#ffffff",
            "@bg_secondary": "#f9fafb",
            "@bg_elevated": "#ffffff",
            "@bg_hover": "#f4f4f5",
            "@bg_pressed": "#e4e4e7",
            "@bg_disabled": "#f4f4f5",
            "@bg_selection": "#e0e7ff",
            "@bg_alternate": "#fafafa",
            "@bg_tooltip": "#18181b",
            "@bg_info": "#eff6ff",
            # 文字色
            "@text_primary": "#18181b",
            "@text_secondary": "#71717a",
            "@text_disabled": "#a1a1aa",
            "@text_tooltip": "#fafafa",
            # 边框色
            "@border_default": "#e4e4e7",
            "@border_hover": "#d4d4d8",
            "@border_disabled": "#f4f4f5",
            "@border_light": "#f4f4f5",
            # 强调色
            "@accent": accent,
            "@accent_hover": accent_hover,
            # 状态色
            "@success": _hex(*_darken(*success_rgb, 0.1)),
            "@danger": _hex(*_darken(*danger_rgb, 0.1)),
            "@danger_hover": _hex(*_darken(*danger_rgb, 0.2)),
        }


def load_linear_theme_qss(theme_mode: str, theme_color: str) -> str:
    """加载 Linear 主题 QSS 并替换颜色变量

    Args:
        theme_mode: 主题模式 (light/dark)
        theme_color: 主题颜色 (蓝色/绿色/红色/紫色/橙色)

    Returns:
        处理后的 QSS 字符串
    """
    try:
        with open(_LINEAR_QSS_PATH, "r", encoding="utf-8") as f:
            qss = f.read()
    except FileNotFoundError:
        return ""

    # 替换颜色变量
    variables = _get_color_variables(theme_mode, theme_color)
    for var_name, color_value in variables.items():
        qss = qss.replace(var_name, color_value)

    return qss


def get_linear_palette_colors(theme_mode: str, theme_color: str) -> Dict[str, str]:
    """获取 Linear 主题的调色板颜色（用于 QPalette 设置）

    Returns:
        颜色字典，键为角色名称
    """
    variables = _get_color_variables(theme_mode, theme_color)
    return {
        "window": variables["@bg_primary"],
        "window_text": variables["@text_primary"],
        "base": variables["@bg_elevated"],
        "alternate_base": variables["@bg_alternate"],
        "tooltip_base": variables["@bg_tooltip"],
        "tooltip_text": variables["@text_tooltip"],
        "text": variables["@text_primary"],
        "button": variables["@bg_elevated"],
        "button_text": variables["@text_primary"],
        "bright_text": "#ef4444",
        "link": variables["@accent"],
        "highlight": variables["@accent"],
        "highlighted_text": "#ffffff",
    }
