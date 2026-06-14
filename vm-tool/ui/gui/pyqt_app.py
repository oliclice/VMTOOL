"""PyQt6高级GUI界面"""
import sys
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
    QLabel, QDialog, QFormLayout, QComboBox, QMessageBox, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QSplitter, QStatusBar, QMenuBar, QMenu,
    QTextEdit, QGroupBox, QProgressBar, QCheckBox
)
from PyQt6.QtCore import Qt, QSortFilterProxyModel, QThread, pyqtSignal, QEvent
from PyQt6.QtGui import QAction, QIcon, QFont, QStandardItemModel, QStandardItem, QPalette, QFontDatabase

from app.services.dict import DictService
from app.services.weight import WeightCalculator
from app.services.filter import FilterService
from app.services.stats import StatsService
from app.core.config_manager import config_manager
from app.core.theme_constants import (
    THEME_MODE_DARK, THEME_MODE_LIGHT, THEME_MODE_AUTO,
    THEME_NAME_CLASSIC, THEME_NAME_LINEAR, THEME_NAME_MATERIAL3,
    THEME_COLOR_BLUE, THEME_COLOR_GREEN,
    THEME_COLOR_RED, THEME_COLOR_PURPLE, THEME_COLOR_ORANGE,
    COLOR_RGB_MAP
)
from .theme_utils import create_palette_from_theme, apply_theme_to_widget, clear_hardcoded_stylesheets
from .theme_manager import theme_manager
from .settings_tab import SettingsTab
from .code_rules_tab import CodeRulesTab
from .threads import ImportThread, AddBatchThread, CalculateThread, CalculateWeightThread
from .tabs.chars_tab import CharsTab
from .tabs.special_tab import SpecialTab
from .tabs.words_tab import WordsTab
from .tabs.stats_tab import StatsTab
from .tabs.import_export_tab import ImportExportTab
from .progress_bar import ProgressBarWidget
from .widgets.sidebar_nav import SidebarNav
from .widgets.dashboard_page import DashboardPage


