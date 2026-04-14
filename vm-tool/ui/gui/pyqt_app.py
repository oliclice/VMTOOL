"""PyQt6高级GUI界面"""
import sys
import os
from typing import List, Dict, Any

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
from .threads import ImportThread, AddBatchThread, CalculateThread
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
        print("[GUI] ===== 开始初始化主窗口 =====", flush=True)
        super().__init__()
        print("[GUI] [1/8] 调用 super().__init__() 完成", flush=True)
        
        self.setWindowTitle("VM-TOOL - 码表处理工具")
        self.resize(1200, 800)  # 设置初始窗口大小
        print(f"[GUI] [2/8] 设置窗口标题和大小: {self.size().width()}x{self.size().height()}", flush=True)
        
        # 加载配置
        print("[GUI] 开始加载配置...", flush=True)
        self.load_config()
        print("[GUI] [3/8] 加载配置完成", flush=True)
        
        # 创建中央组件
        print("[GUI] 开始创建中央组件...", flush=True)
        self.central_widget = QWidget()
        print("[GUI] QWidget 创建完成", flush=True)
        self.setCentralWidget(self.central_widget)
        print("[GUI] [4/8] 创建中央组件完成", flush=True)
        
        # 主布局
        print("[GUI] 开始创建主布局...", flush=True)
        self.main_layout = QVBoxLayout(self.central_widget)
        print("[GUI] [5/8] 创建主布局完成", flush=True)
        
        # 创建菜单栏
        print("[GUI] 开始创建菜单栏...", flush=True)
        self.create_menu_bar()
        print("[GUI] [6/8] 创建菜单栏完成", flush=True)
        
        # 创建状态栏（集成进度条）
        print("[GUI] 开始创建状态栏...", flush=True)
        self.status_bar = QStatusBar()
        print("[GUI] QStatusBar 创建完成", flush=True)
        self.setStatusBar(self.status_bar)
        print("[GUI] [7/8] 创建状态栏完成", flush=True)
        
        # 创建统一进度条组件
        print("[GUI] 开始创建进度条...", flush=True)
        self.progress_bar = ProgressBarWidget()
        print("[GUI] ProgressBarWidget 创建完成", flush=True)
        self.status_bar.addPermanentWidget(self.progress_bar, stretch=1)
        print("[GUI] 进度条组件添加到状态栏完成", flush=True)
        
        # 线程对象
        self.calculate_thread = None
        
        # 同步初始化数据库（这个操作很快，只是创建表结构）
        print("[GUI] [8/8] 开始初始化数据库...", flush=True)
        try:
            from app.dal.init_db import init_database
            print("[GUI] 调用 init_database()...", flush=True)
            init_database()
            print("[GUI] ✓ 数据库初始化成功", flush=True)
        except Exception as e:
            print(f"[GUI] ✗ 数据库初始化失败: {e}", flush=True)
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"数据库初始化失败：{e}")
            return
        
        # 初始化服务（数据库已就绪）
        print("[GUI] 开始初始化服务...", flush=True)
        print("[GUI] 创建 DictService...", flush=True)
        self.dict_service = DictService()
        print("[GUI] ✓ DictService 初始化成功", flush=True)
        print("[GUI] 创建 WeightCalculator...", flush=True)
        self.weight_calc = WeightCalculator()
        print("[GUI] ✓ WeightCalculator 初始化成功", flush=True)
        print("[GUI] 创建 FilterService...", flush=True)
        self.filter_service = FilterService()
        print("[GUI] ✓ FilterService 初始化成功", flush=True)
        print("[GUI] 创建 StatsService...", flush=True)
        self.stats_service = StatsService()
        print("[GUI] ✓ StatsService 初始化成功", flush=True)
        
        # 创建标签页（数据库和服务都已就绪）
        print("[GUI] 开始创建标签页...", flush=True)
        self.create_tab_widget()
        print(f"[GUI] ✓ 标签页创建完成，共 {self.tab_widget.count()} 个标签", flush=True)
        
        # 设置主题（放在最后，避免影响组件创建）
        print("[GUI] 开始设置主题...", flush=True)
        theme_mode = config_manager.get("theme_mode", THEME_MODE_AUTO)
        theme_name = config_manager.get("theme_name", THEME_NAME_CLASSIC)
        theme_color = config_manager.get("theme_color", THEME_COLOR_BLUE)
        print(f"[GUI] 主题配置: mode={theme_mode}, name={theme_name}, color={theme_color}", flush=True)
        
        # 注册到主题管理器
        print("[GUI] 注册到主题管理器...", flush=True)
        theme_manager.register_widget(self)
        print("[GUI] 注册到主题管理器完成", flush=True)
        
        # 初始主题设置
        print("[GUI] 调用 set_theme()...", flush=True)
        self.set_theme(theme_mode, theme_name, theme_color)
        print("[GUI] 主题设置完成", flush=True)
        
        # 连接主题变更信号
        print("[GUI] 连接主题变更信号...", flush=True)
        theme_manager.theme_changed.connect(self.on_theme_changed)
        print("[GUI] 主题变更信号连接完成", flush=True)
        
        print("[GUI] 执行 show() 前的最后检查...", flush=True)
        print(f"[GUI] centralWidget: {self.centralWidget()}", flush=True)
        print(f"[GUI] layout: {self.layout()}", flush=True)
        print(f"[GUI] isVisible: {self.isVisible()}", flush=True)
        
        # 确保窗口在合理的位置
        from PyQt6.QtGui import QGuiApplication
        try:
            screen = QGuiApplication.primaryScreen()
            if screen:
                screen_geometry = screen.geometry()
                print(f"[GUI] 屏幕: {screen_geometry.width()}x{screen_geometry.height()}", flush=True)
                # 将窗口移动到屏幕中心
                x = (screen_geometry.width() - 1200) // 2
                y = (screen_geometry.height() - 800) // 2
                self.move(max(0, x), max(0, y))
                print(f"[GUI] 窗口移动到: ({x}, {y})", flush=True)
        except Exception as e:
            print(f"[GUI] 警告: 无法获取屏幕信息: {e}", flush=True)
        
        print("[GUI] ===== 主窗口初始化完成 =====", flush=True)
    
    def load_config(self):
        """加载配置"""
        # 配置已经通过 config_manager 自动加载，这里可以添加额外的配置加载逻辑
        pass
    
    def set_theme(self, theme_mode, theme_name, theme_color):
        """设置主题"""
        print(f"[GUI-Theme] 开始设置主题: mode={theme_mode}, name={theme_name}, color={theme_color}")
        try:
            clear_hardcoded_stylesheets(self)
            print("[GUI-Theme] ✓ 清除硬编码样式表完成")
            
            palette = create_palette_from_theme(theme_mode, theme_color)
            print("[GUI-Theme] ✓ 创建调色板完成")

            app = QApplication.instance()
            if app:
                app.setPalette(palette)
                print("[GUI-Theme] ✓ 应用调色板到 QApplication")
                
                for window in app.topLevelWidgets():
                    if hasattr(window, 'setPalette'):
                        apply_theme_to_widget(window, palette)
                print("[GUI-Theme] ✓ 应用调色板到所有窗口")
            
            self.setPalette(palette)
            apply_theme_to_widget(self, palette)
            print("[GUI-Theme] ✓ 应用调色板到主窗口完成")
            
            # 移除 repaint() 调用，避免在初始化时导致问题
            # self.update()
            # self.repaint()
            
            theme_manager.set_theme(theme_mode, theme_name, theme_color)
            print("[GUI-Theme] ✓ 主题管理器设置完成")
            print("[GUI-Theme] 主题设置全部完成")
        except Exception as e:
            print(f"[GUI-Theme] ✗ 主题设置失败: {e}")
            import traceback
            traceback.print_exc()
    
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
        """计算权重"""
        # 这里可以添加计算权重的逻辑
        pass
    
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
        print("[GUI-Menu] 开始创建菜单栏...")
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)
        print("[GUI-Menu] ✓ 菜单栏创建完成")
        
        # 文件菜单
        file_menu = QMenu("文件", self)
        menu_bar.addMenu(file_menu)
        print("[GUI-Menu] ✓ 文件菜单创建完成")
        
        import_action = QAction("导入", self)
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        print("[GUI-Menu] ✓ 导入动作添加完成")
        
        export_action = QAction("导出", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        print("[GUI-Menu] ✓ 导出动作添加完成")
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        print("[GUI-Menu] ✓ 退出动作添加完成")
        
        # 工具菜单
        tool_menu = QMenu("工具", self)
        menu_bar.addMenu(tool_menu)
        print("[GUI-Menu] ✓ 工具菜单创建完成")
        
        calculate_weight_action = QAction("计算权重", self)
        calculate_weight_action.triggered.connect(self.calculate_weight)
        tool_menu.addAction(calculate_weight_action)
        
        detect_conflicts_action = QAction("检测编码冲突", self)
        detect_conflicts_action.triggered.connect(self.detect_conflicts)
        tool_menu.addAction(detect_conflicts_action)
        
        migrate_data_action = QAction("数据迁移", self)
        migrate_data_action.triggered.connect(self.migrate_data)
        tool_menu.addAction(migrate_data_action)
        print("[GUI-Menu] ✓ 工具菜单动作添加完成")
        

        
        # 帮助菜单
        help_menu = QMenu("帮助", self)
        menu_bar.addMenu(help_menu)
        print("[GUI-Menu] ✓ 帮助菜单创建完成")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        print("[GUI-Menu] ✓ 关于动作添加完成")
        print("[GUI-Menu] 菜单栏创建全部完成")
    
    def create_tab_widget(self):
        """创建标签页"""
        print("[GUI-Tabs] ===== 开始创建标签页 =====")
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget, 1)  # 添加拉伸因子为1，让标签页占据剩余空间
        print("[GUI-Tabs] ✓ QTabWidget 创建并添加到布局")
        
        # 字表管理标签页
        print("[GUI-Tabs] 创建字表管理标签页...")
        chars_tab = CharsTab(parent=self, dict_service=self.dict_service)
        self.tab_widget.addTab(chars_tab, "字表管理")
        self.chars_tab = chars_tab
        print(f"[GUI-Tabs] ✓ 字表管理标签页创建完成 (索引: {self.tab_widget.count()-1})")
        
        # 特殊表管理标签页
        print("[GUI-Tabs] 创建特殊表管理标签页...")
        special_tab = SpecialTab(parent=self, dict_service=self.dict_service)
        self.tab_widget.addTab(special_tab, "特殊表管理")
        self.special_tab = special_tab
        print(f"[GUI-Tabs] ✓ 特殊表管理标签页创建完成 (索引: {self.tab_widget.count()-1})")
        
        # 词表管理标签页
        print("[GUI-Tabs] 创建词表管理标签页...")
        words_tab = WordsTab(parent=self, dict_service=self.dict_service)
        self.tab_widget.addTab(words_tab, "词表管理")
        self.words_tab = words_tab
        print(f"[GUI-Tabs] ✓ 词表管理标签页创建完成 (索引: {self.tab_widget.count()-1})")
        
        # 统计分析标签页
        print("[GUI-Tabs] 创建统计分析标签页...")
        stats_tab = StatsTab(parent=self, stats_service=self.stats_service)
        self.tab_widget.addTab(stats_tab, "统计分析")
        self.stats_tab = stats_tab
        print(f"[GUI-Tabs] ✓ 统计分析标签页创建完成 (索引: {self.tab_widget.count()-1})")
        
        # 导入导出标签页
        print("[GUI-Tabs] 创建导入导出标签页...")
        import_export_tab = ImportExportTab(parent=self, filter_service=self.filter_service, dict_service=self.dict_service)
        self.tab_widget.addTab(import_export_tab, "导入导出")
        self.import_export_tab = import_export_tab
        print(f"[GUI-Tabs] ✓ 导入导出标签页创建完成 (索引: {self.tab_widget.count()-1})")
        
        # 编码规则标签页
        print("[GUI-Tabs] 创建编码规则标签页...")
        code_rules_tab = CodeRulesTab(parent=self, dict_service=self.dict_service)
        self.tab_widget.addTab(code_rules_tab, "编码规则")
        self.code_rules_tab = code_rules_tab
        print(f"[GUI-Tabs] ✓ 编码规则标签页创建完成 (索引: {self.tab_widget.count()-1})")
        
        # 设置标签页
        print("[GUI-Tabs] 创建设置标签页...")
        settings_tab = QWidget()
        self.tab_widget.addTab(settings_tab, "设置")
        self.create_settings_tab(settings_tab)
        print(f"[GUI-Tabs] ✓ 设置标签页创建完成 (索引: {self.tab_widget.count()-1})")
        
        print(f"[GUI-Tabs] ===== 标签页创建全部完成，共 {self.tab_widget.count()} 个标签 =====")
    

    

    
    
    
        

    
