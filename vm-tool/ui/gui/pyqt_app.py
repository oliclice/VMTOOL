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
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
    QLabel, QDialog, QFormLayout, QComboBox, QMessageBox, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QSplitter, QStatusBar, QMenuBar, QMenu,
    QTextEdit, QGroupBox, QProgressBar, QCheckBox
)
from PyQt6.QtCore import Qt, QSortFilterProxyModel, QThread, pyqtSignal, QEvent
from PyQt6.QtGui import QAction, QIcon, QFont, QColor, QStandardItemModel, QStandardItem, QPalette, QFontDatabase
from PyQt6.QtWidgets import QStyle

from app.services.dict import DictService
from app.services.weight import WeightCalculator
from app.services.filter import FilterService
from app.services.stats import StatsService
from app.core.config_manager import config_manager
from app.core.theme_constants import (
    THEME_MODE_DARK, THEME_MODE_LIGHT, THEME_MODE_AUTO,
    THEME_NAME_CLASSIC, THEME_COLOR_BLUE, THEME_COLOR_GREEN,
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


class VMTOOLPyQtApp(QMainWindow):
    """VM-TOOL PyQt6 GUI应用"""

    def __init__(self):
        """初始化应用"""
        super().__init__()

        self.setWindowTitle("VM-TOOL - 码表处理工具")
        self.resize(1200, 800)  # 设置初始窗口大小

        # 加载配置
        self.load_config()

        # 创建中央组件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)

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

        # 创建标签页（数据库和服务都已就绪）
        self.create_tab_widget()

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
                # 将窗口移动到屏幕中心
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

            palette = create_palette_from_theme(theme_mode, theme_color)

            app = QApplication.instance()
            if app:
                app.setPalette(palette)

                for window in app.topLevelWidgets():
                    if hasattr(window, 'setPalette'):
                        apply_theme_to_widget(window, palette)

            self.setPalette(palette)
            apply_theme_to_widget(self, palette)

            # 移除 repaint() 调用，避免在初始化时导致问题
            # self.update()
            # self.repaint()

            theme_manager.set_theme(theme_mode, theme_name, theme_color)
        except Exception as e:
            logger.error(f"[GUI-Theme] 主题设置失败: {e}", exc_info=True)

    def on_theme_changed(self, theme_mode, theme_name, theme_color):
        """处理主题变更信号"""
        self.set_theme(theme_mode, theme_name, theme_color)

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

    def create_tab_widget(self):
        """创建标签页"""
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget, 1)  # 添加拉伸因子为1，让标签页占据剩余空间

        # 字表管理标签页
        chars_tab = CharsTab(parent=self, dict_service=self.dict_service)
        self.tab_widget.addTab(chars_tab, "字表管理")
        self.chars_tab = chars_tab

        # 特殊表管理标签页
        special_tab = SpecialTab(parent=self, dict_service=self.dict_service)
        self.tab_widget.addTab(special_tab, "特殊表管理")
        self.special_tab = special_tab

        # 词表管理标签页
        words_tab = WordsTab(parent=self, dict_service=self.dict_service)
        self.tab_widget.addTab(words_tab, "词表管理")
        self.words_tab = words_tab

        # 统计分析标签页
        stats_tab = StatsTab(parent=self, stats_service=self.stats_service)
        self.tab_widget.addTab(stats_tab, "统计分析")
        self.stats_tab = stats_tab

        # 导入导出标签页
        import_export_tab = ImportExportTab(parent=self, filter_service=self.filter_service, dict_service=self.dict_service)
        self.tab_widget.addTab(import_export_tab, "导入导出")
        self.import_export_tab = import_export_tab

        # 编码规则标签页
        code_rules_tab = CodeRulesTab(parent=self, dict_service=self.dict_service)
        self.tab_widget.addTab(code_rules_tab, "编码规则")
        self.code_rules_tab = code_rules_tab

        # 设置标签页
        settings_tab = QWidget()
        self.tab_widget.addTab(settings_tab, "设置")
        self.create_settings_tab(settings_tab)
