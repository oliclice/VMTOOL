"""模块化主题配置 - 所有主题定义的单一真相源

整合所有颜色定义，消除重复，提供统一的 API 供 GUI 组件使用。
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from PyQt6.QtGui import QPalette, QColor

from .theme_constants import (
    THEME_MODE_AUTO, THEME_MODE_LIGHT, THEME_MODE_DARK,
    THEME_NAME_CLASSIC, THEME_NAME_MATERIAL3, THEME_NAME_LINEAR,
    THEME_COLOR_BLUE, THEME_COLOR_GREEN, THEME_COLOR_RED,
    THEME_COLOR_PURPLE, THEME_COLOR_ORANGE
)


@dataclass
class ColorPalette:
    """主题调色板 - 定义所有颜色 token"""
    # 背景色层级
    bg_primary: str
    bg_secondary: str
    bg_elevated: str
    bg_hover: str
    bg_pressed: str
    bg_disabled: str
    bg_selection: str
    bg_alternate: str
    bg_tooltip: str
    bg_info: str

    # 文字色层级
    text_primary: str
    text_secondary: str
    text_disabled: str
    text_tooltip: str

    # 边框色
    border_default: str
    border_hover: str
    border_disabled: str
    border_light: str

    # 半透明值
    rgba_border_subtle: str
    rgba_border_standard: str
    rgba_border_strong: str
    rgba_border_disabled: str
    rgba_surface: str
    rgba_surface_hover: str
    rgba_surface_strong: str
    rgba_surface_disabled: str
    rgba_surface_pressed: str
    rgba_selection: str
    rgba_info_bg: str

    # 强调色
    accent: str
    accent_hover: str

    # 状态色
    success: str
    danger: str
    danger_hover: str


@dataclass
class ThemeDefinition:
    """完整主题定义"""
    name: str
    light: ColorPalette
    dark: ColorPalette


# ==================== 强调色 RGB 映射 ====================
_ACCENT_RGB: Dict[str, Tuple[int, int, int]] = {
    THEME_COLOR_BLUE: (94, 106, 210),      # #5e6ad2 Linear Brand Indigo
    THEME_COLOR_GREEN: (39, 166, 68),      # #27a644
    THEME_COLOR_RED: (239, 68, 68),        # #ef4444
    THEME_COLOR_PURPLE: (113, 112, 255),   # #7170ff
    THEME_COLOR_ORANGE: (249, 115, 22),    # #f97316
}

# 经典/Material3 主题的强调色
_CLASSIC_ACCENT_RGB: Dict[str, Tuple[int, int, int]] = {
    THEME_COLOR_BLUE: (50, 150, 250),
    THEME_COLOR_GREEN: (50, 150, 100),
    THEME_COLOR_RED: (200, 50, 50),
    THEME_COLOR_PURPLE: (150, 50, 200),
    THEME_COLOR_ORANGE: (200, 100, 50),
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


def _create_linear_palette(theme_color: str, is_dark: bool) -> ColorPalette:
    """创建 Linear 主题调色板"""
    accent_rgb = _ACCENT_RGB.get(theme_color, _ACCENT_RGB[THEME_COLOR_BLUE])
    accent = _hex(*accent_rgb)
    accent_hover = _hex(*_lighten(*accent_rgb, 0.15))
    success_rgb = (39, 166, 68)
    danger_rgb = (239, 68, 68)

    if is_dark:
        return ColorPalette(
            bg_primary="#08090a",
            bg_secondary="#0f1011",
            bg_elevated="#191a1b",
            bg_hover="#28282c",
            bg_pressed="#34343a",
            bg_disabled="#141516",
            bg_selection="#1a1b3a",
            bg_alternate="#0f1011",
            bg_tooltip="#191a1b",
            bg_info="#191a1b",
            text_primary="#f7f8f8",
            text_secondary="#d0d6e0",
            text_disabled="#62666d",
            text_tooltip="#f7f8f8",
            border_default="#1a1c22",
            border_hover="#24262c",
            border_disabled="#121315",
            border_light="#141619",
            rgba_border_subtle="rgba(255,255,255,0.05)",
            rgba_border_standard="rgba(255,255,255,0.08)",
            rgba_border_strong="rgba(255,255,255,0.12)",
            rgba_border_disabled="rgba(255,255,255,0.04)",
            rgba_surface="rgba(255,255,255,0.02)",
            rgba_surface_hover="rgba(255,255,255,0.06)",
            rgba_surface_strong="rgba(255,255,255,0.08)",
            rgba_surface_disabled="rgba(255,255,255,0.02)",
            rgba_surface_pressed="rgba(255,255,255,0.01)",
            rgba_selection="rgba(94,106,210,0.20)",
            rgba_info_bg="rgba(94,106,210,0.08)",
            accent=accent,
            accent_hover=accent_hover,
            success=_hex(*success_rgb),
            danger=_hex(*danger_rgb),
            danger_hover=_hex(*_lighten(*danger_rgb, 0.15)),
        )
    else:
        return ColorPalette(
            bg_primary="#f7f8f8",
            bg_secondary="#f3f4f5",
            bg_elevated="#ffffff",
            bg_hover="#f5f6f7",
            bg_pressed="#e6e6e6",
            bg_disabled="#f3f4f5",
            bg_selection="#e8e9f8",
            bg_alternate="#f3f4f5",
            bg_tooltip="#0f1011",
            bg_info="#f3f4f5",
            text_primary="#1a1b1e",
            text_secondary="#62666d",
            text_disabled="#8a8f98",
            text_tooltip="#f7f8f8",
            border_default="#d0d6e0",
            border_hover="#b0b8c4",
            border_disabled="#e6e6e6",
            border_light="#e6e6e6",
            rgba_border_subtle="rgba(0,0,0,0.06)",
            rgba_border_standard="rgba(0,0,0,0.10)",
            rgba_border_strong="rgba(0,0,0,0.15)",
            rgba_border_disabled="rgba(0,0,0,0.05)",
            rgba_surface="rgba(0,0,0,0.02)",
            rgba_surface_hover="rgba(0,0,0,0.04)",
            rgba_surface_strong="rgba(0,0,0,0.06)",
            rgba_surface_disabled="rgba(0,0,0,0.03)",
            rgba_surface_pressed="rgba(0,0,0,0.08)",
            rgba_selection="rgba(94,106,210,0.12)",
            rgba_info_bg="rgba(94,106,210,0.06)",
            accent=accent,
            accent_hover=accent_hover,
            success=_hex(*_darken(*success_rgb, 0.1)),
            danger=_hex(*_darken(*danger_rgb, 0.1)),
            danger_hover=_hex(*_darken(*danger_rgb, 0.2)),
        )


def _create_classic_palette(theme_color: str, is_dark: bool) -> ColorPalette:
    """创建经典/Material3 主题调色板"""
    accent_rgb = _CLASSIC_ACCENT_RGB.get(theme_color, _CLASSIC_ACCENT_RGB[THEME_COLOR_BLUE])
    accent = _hex(*accent_rgb)
    accent_hover = _hex(*_lighten(*accent_rgb, 0.15))

    if is_dark:
        return ColorPalette(
            bg_primary="#1e1e1e",
            bg_secondary="#2d2d2d",
            bg_elevated="#333333",
            bg_hover="#3d3d3d",
            bg_pressed="#4a4a4a",
            bg_disabled="#252525",
            bg_selection="#1a237e",
            bg_alternate="#2d2d2d",
            bg_tooltip="#424242",
            bg_info="#2d2d2d",
            text_primary="#f0f0f0",
            text_secondary="#b0b0b0",
            text_disabled="#666666",
            text_tooltip="#f0f0f0",
            border_default="#404040",
            border_hover="#505050",
            border_disabled="#333333",
            border_light="#3a3a3a",
            rgba_border_subtle="rgba(255,255,255,0.08)",
            rgba_border_standard="rgba(255,255,255,0.12)",
            rgba_border_strong="rgba(255,255,255,0.16)",
            rgba_border_disabled="rgba(255,255,255,0.06)",
            rgba_surface="rgba(255,255,255,0.04)",
            rgba_surface_hover="rgba(255,255,255,0.08)",
            rgba_surface_strong="rgba(255,255,255,0.12)",
            rgba_surface_disabled="rgba(255,255,255,0.04)",
            rgba_surface_pressed="rgba(255,255,255,0.02)",
            rgba_selection="rgba(25,118,210,0.30)",
            rgba_info_bg="rgba(25,118,210,0.12)",
            accent=accent,
            accent_hover=accent_hover,
            success="#66BB6A",
            danger="#EF5350",
            danger_hover="#E53935",
        )
    else:
        return ColorPalette(
            bg_primary="#f5f5f5",
            bg_secondary="#ffffff",
            bg_elevated="#ffffff",
            bg_hover="#eeeeee",
            bg_pressed="#e0e0e0",
            bg_disabled="#fafafa",
            bg_selection="#e3f2fd",
            bg_alternate="#f5f5f5",
            bg_tooltip="#616161",
            bg_info="#e3f2fd",
            text_primary="#212121",
            text_secondary="#757575",
            text_disabled="#9e9e9e",
            text_tooltip="#ffffff",
            border_default="#e0e0e0",
            border_hover="#bdbdbd",
            border_disabled="#eeeeee",
            border_light="#eeeeee",
            rgba_border_subtle="rgba(0,0,0,0.08)",
            rgba_border_standard="rgba(0,0,0,0.12)",
            rgba_border_strong="rgba(0,0,0,0.16)",
            rgba_border_disabled="rgba(0,0,0,0.06)",
            rgba_surface="rgba(0,0,0,0.02)",
            rgba_surface_hover="rgba(0,0,0,0.04)",
            rgba_surface_strong="rgba(0,0,0,0.08)",
            rgba_surface_disabled="rgba(0,0,0,0.03)",
            rgba_surface_pressed="rgba(0,0,0,0.10)",
            rgba_selection="rgba(25,118,210,0.20)",
            rgba_info_bg="rgba(25,118,210,0.08)",
            accent=accent,
            accent_hover=accent_hover,
            success="#4CAF50",
            danger="#F44336",
            danger_hover="#E53935",
        )


# ==================== 主题定义注册表 ====================
_THEMES: Dict[str, ThemeDefinition] = {
    THEME_NAME_LINEAR: ThemeDefinition(
        name=THEME_NAME_LINEAR,
        light=_create_linear_palette(THEME_COLOR_BLUE, False),
        dark=_create_linear_palette(THEME_COLOR_BLUE, True),
    ),
    THEME_NAME_CLASSIC: ThemeDefinition(
        name=THEME_NAME_CLASSIC,
        light=_create_classic_palette(THEME_COLOR_BLUE, False),
        dark=_create_classic_palette(THEME_COLOR_BLUE, True),
    ),
    THEME_NAME_MATERIAL3: ThemeDefinition(
        name=THEME_NAME_MATERIAL3,
        light=_create_classic_palette(THEME_COLOR_BLUE, False),
        dark=_create_classic_palette(THEME_COLOR_BLUE, True),
    ),
}


class ThemeConfig:
    """所有主题定义的单一真相源"""

    @classmethod
    def get_theme(cls, theme_name: str) -> ThemeDefinition:
        """获取主题定义"""
        return _THEMES.get(theme_name, _THEMES[THEME_NAME_CLASSIC])

    @classmethod
    def get_palette(cls, theme_name: str, theme_mode: str, theme_color: str) -> ColorPalette:
        """获取指定配置的调色板

        Args:
            theme_name: 主题名称 (经典/Material3/Linear)
            theme_mode: 主题模式 (light/dark/auto)
            theme_color: 主题颜色 (蓝色/绿色/红色/紫色/橙色)
        """
        theme = cls.get_theme(theme_name)

        # 根据主题名称选择基础调色板
        if theme_name == THEME_NAME_LINEAR:
            base_palette = _create_linear_palette(theme_color, theme_mode == THEME_MODE_DARK)
        else:
            base_palette = _create_classic_palette(theme_color, theme_mode == THEME_MODE_DARK)

        return base_palette

    @classmethod
    def get_qpalette(cls, theme_name: str, theme_mode: str, theme_color: str) -> QPalette:
        """获取 Qt 调色板

        Args:
            theme_name: 主题名称
            theme_mode: 主题模式
            theme_color: 主题颜色
        """
        palette_colors = cls.get_palette(theme_name, theme_mode, theme_color)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(palette_colors.bg_primary))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(palette_colors.text_primary))
        palette.setColor(QPalette.ColorRole.Base, QColor(palette_colors.bg_elevated))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(palette_colors.bg_alternate))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(palette_colors.bg_tooltip))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(palette_colors.text_tooltip))
        palette.setColor(QPalette.ColorRole.Text, QColor(palette_colors.text_primary))
        palette.setColor(QPalette.ColorRole.Button, QColor(palette_colors.bg_elevated))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(palette_colors.text_primary))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(palette_colors.danger))
        palette.setColor(QPalette.ColorRole.Link, QColor(palette_colors.accent))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(palette_colors.accent))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(palette_colors.text_tooltip))

        return palette

    @classmethod
    def get_status_color(cls, status: str, theme_name: str, theme_mode: str, theme_color: str) -> str:
        """获取状态颜色

        Args:
            status: 状态类型 (info, success, error, warning)
            theme_name: 主题名称
            theme_mode: 主题模式
            theme_color: 主题颜色
        """
        palette = cls.get_palette(theme_name, theme_mode, theme_color)

        status_map = {
            "info": palette.accent,
            "success": palette.success,
            "error": palette.danger,
            "warning": palette.accent_hover,
        }
        return status_map.get(status, palette.accent)

    @classmethod
    def get_accent_color(cls, theme_color: str, theme_name: str = THEME_NAME_LINEAR) -> str:
        """获取强调色

        Args:
            theme_color: 主题颜色
            theme_name: 主题名称
        """
        if theme_name == THEME_NAME_LINEAR:
            rgb = _ACCENT_RGB.get(theme_color, _ACCENT_RGB[THEME_COLOR_BLUE])
        else:
            rgb = _CLASSIC_ACCENT_RGB.get(theme_color, _CLASSIC_ACCENT_RGB[THEME_COLOR_BLUE])
        return _hex(*rgb)

    @classmethod
    def get_hint_color(cls, theme_name: str, theme_mode: str) -> str:
        """获取提示文字颜色"""
        palette = cls.get_palette(theme_name, theme_mode, THEME_COLOR_BLUE)
        return palette.text_secondary

    @classmethod
    def get_info_box_style(cls, theme_name: str, theme_mode: str, theme_color: str) -> str:
        """获取信息框样式"""
        palette = cls.get_palette(theme_name, theme_mode, theme_color)
        return (f"QLabel {{ color: {palette.accent}; padding: 8px; "
                f"background-color: {palette.rgba_info_bg}; border-radius: 6px; }}")

    @classmethod
    def get_button_style(cls, button_type: str, theme_name: str, theme_mode: str, theme_color: str) -> str:
        """获取按钮样式

        Args:
            button_type: 按钮类型 (primary, success, default)
            theme_name: 主题名称
            theme_mode: 主题模式
            theme_color: 主题颜色
        """
        palette = cls.get_palette(theme_name, theme_mode, theme_color)

        if button_type == "primary":
            return (f"QPushButton {{ background-color: {palette.accent}; color: {palette.text_tooltip}; "
                    f"font-weight: 600; padding: 10px; border-radius: 6px; "
                    f"border: 1px solid {palette.accent}; }} "
                    f"QPushButton:hover {{ background-color: {palette.accent_hover}; "
                    f"border-color: {palette.accent_hover}; }}")
        elif button_type == "success":
            return (f"QPushButton {{ background-color: {palette.success}; color: {palette.text_tooltip}; "
                    f"font-weight: 600; padding: 10px; border-radius: 6px; "
                    f"border: 1px solid {palette.success}; }} "
                    f"QPushButton:hover {{ background-color: {palette.accent_hover}; "
                    f"border-color: {palette.accent_hover}; }}")
        return ""
