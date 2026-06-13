"""主题同步更新模块

管理组件注册和主题同步，确保主题变更时所有注册的组件自动更新。
"""
import logging
import weakref
from typing import Callable, Dict, Optional, Any

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class ThemeSync(QObject):
    """管理组件注册和主题同步"""

    theme_changed = pyqtSignal(str, str, str)  # mode, name, color

    def __init__(self, parent=None):
        super().__init__(parent)
        self._registered_widgets: Dict[int, Dict[str, Any]] = {}
        self._update_count = 0

    def set_theme_manager(self, manager) -> None:
        """连接到主题管理器

        Args:
            manager: ThemeManager 实例
        """
        manager.theme_changed.connect(self._on_theme_changed)

    def register_widget(self, widget, callback: Optional[Callable] = None) -> None:
        """注册组件以自动更新主题

        Args:
            widget: 要注册的 QWidget
            callback: 可选的回调函数，签名 callback(mode, name, color)
                     如果不提供，则调用 widget.on_theme_changed() 或 widget.refresh_theme()
        """
        widget_id = id(widget)

        # 避免重复注册
        if widget_id in self._registered_widgets:
            return

        self._registered_widgets[widget_id] = {
            'ref': weakref.ref(widget),
            'callback': callback,
            'class_name': widget.__class__.__name__,
        }

        logger.debug(f"Registered widget: {widget.__class__.__name__} (id={widget_id})")

    def unregister_widget(self, widget) -> None:
        """从主题更新中注销组件

        Args:
            widget: 要注销的 QWidget
        """
        widget_id = id(widget)
        if widget_id in self._registered_widgets:
            del self._registered_widgets[widget_id]
            logger.debug(f"Unregistered widget: {widget.__class__.__name__} (id={widget_id})")

    def _on_theme_changed(self, mode: str, name: str, color: str) -> None:
        """通知所有注册的组件主题变更

        Args:
            mode: 主题模式 (light/dark/auto)
            name: 主题名称 (经典/Material3/Linear)
            color: 主题颜色 (蓝色/绿色/红色/紫色/橙色)
        """
        self._update_count += 1
        dead_refs = []

        logger.info(f"Theme changed: mode={mode}, name={name}, color={color}, "
                    f"updating {len(self._registered_widgets)} widgets")

        for widget_id, info in self._registered_widgets.items():
            widget = info['ref']()
            if widget is None:
                dead_refs.append(widget_id)
                continue

            try:
                if info['callback']:
                    # 使用自定义回调
                    info['callback'](mode, name, color)
                elif hasattr(widget, 'on_theme_changed'):
                    # 调用组件的 on_theme_changed 方法
                    widget.on_theme_changed(mode, name, color)
                elif hasattr(widget, 'refresh_theme'):
                    # 调用组件的 refresh_theme 方法
                    widget.refresh_theme()
                else:
                    logger.warning(f"Widget {info['class_name']} has no theme update method")
            except Exception as e:
                logger.error(f"Theme update failed for {info['class_name']}: {e}",
                           exc_info=True)

        # 清理死引用
        for ref_id in dead_refs:
            del self._registered_widgets[ref_id]

        logger.debug(f"Theme update complete, {self._update_count} updates so far")

    def sync_tab_bar(self, tab_bar) -> None:
        """为 QTabBar 构建并注入侧边栏主题 QSS

        Args:
            tab_bar: QTabBar 实例（内置 tab bar，非自定义类）
        """
        from app.core.theme_config import ThemeConfig
        from app.core.theme_constants import THEME_MODE_DARK
        from .theme_manager import theme_manager

        mode, name, color = theme_manager.get_current_theme()
        palette = ThemeConfig.get_palette(name, mode, color)
        is_dark = (mode == THEME_MODE_DARK)

        # 将 hex 强调色转为 RGB 三元组用于 QSS rgba()
        hex_accent = palette.accent.lstrip("#")
        r, g, b = int(hex_accent[0:2], 16), int(hex_accent[2:4], 16), int(hex_accent[4:6], 16)

        if is_dark:
            css = f"""
                QTabBar#sidebarTabBar {{
                    background: #13141f;
                    border-right: 1px solid #222236;
                    min-width: 148px;
                }}
                QTabBar#sidebarTabBar::tab {{
                    padding: 9px 14px;
                    text-align: left;
                    border-left: 3px solid transparent;
                    color: rgba(255,255,255,0.45);
                    background: transparent;
                }}
                QTabBar#sidebarTabBar::tab:selected {{
                    background: rgba({r},{g},{b},0.15);
                    color: #b8c2ff;
                    border-left: 3px solid {palette.accent};
                    font-weight: 600;
                }}
                QTabBar#sidebarTabBar::tab:hover:!selected {{
                    background: rgba(255,255,255,0.05);
                }}
            """
        else:
            css = f"""
                QTabBar#sidebarTabBar {{
                    background: #f8f9fb;
                    border-right: 1px solid #e8ecf1;
                    min-width: 148px;
                }}
                QTabBar#sidebarTabBar::tab {{
                    padding: 9px 14px;
                    text-align: left;
                    border-left: 3px solid transparent;
                    color: #64748b;
                    background: transparent;
                }}
                QTabBar#sidebarTabBar::tab:selected {{
                    background: rgba({r},{g},{b},0.10);
                    color: {palette.accent};
                    border-left: 3px solid {palette.accent};
                    font-weight: 600;
                }}
                QTabBar#sidebarTabBar::tab:hover:!selected {{
                    background: rgba(0,0,0,0.04);
                }}
            """

        tab_bar.setStyleSheet(css)

    def get_registered_count(self) -> int:
        """获取注册的组件数量"""
        return len(self._registered_widgets)

    def clear(self) -> None:
        """清除所有注册的组件"""
        self._registered_widgets.clear()
        logger.debug("Cleared all registered widgets")


# 全局主题同步实例
theme_sync = ThemeSync()
