from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QLineEdit, QLabel, QComboBox, QMenu, QMessageBox)
from PyQt6.QtCore import Qt
import logging
from app.services.dict import DictService
from ..threads import AddBatchThread

logger = logging.getLogger(__name__)

class BaseTableTab(QWidget):
    """表格管理标签页基类"""
    def __init__(self, parent=None, dict_service=None):
        logger.debug(f"[BaseTableTab] ===== 开始初始化 {self.__class__.__name__} =====")
        super().__init__(parent)
        logger.debug(f"[BaseTableTab] [1/4] 调用 super().__init__() 完成")
        
        self.dict_service = dict_service
        logger.debug(f"[BaseTableTab] [2/4] dict_service 设置: {'✓' if dict_service else '✗'}")
        
        self.is_initializing = True
        logger.debug(f"[BaseTableTab] [3/4] 开始初始化 UI...")
        self.init_ui()
        logger.debug(f"[BaseTableTab] [4/4] UI 初始化完成，开始刷新数据...")
        
        self.refresh_data()
        logger.debug(f"[BaseTableTab] 数据刷新完成")
        
        self.is_initializing = False
        logger.debug(f"[BaseTableTab] ===== {self.__class__.__name__} 初始化完成 =====")
    
    def init_ui(self):
        """初始化UI"""
        logger.debug(f"[BaseTableTab-UI] 开始初始化 UI 组件...")
        layout = QVBoxLayout(self)
        logger.debug(f"[BaseTableTab-UI] ✓ 创建主布局")
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入关键词搜索")
        logger.debug(f"[BaseTableTab-UI] ✓ 创建搜索框")
        
        # 添加字段选择下拉菜单
        self.search_field = QComboBox()
        self.search_field.addItems(["词", "编码", "权重", "手动"])
        logger.debug(f"[BaseTableTab-UI] ✓ 创建搜索字段下拉菜单")
        
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.search_data)
        logger.debug(f"[BaseTableTab-UI] ✓ 创建搜索按钮")
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.search_field)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        logger.debug(f"[BaseTableTab-UI] ✓ 搜索框布局添加完成")
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["词", "编码", "权重", "手动"])
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        logger.debug(f"[BaseTableTab-UI] ✓ 创建表格组件 (4列)")
        
        # 设置列宽
        self.set_column_widths()
        logger.debug(f"[BaseTableTab-UI] ✓ 设置列宽完成")
        
        # 允许单元格编辑
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked)
        logger.debug(f"[BaseTableTab-UI] ✓ 设置单元格编辑模式")
        
        # 监听编辑完成信号
        self.table.cellChanged.connect(self.on_cell_changed)
        logger.debug(f"[BaseTableTab-UI] ✓ 连接 cellChanged 信号")
        
        # 添加右键菜单
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        logger.debug(f"[BaseTableTab-UI] ✓ 设置右键菜单")
        
        layout.addWidget(self.table)
        logger.debug(f"[BaseTableTab-UI] ✓ 表格添加到布局")
        
        # 操作按钮
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_item)
        logger.debug(f"[BaseTableTab-UI] ✓ 创建添加按钮")
        
        add_batch_button = QPushButton("批量添加")
        add_batch_button.clicked.connect(self.add_batch_items)
        logger.debug(f"[BaseTableTab-UI] ✓ 创建批量添加按钮")
        
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self.delete_item)
        logger.debug(f"[BaseTableTab-UI] ✓ 创建删除按钮")
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_data)
        logger.debug(f"[BaseTableTab-UI] ✓ 创建刷新按钮")
        
        # 添加额外按钮
        self.add_extra_buttons(button_layout)
        logger.debug(f"[BaseTableTab-UI] ✓ 添加额外按钮")
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(add_batch_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(refresh_button)
        layout.addLayout(button_layout)
        logger.debug(f"[BaseTableTab-UI] ✓ 按钮布局添加完成")
        logger.debug(f"[BaseTableTab-UI] UI 初始化全部完成")
    
    def set_column_widths(self):
        """设置列宽，子类可重写"""
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)
    
    def add_extra_buttons(self, layout):
        """添加额外按钮，子类可重写"""
        pass
    
    def refresh_data(self):
        """刷新数据，子类必须重写"""
        raise NotImplementedError
    
    def search_data(self):
        """搜索数据，子类必须重写"""
        raise NotImplementedError
    
    def add_item(self):
        """添加项，子类必须重写"""
        raise NotImplementedError
    
    def add_batch_items(self):
        """批量添加项，子类必须重写"""
        raise NotImplementedError
    
    def delete_item(self):
        """删除项，子类必须重写"""
        raise NotImplementedError
    
    def update_item(self):
        """更新项，子类必须重写"""
        raise NotImplementedError
    
    def on_cell_changed(self, row, column):
        """处理单元格编辑完成，子类必须重写"""
        raise NotImplementedError
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        if not self.dict_service:
            return
        
        menu = QMenu()
        
        add_action = menu.addAction("添加")
        delete_action = menu.addAction("删除")
        update_action = menu.addAction("编辑")
        
        action = menu.exec(self.table.mapToGlobal(position))
        
        if action == add_action:
            self.add_item()
        elif action == delete_action:
            self.delete_item()
        elif action == update_action:
            self.update_item()