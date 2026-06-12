"""Linear 主题样式加载器

重构后使用 ThemeConfig 作为颜色定义的单一真相源。
"""
import os
from typing import Dict, Tuple

from app.core.theme_constants import (
    THEME_MODE_DARK, THEME_MODE_LIGHT,
    THEME_COLOR_BLUE, THEME_COLOR_GREEN, THEME_COLOR_RED,
    THEME_COLOR_PURPLE, THEME_COLOR_ORANGE
)
from app.core.theme_config import _ACCENT_RGB, _hex, _lighten, _darken

# QSS 文件路径
_QSS_DIR = os.path.dirname(os.path.abspath(__file__))
_LINEAR_QSS_PATH = os.path.join(_QSS_DIR, "linear_theme.qss")


def _get_color_variables(theme_mode: str, theme_color: str) -> Dict[str, str]:
    """获取 Linear 设计系统的颜色变量

    基于 Linear 官方设计系统：
    - 深色画布 #08090a，面板 #0f1011，浮层 #191a1b
    - 半透明白色边框 rgba(255,255,255,0.05-0.08)
    - 品牌靛蓝 #5e6ad2 / #7170ff
    """
    accent_rgb = _ACCENT_RGB.get(theme_color, _ACCENT_RGB[THEME_COLOR_BLUE])
    accent = _hex(*accent_rgb)
    # hover 状态使用更亮的变体
    accent_hover = _hex(*_lighten(*accent_rgb, 0.15))
    success_rgb = (39, 166, 68)   # #27a644
    danger_rgb = (239, 68, 68)    # #ef4444

    if theme_mode == THEME_MODE_DARK:
        return {
            # 背景色 — Linear 深色层级
            "@bg_primary": "#08090a",        # Marketing Black
            "@bg_secondary": "#0f1011",      # Panel Dark
            "@bg_elevated": "#191a1b",       # Level 3 Surface
            "@bg_hover": "#28282c",          # Secondary Surface
            "@bg_pressed": "#34343a",        # 交互反馈
            "@bg_disabled": "#141516",       # Line Tint
            "@bg_selection": "#1a1b3a",      # 靛蓝半透明近似
            "@bg_alternate": "#0f1011",      # Panel Dark
            "@bg_tooltip": "#191a1b",        # Level 3
            "@bg_info": "#191a1b",           # Level 3
            # 文字色 — Linear 灰度层级
            "@text_primary": "#f7f8f8",      # Primary Text
            "@text_secondary": "#d0d6e0",    # Secondary Text
            "@text_disabled": "#62666d",     # Quaternary Text
            "@text_tooltip": "#f7f8f8",      # Primary Text
            # 边框色 — 实色近似
            "@border_default": "#1a1c22",    # 近似 rgba(255,255,255,0.08)
            "@border_hover": "#24262c",      # 近似 rgba(255,255,255,0.12)
            "@border_disabled": "#121315",   # 近似 rgba(255,255,255,0.04)
            "@border_light": "#141619",      # 近似 rgba(255,255,255,0.05)
            # 半透明值 — 深色模式用白色叠加
            "@rgba_border_subtle": "rgba(255,255,255,0.05)",
            "@rgba_border_standard": "rgba(255,255,255,0.08)",
            "@rgba_border_strong": "rgba(255,255,255,0.12)",
            "@rgba_border_disabled": "rgba(255,255,255,0.04)",
            "@rgba_surface": "rgba(255,255,255,0.02)",
            "@rgba_surface_hover": "rgba(255,255,255,0.06)",
            "@rgba_surface_strong": "rgba(255,255,255,0.08)",
            "@rgba_surface_disabled": "rgba(255,255,255,0.02)",
            "@rgba_surface_pressed": "rgba(255,255,255,0.01)",
            "@rgba_selection": "rgba(94,106,210,0.20)",
            "@rgba_info_bg": "rgba(94,106,210,0.08)",
            # 强调色
            "@accent": accent,
            "@accent_hover": accent_hover,
            # 状态色
            "@success": _hex(*success_rgb),
            "@danger": _hex(*danger_rgb),
            "@danger_hover": _hex(*_lighten(*danger_rgb, 0.15)),
        }
    else:
        return {
            # 背景色 — Linear 浅色层级
            "@bg_primary": "#f7f8f8",        # Light Background
            "@bg_secondary": "#f3f4f5",      # Light Surface
            "@bg_elevated": "#ffffff",       # Pure White
            "@bg_hover": "#f5f6f7",          # Light Surface alt
            "@bg_pressed": "#e6e6e6",        # Light Border Alt
            "@bg_disabled": "#f3f4f5",       # Light Surface
            "@bg_selection": "#e8e9f8",      # 靛蓝浅色近似
            "@bg_alternate": "#f3f4f5",      # Light Surface
            "@bg_tooltip": "#0f1011",        # Panel Dark
            "@bg_info": "#f3f4f5",           # Light Surface
            # 文字色
            "@text_primary": "#1a1b1e",      # 近黑文字
            "@text_secondary": "#62666d",    # Quaternary Text
            "@text_disabled": "#8a8f98",     # Tertiary Text
            "@text_tooltip": "#f7f8f8",      # Primary Text
            # 边框色 — 实色
            "@border_default": "#d0d6e0",    # Light Border
            "@border_hover": "#b0b8c4",      # 悬停增强
            "@border_disabled": "#e6e6e6",   # Light Border Alt
            "@border_light": "#e6e6e6",      # Light Border Alt
            # 半透明值 — 浅色模式用黑色/灰色叠加
            "@rgba_border_subtle": "rgba(0,0,0,0.06)",
            "@rgba_border_standard": "rgba(0,0,0,0.10)",
            "@rgba_border_strong": "rgba(0,0,0,0.15)",
            "@rgba_border_disabled": "rgba(0,0,0,0.05)",
            "@rgba_surface": "rgba(0,0,0,0.02)",
            "@rgba_surface_hover": "rgba(0,0,0,0.04)",
            "@rgba_surface_strong": "rgba(0,0,0,0.06)",
            "@rgba_surface_disabled": "rgba(0,0,0,0.03)",
            "@rgba_surface_pressed": "rgba(0,0,0,0.08)",
            "@rgba_selection": "rgba(94,106,210,0.12)",
            "@rgba_info_bg": "rgba(94,106,210,0.06)",
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

    # 替换颜色变量 - 按变量名长度降序排序，避免短变量名替换长变量名的一部分
    # 例如 @accent 在 @accent_hover 之前被替换会导致 #22c55e_hover
    variables = _get_color_variables(theme_mode, theme_color)
    for var_name, color_value in sorted(variables.items(), key=lambda x: len(x[0]), reverse=True):
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
        "highlighted_text": "#f7f8f8",
    }