class VMTOOLPyQtApp(QMainWindow):
    """VM-TOOL PyQt6 GUI应用"""

    def __init__(self):
        """初始化应用"""
        super().__init__()

        self.setWindowTitle("VM-TOOL - 码表处理工具")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        # 加载配置
        self.load_config()

        # 创建中央组件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 创建菜单栏
        self.create_menu_bar()

        # 创建状态栏（集成进度条）
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 创建统一进度条组件
        self.progress_bar = ProgressBarWidget()
        self.status_bar.addPermanentWidget(self.progress_bar, stretch=1)

        # 线程对象
        self.calculate_thread = None

        # 同步初始化数据库（这个操作很快，只是创建表结构）
        try:
            from app.dal.init_db import init_database
            init_database()
        except Exception as e:
            logger.error(f"[GUI] 数据库初始化失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"数据库初始化失败：{e}")
            return

        # 初始化服务（数据库已就绪）
        self.dict_service = DictService()
        self.weight_calc = WeightCalculator()
        self.filter_service = FilterService()
        self.stats_service = StatsService()

        # 创建侧边栏和内容区（数据库和服务都已就绪）
        self.create_sidebar_and_content()

        # 设置主题（放在最后，避免影响组件创建）
        theme_mode = config_manager.get("theme_mode", THEME_MODE_AUTO)
        theme_name = config_manager.get("theme_name", THEME_NAME_CLASSIC)
        theme_color = config_manager.get("theme_color", THEME_COLOR_BLUE)

        # 注册到主题管理器
        theme_manager.register_widget(self)

        # 初始主题设置
        self.set_theme(theme_mode, theme_name, theme_color)

        # 连接主题变更信号
        theme_manager.theme_changed.connect(self.on_theme_changed)

        # 确保窗口在合理的位置
        from PyQt6.QtGui import QGuiApplication
        try:
            screen = QGuiApplication.primaryScreen()
            if screen:
                screen_geometry = screen.geometry()
                x = (screen_geometry.width() - 1200) // 2
                y = (screen_geometry.height() - 800) // 2
                self.move(max(0, x), max(0, y))
        except Exception as e:
            logger.warning(f"[GUI] 无法获取屏幕信息: {e}")

    def load_config(self):
        """加载配置"""
        # 配置已经通过 config_manager 自动加载，这里可以添加额外的配置加载逻辑
        pass

    def set_theme(self, theme_mode, theme_name, theme_color):
        """设置主题"""
        try:
            clear_hardcoded_stylesheets(self)

            # 使用 ThemeConfig 创建调色板
            from app.core.theme_config import ThemeConfig
            palette = ThemeConfig.get_qpalette(theme_name, theme_mode, theme_color)

            app = QApplication.instance()
            if app:
                app.setPalette(palette)

                for window in app.topLevelWidgets():
                    if hasattr(window, 'setPalette'):
                        apply_theme_to_widget(window, palette)

            self.setPalette(palette)
            apply_theme_to_widget(self, palette)

            # 应用 QSS 样式表 (Linear 或 Material3)
            self._apply_theme_stylesheet(theme_name, theme_mode, theme_color)

            # 更新主题管理器（这会触发 theme_changed 信号通知所有注册的组件）
            theme_manager.set_theme(theme_mode, theme_name, theme_color)
        except Exception as e:
            logger.error(f"[GUI-Theme] 主题设置失败: {e}", exc_info=True)

    def _apply_theme_stylesheet(self, theme_name, theme_mode, theme_color):
        """应用主题 QSS 样式表"""
        from app.core.theme_config import ThemeConfig

        if theme_name == THEME_NAME_LINEAR:
            # Linear 主题使用 QSS
            palette = ThemeConfig.get_palette(theme_name, theme_mode, theme_color)
            from .styles import load_linear_theme_qss
            qss = load_linear_theme_qss(theme_mode, theme_color)
            from .styles.theme_variables import resolve_qss_variables
            qss = resolve_qss_variables(qss, palette)
            QApplication.instance().setStyleSheet(qss)
        elif theme_name == THEME_NAME_MATERIAL3:
            # Material3 主题使用 QSS
            palette = ThemeConfig.get_palette(theme_name, theme_mode, theme_color)
            from .styles.theme_variables import resolve_qss_variables
            import os
            qss_path = os.path.join(os.path.dirname(__file__), "styles", "material_theme.qss")
            with open(qss_path, "r", encoding="utf-8") as f:
                qss = f.read()
            qss = resolve_qss_variables(qss, palette)
            QApplication.instance().setStyleSheet(qss)
        else:
            # 经典主题不使用 QSS，仅依赖 QPalette
            QApplication.instance().setStyleSheet("")

    def on_theme_changed(self, theme_mode, theme_name, theme_color):
        """处理主题变更信号 - 仅应用主题，不重复调用 set_theme"""
        try:
            clear_hardcoded_stylesheets(self)

            # 使用 ThemeConfig 创建调色板
            from app.core.theme_config import ThemeConfig
            palette = ThemeConfig.get_qpalette(theme_name, theme_mode, theme_color)

            app = QApplication.instance()
            if app:
                app.setPalette(palette)

                for window in app.topLevelWidgets():
                    if hasattr(window, 'setPalette'):
                        apply_theme_to_widget(window, palette)

            self.setPalette(palette)
            apply_theme_to_widget(self, palette)

            # 应用 QSS 样式表
            self._apply_theme_stylesheet(theme_name, theme_mode, theme_color)
        except Exception as e:
            logger.error(f"[GUI-Theme] 主题设置失败: {e}", exc_info=True)

    def import_data(self):
        """导入数据"""
        if not hasattr(self, 'import_export_tab'):
            QMessageBox.warning(self, "警告", "导入导出标签页未初始化")
            return
        self.import_export_tab.import_data()

    def export_data(self):
        """导出数据"""
        if not hasattr(self, 'import_export_tab'):
            QMessageBox.warning(self, "警告", "导入导出标签页未初始化")
            return
        self.import_export_tab.export_data()

    def calculate_weight(self):
        """计算权重 - 基于词频对数重新计算所有词条权重"""
        reply = QMessageBox.question(
            self, "确认", "将基于词频数据重新计算所有词条权重，是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        progress_bar = self.progress_bar
        if progress_bar:
            progress_bar.start_progress("正在计算权重...")

        self.calc_weight_thread = CalculateWeightThread(self.weight_calc)

        def update_progress(progress, message):
            if progress_bar:
                progress_bar.update_progress(progress, message)

        def on_finished(result):
            updated = result.get("updated", 0)
            total = result.get("total", 0)
            msg = f"权重计算完成，共 {total} 条，更新 {updated} 条"
            if progress_bar:
                progress_bar.finish_progress(msg, success=True)
            else:
                self.status_bar.showMessage(msg, 5000)

        def on_error(error):
            msg = f"权重计算失败：{error}"
            if progress_bar:
                progress_bar.error_progress(msg)
            else:
                QMessageBox.critical(self, "错误", msg)

        self.calc_weight_thread.progress.connect(update_progress)
        self.calc_weight_thread.finished.connect(on_finished)
        self.calc_weight_thread.error.connect(on_error)
        self.calc_weight_thread.start()

    def detect_conflicts(self):
        """检测编码冲突"""
        # 这里可以添加检测编码冲突的逻辑
        pass

    def migrate_data(self):
        """数据迁移"""
        # 这里可以添加数据迁移的逻辑
        pass

    def show_about(self):
        """显示关于对话框"""
        # 这里可以添加显示关于对话框的逻辑
        pass

    def create_settings_tab(self, parent):
        """创建设置标签页"""
        from .settings_tab import SettingsTab
        layout = QVBoxLayout(parent)

        # 创建 SettingsTab 实例
        settings_tab = SettingsTab(parent=self, dict_service=self.dict_service)
        layout.addWidget(settings_tab)

    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)

        # 文件菜单
        file_menu = QMenu("文件", self)
        menu_bar.addMenu(file_menu)

        import_action = QAction("导入", self)
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)

        export_action = QAction("导出", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 工具菜单
        tool_menu = QMenu("工具", self)
        menu_bar.addMenu(tool_menu)

        calculate_weight_action = QAction("计算权重", self)
        calculate_weight_action.triggered.connect(self.calculate_weight)
        tool_menu.addAction(calculate_weight_action)

        detect_conflicts_action = QAction("检测编码冲突", self)
        detect_conflicts_action.triggered.connect(self.detect_conflicts)
        tool_menu.addAction(detect_conflicts_action)

        migrate_data_action = QAction("数据迁移", self)
        migrate_data_action.triggered.connect(self.migrate_data)
        tool_menu.addAction(migrate_data_action)

        # 帮助菜单
        help_menu = QMenu("帮助", self)
        menu_bar.addMenu(help_menu)

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_sidebar_and_content(self):
        """创建侧边栏导航和内容区"""
        from app.core.theme_constants import TAB_ICONS

        # 创建 QSplitter 作为主容器
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)

        # 创建侧边栏导航
        self.sidebar_nav = SidebarNav()
        self.sidebar_nav.setMinimumWidth(200)
        self.sidebar_nav.setMaximumWidth(300)
        self.splitter.addWidget(self.sidebar_nav)

        # 创建内容区 (QStackedWidget)
        self.content_stack = QStackedWidget()
        self.splitter.addWidget(self.content_stack)

        # 设置默认比例 220:980
        self.splitter.setSizes([220, 980])
        self.main_layout.addWidget(self.splitter, 1)

        # 创建页面并添加到侧边栏
        # [0] Dashboard
        dashboard_page = DashboardPage(
            parent=self,
            dict_service=self.dict_service,
            stats_service=self.stats_service
        )
        self.content_stack.addWidget(dashboard_page)
        self.sidebar_nav.add_group("概览")
        self.sidebar_nav.add_item("📊", "首页", 0)

        # [1] 字表管理
        self.chars_tab = CharsTab(parent=self, dict_service=self.dict_service)
        self.content_stack.addWidget(self.chars_tab)

        # [2] 特殊表管理
        self.special_tab = SpecialTab(parent=self, dict_service=self.dict_service)
        self.content_stack.addWidget(self.special_tab)

        # [3] 词表管理
        self.words_tab = WordsTab(parent=self, dict_service=self.dict_service)
        self.content_stack.addWidget(self.words_tab)

        self.sidebar_nav.add_group("数据管理")
        self.sidebar_nav.add_item(TAB_ICONS["chars"], "字表管理", 1)
        self.sidebar_nav.add_item(TAB_ICONS["special"], "特殊表管理", 2)
        self.sidebar_nav.add_item(TAB_ICONS["words"], "词表管理", 3)

        # [4] 统计分析
        self.stats_tab = StatsTab(parent=self, stats_service=self.stats_service)
        self.content_stack.addWidget(self.stats_tab)

        # [5] 导入导出
        self.import_export_tab = ImportExportTab(
            parent=self,
            filter_service=self.filter_service,
            dict_service=self.dict_service
        )
        self.content_stack.addWidget(self.import_export_tab)

        # [6] 编码规则
        self.code_rules_tab = CodeRulesTab(parent=self, dict_service=self.dict_service)
        self.content_stack.addWidget(self.code_rules_tab)

        self.sidebar_nav.add_group("工具")
        self.sidebar_nav.add_item(TAB_ICONS["stats"], "统计分析", 4)
        self.sidebar_nav.add_item(TAB_ICONS["import_export"], "导入导出", 5)
        self.sidebar_nav.add_item(TAB_ICONS["code_rules"], "编码规则", 6)

        # 分隔线
        self.sidebar_nav.add_separator()

        # [7] 设置
        settings_tab = SettingsTab(parent=self, dict_service=self.dict_service)
        self.content_stack.addWidget(settings_tab)

        self.sidebar_nav.add_item(TAB_ICONS["settings"], "设置", 7)

        # 添加版本号到侧边栏底部
        from PyQt6.QtWidgets import QSizePolicy
        version_label = QLabel("v1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("font-size: 10px; color: #62666d; padding: 8px;")
        self.sidebar_nav.add_bottom_widget(version_label)

        # 连接信号
        self.sidebar_nav.nav_changed.connect(self._on_nav_changed)

        # 设置默认选中首页
        self.sidebar_nav.set_active(0)
        self.content_stack.setCurrentIndex(0)

        # 刷新仪表盘数据
        dashboard_page.refresh()

    def _on_nav_changed(self, page_index: int):
        """导航切换处理"""
        self.content_stack.setCurrentIndex(page_index)
        # 如果切换到仪表盘，刷新数据
        if page_index == 0:
            dashboard = self.content_stack.widget(0)
            if hasattr(dashboard, 'refresh'):
                dashboard.refresh()
