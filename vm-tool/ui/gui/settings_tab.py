from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
                             QComboBox, QPushButton, QTreeWidget, QTreeWidgetItem, 
                             QSplitter, QScrollArea, QGroupBox, QLineEdit, QTextEdit, 
                             QCheckBox, QFontDialog, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase
import os
from app.core.config_manager import config_manager
from app.services.dict import DictService
from .settings import (
    load_theme_settings,
    load_language_settings,
    load_code_rules,
    load_config_dir_settings,
    load_database_path_settings,
    load_cache_settings,
    load_delete_table_settings,
    load_file_config_settings,
    load_stats_settings,
    load_weight_settings
)

class SettingsTab(QWidget):
    """设置标签页"""
    def __init__(self, parent=None, dict_service=None):
        super().__init__(parent)
        self.dict_service = dict_service
        self.section_widgets = {}
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QHBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Horizontal)
        
        # 左侧设置类型列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        settings_types = QTreeWidget()
        settings_types.setHeaderLabel("设置类型")
        # 允许拖动排序
        settings_types.setDragEnabled(True)
        settings_types.setDropIndicatorShown(True)
        settings_types.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        
        # 从配置中加载设置类型顺序，如果没有则使用默认顺序
        default_sections = ["主题设置", "字体设置", "语言设置",
                          "配置目录", "数据库路径", "缓存设置", "统计设置", "删除表", "文件配置", "权重计算"]
        sections = config_manager.get("settings_order", default_sections)
        
        # 添加设置类型
        for section in sections:
            QTreeWidgetItem(settings_types, [section])
        
        # 连接拖动结束信号
        settings_types.model().rowsInserted.connect(self.on_settings_order_changed)
        
        left_layout.addWidget(settings_types)
        splitter.addWidget(left_widget)
        
        # 右侧设置内容
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 设置标题
        self.settings_title = QLabel("设置")
        self.settings_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        right_layout.addWidget(self.settings_title)
        
        # 设置内容区域 - 使用滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.settings_content = QWidget()
        self.settings_content_layout = QVBoxLayout(self.settings_content)
        # 调整布局间距
        self.settings_content_layout.setSpacing(10)
        self.settings_content_layout.setContentsMargins(10, 10, 10, 10)
        
        # 加载所有设置项
        self.load_all_settings()
        
        scroll_area.setWidget(self.settings_content)
        right_layout.addWidget(scroll_area)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器大小
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter)
        
        # 连接信号
        settings_types.itemClicked.connect(self.on_settings_type_clicked)
    
    def load_all_settings(self):
        """加载所有设置项"""
        # 主题设置
        load_theme_settings(self.settings_content_layout, self.section_widgets, self.parent())
        
        # 语言设置（包含字体设置）
        load_language_settings(self.settings_content_layout, self.section_widgets, self.parent())
        
        # 编码规则
        load_code_rules(self.settings_content_layout, self.section_widgets, self.parent())
        
        # 配置目录
        load_config_dir_settings(self.settings_content_layout, self.section_widgets, self.parent())
        
        # 数据库路径
        load_database_path_settings(self.settings_content_layout, self.section_widgets, self.parent())
        
        # 缓存设置
        load_cache_settings(self.settings_content_layout, self.section_widgets, self.parent())
        
        # 删除表
        load_delete_table_settings(self.settings_content_layout, self.section_widgets, self.parent(), self.dict_service)
        
        # 文件配置
        load_file_config_settings(self.settings_content_layout, self.section_widgets, self.parent())
        
        # 统计设置
        load_stats_settings(self.settings_content_layout, self.section_widgets, self.parent())

        # 权重计算
        load_weight_settings(self.settings_content_layout, self.section_widgets, self.parent())


    

    

    

    

    

    

    

    

    

    

    

    

    
    def on_settings_order_changed(self):
        """设置类型顺序改变事件"""
        # 获取当前的设置类型顺序
        settings_types = self.findChild(QTreeWidget)
        if settings_types:
            sections = []
            for i in range(settings_types.topLevelItemCount()):
                item = settings_types.topLevelItem(i)
                sections.append(item.text(0))
            
            # 保存到配置文件
            config_manager.set("settings_order", sections)
            
            # 重新加载设置内容，按照新的顺序
            self.reload_settings_content()
    
    def reload_settings_content(self):
        """重新加载设置内容"""
        # 清除当前的设置内容
        for widget in self.section_widgets.values():
            widget.deleteLater()
        self.section_widgets.clear()
        
        # 从配置中加载设置类型顺序
        default_sections = ["主题设置", "语言设置", "编码规则",
                          "配置目录", "数据库路径", "缓存设置", "统计设置", "删除表", "文件配置", "权重计算"]
        sections = config_manager.get("settings_order", default_sections)
        
        # 按照新的顺序加载设置
        for section in sections:
            if section == "主题设置":
                load_theme_settings(self.settings_content_layout, self.section_widgets, self.parent())
            elif section == "语言设置":
                load_language_settings(self.settings_content_layout, self.section_widgets, self.parent())
            elif section == "编码规则":
                load_code_rules(self.settings_content_layout, self.section_widgets, self.parent())
            elif section == "配置目录":
                load_config_dir_settings(self.settings_content_layout, self.section_widgets, self.parent())
            elif section == "数据库路径":
                load_database_path_settings(self.settings_content_layout, self.section_widgets, self.parent())
            elif section == "缓存设置":
                load_cache_settings(self.settings_content_layout, self.section_widgets, self.parent())
            elif section == "统计设置":
                load_stats_settings(self.settings_content_layout, self.section_widgets, self.parent())
            elif section == "删除表":
                load_delete_table_settings(self.settings_content_layout, self.section_widgets, self.parent(), self.dict_service)
            elif section == "文件配置":
                load_file_config_settings(self.settings_content_layout, self.section_widgets, self.parent())
            elif section == "权重计算":
                load_weight_settings(self.settings_content_layout, self.section_widgets, self.parent())
    
    def on_settings_type_clicked(self, tree_item, column):
        """设置类型点击事件"""
        # 获取选中的设置类型
        settings_type = tree_item.text(column)
        
        # 滚动到对应的设置部分
        if settings_type in self.section_widgets:
            widget = self.section_widgets[settings_type]
            # 滚动到该控件
            scroll_area = self.parent().findChild(QScrollArea)
            if scroll_area:
                scroll_area.ensureWidgetVisible(widget)
    
    def save_settings(self):
        """保存设置"""
        # 配置会在修改时自动保存，这里只是显示一个提示
        if hasattr(self.parent(), 'show_toast'):
            self.parent().show_toast("设置已保存")
    
