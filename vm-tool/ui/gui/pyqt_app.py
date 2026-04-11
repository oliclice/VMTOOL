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
    QProgressDialog, QTextEdit, QGroupBox, QProgressBar, QCheckBox
)
from PyQt6.QtCore import Qt, QSortFilterProxyModel, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QFont, QColor, QStandardItemModel, QStandardItem, QPalette

from app.services.dict import DictService
from app.services.weight import WeightCalculator
from app.services.filter import FilterService
from app.services.stats import StatsService
from app.core.config_manager import config_manager


class ImportThread(QThread):
    """导入线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, filter_service, file_path, format):
        super().__init__()
        self.filter_service = filter_service
        self.file_path = file_path
        self.format = format
    
    def run(self):
        try:
            def progress_callback(progress, message):
                self.progress.emit(progress, message)
            
            if self.format == "txt":
                result = self.filter_service.import_from_txt(self.file_path, progress_callback=progress_callback)
            elif self.format == "csv":
                result = self.filter_service.import_from_csv(self.file_path, progress_callback=progress_callback)
            elif self.format == "json":
                result = self.filter_service.import_from_json(self.file_path, progress_callback=progress_callback)
            else:
                self.error.emit("不支持的格式")
                return
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AddBatchThread(QThread):
    """批量添加线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, dict_service, items, is_character=False):
        super().__init__()
        self.dict_service = dict_service
        self.items = items
        self.is_character = is_character
    
    def run(self):
        try:
            def progress_callback(progress, message):
                self.progress.emit(progress, message)
            
            item_data = []
            for item in self.items:
                item_data.append({"word": item, "code": None, "weight": 1.0})
            
            if self.is_character:
                result = self.dict_service.add_characters(item_data, progress_callback=progress_callback)
            else:
                result = self.dict_service.add_words(item_data, progress_callback=progress_callback)
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class VMTOOLPyQtApp(QMainWindow):
    """VM-TOOL PyQt6 GUI应用"""
    
    def __init__(self):
        """初始化应用"""
        super().__init__()
        self.setWindowTitle("VM-TOOL - 码表处理工具")
        
        # 加载配置
        self.load_config()
        
        # 创建中央组件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 初始化数据库
        try:
            from app.dal.init_db import init_database
            init_database()
            self.status_bar.showMessage("数据库初始化成功")
        except Exception as e:
            self.status_bar.showMessage(f"数据库初始化失败: {e}")
        
        # 初始化服务
        self.dict_service = DictService()
        self.weight_calc = WeightCalculator()
        self.filter_service = FilterService()
        self.stats_service = StatsService()
        
        # 初始化主题设置
        theme_name = config_manager.get("theme_name", "经典")
        theme_mode = config_manager.get("theme_mode", "auto")
        self.set_theme(theme_mode, theme_name)
        
        # 创建标签页
        self.create_tab_widget()
    
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
        self.main_layout.addWidget(self.tab_widget)
        
        # 字表管理标签页
        chars_tab = QWidget()
        self.tab_widget.addTab(chars_tab, "字表管理")
        self.create_chars_tab(chars_tab)
        
        # 词表管理标签页
        words_tab = QWidget()
        self.tab_widget.addTab(words_tab, "词表管理")
        self.create_words_tab(words_tab)
        
        # 统计分析标签页
        stats_tab = QWidget()
        self.tab_widget.addTab(stats_tab, "统计分析")
        self.create_stats_tab(stats_tab)
        
        # 导入导出标签页
        import_export_tab = QWidget()
        self.tab_widget.addTab(import_export_tab, "导入导出")
        self.create_import_export_tab(import_export_tab)
        
        # 设置标签页
        settings_tab = QWidget()
        self.tab_widget.addTab(settings_tab, "设置")
        self.create_settings_tab(settings_tab)
    
    def create_chars_tab(self, parent):
        """创建字表管理标签页"""
        layout = QVBoxLayout(parent)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.char_search_edit = QLineEdit()
        self.char_search_edit.setPlaceholderText("输入关键词搜索")
        
        # 添加字段选择下拉菜单
        self.char_search_field = QComboBox()
        self.char_search_field.addItems(["字", "编码", "权重", "手动"])
        
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.search_chars)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.char_search_edit)
        search_layout.addWidget(self.char_search_field)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        
        # 字表表格
        self.char_table = QTableWidget()
        self.char_table.setColumnCount(4)
        self.char_table.setHorizontalHeaderLabels(["字", "编码", "权重", "手动"])
        self.char_table.setSortingEnabled(True)
        self.char_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 设置列宽
        self.char_table.setColumnWidth(0, 100)
        self.char_table.setColumnWidth(1, 150)
        self.char_table.setColumnWidth(2, 100)
        self.char_table.setColumnWidth(3, 80)
        
        # 添加右键菜单
        self.char_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.char_table.customContextMenuRequested.connect(self.show_char_context_menu)
        
        layout.addWidget(self.char_table)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_char)
        
        add_batch_button = QPushButton("批量添加")
        add_batch_button.clicked.connect(self.add_batch_chars)
        
        edit_button = QPushButton("编辑")
        edit_button.clicked.connect(self.edit_char)
        
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self.delete_char)
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_chars)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(add_batch_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(refresh_button)
        layout.addLayout(button_layout)
        
        # 加载字表
        self.refresh_chars()
    
    def create_words_tab(self, parent):
        """创建词表管理标签页"""
        layout = QVBoxLayout(parent)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入关键词搜索")
        
        # 添加字段选择下拉菜单
        self.word_search_field = QComboBox()
        self.word_search_field.addItems(["词", "编码", "权重", "手动"])
        
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.search_words)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.word_search_field)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        
        # 词表表格
        self.word_table = QTableWidget()
        self.word_table.setColumnCount(4)
        self.word_table.setHorizontalHeaderLabels(["词", "编码", "权重", "手动"])
        self.word_table.setSortingEnabled(True)
        self.word_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 设置列宽
        self.word_table.setColumnWidth(0, 200)
        self.word_table.setColumnWidth(1, 150)
        self.word_table.setColumnWidth(2, 100)
        self.word_table.setColumnWidth(3, 80)
        
        # 添加右键菜单
        self.word_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.word_table.customContextMenuRequested.connect(self.show_word_context_menu)
        
        layout.addWidget(self.word_table)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_word)
        
        add_batch_button = QPushButton("批量添加")
        add_batch_button.clicked.connect(self.add_batch_words)
        
        edit_button = QPushButton("编辑")
        edit_button.clicked.connect(self.edit_word)
        
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self.delete_word)
        
        calc_all_codes_button = QPushButton("批量计算编码")
        calc_all_codes_button.clicked.connect(self.calculate_all_codes)
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_words)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(add_batch_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(calc_all_codes_button)
        button_layout.addWidget(refresh_button)
        layout.addLayout(button_layout)
        
        # 加载词表
        self.refresh_words()
    
    def create_stats_tab(self, parent):
        """创建统计分析标签页"""
        layout = QVBoxLayout(parent)
        
        # 基本统计
        stats_frame = QWidget()
        stats_layout = QHBoxLayout(stats_frame)
        
        self.total_words_label = QLabel("总词条数: 0")
        self.average_length_label = QLabel("平均词长: 0")
        self.conflict_count_label = QLabel("编码冲突数: 0")
        self.average_weight_label = QLabel("平均权重: 0")
        
        stats_layout.addWidget(self.total_words_label)
        stats_layout.addWidget(self.average_length_label)
        stats_layout.addWidget(self.conflict_count_label)
        stats_layout.addWidget(self.average_weight_label)
        
        layout.addWidget(stats_frame)
        
        # 统计设置
        stats_settings_frame = QWidget()
        stats_settings_layout = QHBoxLayout(stats_settings_frame)
        
        # 统计字段选择
        field_label = QLabel("统计字段:")
        self.stats_field_combo = QComboBox()
        self.stats_field_combo.addItems(["词长", "编码频次", "权重值"])
        self.stats_field_combo.setCurrentText("词长")
        
        # 显示条数设置
        count_label = QLabel("显示条数:")
        self.stats_count_edit = QLineEdit()
        self.stats_count_edit.setText("10")
        self.stats_count_edit.setFixedWidth(50)
        
        stats_settings_layout.addWidget(field_label)
        stats_settings_layout.addWidget(self.stats_field_combo)
        stats_settings_layout.addWidget(count_label)
        stats_settings_layout.addWidget(self.stats_count_edit)
        stats_settings_layout.addStretch()
        
        layout.addWidget(stats_settings_frame)
        
        # 高频词
        high_freq_frame = QWidget()
        high_freq_layout = QVBoxLayout(high_freq_frame)
        
        self.high_freq_label = QLabel("高频词前10名")
        self.high_freq_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        high_freq_layout.addWidget(self.high_freq_label)
        
        self.high_freq_table = QTableWidget()
        self.high_freq_table.setColumnCount(4)
        self.high_freq_table.setHorizontalHeaderLabels(["排名", "词", "编码", "权重"])
        self.high_freq_table.setSortingEnabled(True)
        
        # 设置列宽
        self.high_freq_table.setColumnWidth(0, 60)
        self.high_freq_table.setColumnWidth(1, 150)
        self.high_freq_table.setColumnWidth(2, 120)
        self.high_freq_table.setColumnWidth(3, 80)
        
        # 添加右键菜单
        self.high_freq_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.high_freq_table.customContextMenuRequested.connect(self.show_high_freq_context_menu)
        
        high_freq_layout.addWidget(self.high_freq_table)
        layout.addWidget(high_freq_frame)
        
        # 刷新按钮
        refresh_button = QPushButton("刷新统计")
        refresh_button.clicked.connect(self.refresh_stats)
        layout.addWidget(refresh_button)
        
        # 加载统计信息
        self.refresh_stats()
    
    def create_import_export_tab(self, parent):
        """创建导入导出标签页"""
        layout = QVBoxLayout(parent)
        
        # 导入部分
        import_frame = QWidget()
        import_layout = QFormLayout(import_frame)
        
        self.import_path_edit = QLineEdit()
        import_browse_button = QPushButton("浏览")
        import_browse_button.clicked.connect(lambda: self.browse_file(self.import_path_edit))
        
        self.import_format_combo = QComboBox()
        self.import_format_combo.addItems(["txt", "csv", "json"])
        
        import_button = QPushButton("导入")
        import_button.clicked.connect(self.import_file)
        
        import_layout.addRow("文件路径:", self.import_path_edit)
        import_layout.addRow("", import_browse_button)
        import_layout.addRow("格式:", self.import_format_combo)
        import_layout.addRow("", import_button)
        
        layout.addWidget(import_frame)
        
        # 导出部分
        export_frame = QWidget()
        export_layout = QFormLayout(export_frame)
        
        self.export_path_edit = QLineEdit()
        export_browse_button = QPushButton("浏览")
        export_browse_button.clicked.connect(lambda: self.browse_save_file(self.export_path_edit))
        
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["txt", "csv", "json"])
        
        export_button = QPushButton("导出")
        export_button.clicked.connect(self.export_file)
        
        export_layout.addRow("文件路径:", self.export_path_edit)
        export_layout.addRow("", export_browse_button)
        export_layout.addRow("格式:", self.export_format_combo)
        export_layout.addRow("", export_button)
        
        layout.addWidget(export_frame)
    
    def refresh_words(self):
        """刷新词表"""
        self.status_bar.showMessage("加载词表...")
        
        # 清空表格
        self.word_table.setRowCount(0)
        
        try:
            words = self.dict_service.get_all_words()
            # 只获取词表（is_character=False）
            multi_words = [word for word in words if not word["is_character"]]
            # 只显示前100条
            display_words = multi_words[:100]
            self.word_table.setRowCount(len(display_words))
            
            for i, word in enumerate(display_words):
                self.word_table.setItem(i, 0, QTableWidgetItem(word["word"]))
                self.word_table.setItem(i, 1, QTableWidgetItem(word["code"]))
                self.word_table.setItem(i, 2, QTableWidgetItem(str(word["weight"])))
                self.word_table.setItem(i, 3, QTableWidgetItem("是" if word["manual"] else "否"))
            
            self.status_bar.showMessage(f"加载完成，共 {len(multi_words)} 条词条，显示前100条")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载词表失败: {e}")
            self.status_bar.showMessage("加载失败")
    
    def search_words(self):
        """搜索词条"""
        keyword = self.search_edit.text()
        if not keyword:
            self.refresh_words()
            return
        
        # 获取选择的搜索字段
        field_map = {"词": "word", "编码": "code", "权重": "weight", "手动": "manual"}
        field = field_map.get(self.word_search_field.currentText(), "word")
        
        self.status_bar.showMessage(f"搜索 '{keyword}'...")
        
        # 清空表格
        self.word_table.setRowCount(0)
        
        try:
            results = self.dict_service.search_words(keyword, field)
            # 只获取多个字符的词条
            multi_words = [result for result in results if len(result["word"]) > 1]
            self.word_table.setRowCount(len(multi_words))
            
            for i, result in enumerate(multi_words):
                self.word_table.setItem(i, 0, QTableWidgetItem(result["word"]))
                self.word_table.setItem(i, 1, QTableWidgetItem(result["code"]))
                self.word_table.setItem(i, 2, QTableWidgetItem(str(result["weight"])))
                self.word_table.setItem(i, 3, QTableWidgetItem("是" if result["manual"] else "否"))
            
            self.status_bar.showMessage(f"搜索完成，找到 {len(multi_words)} 条结果")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {e}")
            self.status_bar.showMessage("搜索失败")
    
    def add_word(self):
        """添加词条"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加词条")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        word_edit = QLineEdit()
        code_edit = QLineEdit()
        weight_edit = QLineEdit()
        weight_edit.setText("1.0")
        
        form_layout.addRow("词:", word_edit)
        form_layout.addRow("编码:", code_edit)
        form_layout.addRow("权重:", weight_edit)
        
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        cancel_button = QPushButton("取消")
        
        def save_word():
            try:
                word = word_edit.text()
                code = code_edit.text()
                weight = float(weight_edit.text())
                
                # 如果没有输入编码，自动计算编码
                if not code:
                    code = self.dict_service.generate_code(word)
                    if code:
                        QMessageBox.information(self, "提示", f"自动计算编码为: {code}")
                    else:
                        QMessageBox.warning(self, "警告", "无法自动计算编码，请手动输入")
                        return
                
                self.dict_service.add_word(word, code, weight)
                QMessageBox.information(self, "成功", "词条添加成功")
                dialog.accept()
                self.refresh_words()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加失败: {e}")
        
        save_button.clicked.connect(save_word)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def edit_word(self):
        """编辑词条"""
        selected_row = self.word_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要编辑的词条")
            return
        
        word = self.word_table.item(selected_row, 0).text()
        code = self.word_table.item(selected_row, 1).text()
        weight = float(self.word_table.item(selected_row, 2).text())
        
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑词条")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        word_edit = QLineEdit(word)
        word_edit.setReadOnly(True)
        code_edit = QLineEdit(code)
        weight_edit = QLineEdit(str(weight))
        
        form_layout.addRow("词:", word_edit)
        form_layout.addRow("编码:", code_edit)
        form_layout.addRow("权重:", weight_edit)
        
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        cancel_button = QPushButton("取消")
        
        def save_edit():
            try:
                new_code = code_edit.text()
                new_weight = float(weight_edit.text())
                
                update_data = {}
                if new_code != code:
                    update_data["code"] = new_code
                if new_weight != weight:
                    update_data["weight"] = new_weight
                
                if update_data:
                    self.dict_service.update_word(word, **update_data)
                    QMessageBox.information(self, "成功", "词条更新成功")
                    dialog.accept()
                    self.refresh_words()
                else:
                    dialog.reject()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新失败: {e}")
        
        save_button.clicked.connect(save_edit)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def delete_word(self):
        """删除词条"""
        selected_row = self.word_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要删除的词条")
            return
        
        word = self.word_table.item(selected_row, 0).text()
        
        reply = QMessageBox.question(
            self, "确认", f"确定要删除词条 '{word}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                result = self.dict_service.delete_word(word)
                if result:
                    QMessageBox.information(self, "成功", "词条删除成功")
                    self.refresh_words()
                else:
                    QMessageBox.warning(self, "警告", "词条不存在")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
    
    def calculate_all_codes(self):
        """批量计算编码"""
        dialog = QDialog(self)
        dialog.setWindowTitle("批量计算编码")
        dialog.setGeometry(200, 200, 400, 250)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        rule_combo = QComboBox()
        
        # 加载自定义规则列表
        from app.core.config_manager import config_manager
        rules = config_manager.get("custom_rules", {})
        rule_names = list(rules.keys())
        if not rule_names:
            # 默认规则
            rules = {
                "默认规则": "v[2]=s[1][1]+s[1][2]+s[2][1]+s[2][2]\nv[3]=s[1][1]+s[2][1]+s[3][1]"
            }
            config_manager.set("custom_rules", rules)
            rule_names = list(rules.keys())
        
        rule_combo.addItems(rule_names)
        current_rule = config_manager.get("code_rule", rule_names[0] if rule_names else "")
        if current_rule in rule_names:
            rule_combo.setCurrentText(current_rule)
        
        separator_edit = QLineEdit()
        separator_edit.setPlaceholderText("编码分隔符")
        
        max_length_edit = QLineEdit()
        max_length_edit.setText("10")
        
        # 预览区域
        preview_group = QGroupBox("编码变化预览")
        preview_layout = QVBoxLayout()
        preview_text_edit = QTextEdit()
        preview_text_edit.setReadOnly(True)
        preview_text_edit.setFixedHeight(120)
        preview_layout.addWidget(preview_text_edit)
        preview_group.setLayout(preview_layout)
        
        # 进度条
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setVisible(False)
        
        form_layout.addRow("编码规则:", rule_combo)
        form_layout.addRow("分隔符:", separator_edit)
        form_layout.addRow("最大长度:", max_length_edit)
        form_layout.addRow(preview_group)
        form_layout.addRow(progress_bar)
        
        button_layout = QHBoxLayout()
        calculate_button = QPushButton("计算")
        cancel_button = QPushButton("取消")
        
        # 加载预览数据
        def load_preview():
            try:
                rule = rule_combo.currentText()
                separator = separator_edit.text()
                max_length = int(max_length_edit.text())
                
                # 设置编码生成配置
                config = {
                    'rule': 'custom',  # 始终使用custom规则
                    'separator': separator,
                    'max_length': max_length
                }
                self.dict_service.code_generator.set_config(config)
                
                # 保存当前选择的规则
                config_manager.set("code_rule", rule)
                
                # 获取预览数据
                preview_data = self.dict_service.get_code_preview()
                
                # 显示预览
                preview_text = ""
                for item in preview_data:
                    preview_text += f"{item['word']} {item['old_code']}-> {item['new_code']}\n"
                
                preview_text_edit.setText(preview_text)
            except Exception as e:
                preview_text_edit.setText(f"预览加载失败: {e}")
        
        # 初始加载预览
        load_preview()
        
        # 当规则或配置变化时重新加载预览
        rule_combo.currentTextChanged.connect(load_preview)
        separator_edit.textChanged.connect(load_preview)
        max_length_edit.textChanged.connect(load_preview)
        
        # 导入线程模块
        from PyQt6.QtCore import QThread, pyqtSignal
        
        class CalculateThread(QThread):
            progress_updated = pyqtSignal(int, str)
            finished = pyqtSignal(dict)
            error = pyqtSignal(str)
            
            def __init__(self, dict_service):
                super().__init__()
                self.dict_service = dict_service
            
            def run(self):
                try:
                    self.progress_updated.emit(0, "准备计算编码...")
                    
                    # 定义进度回调函数
                    def progress_callback(progress, message):
                        self.progress_updated.emit(progress, message)
                    
                    # 调用计算方法，传递进度回调
                    result = self.dict_service.calculate_all_codes(progress_callback)
                    
                    self.finished.emit(result)
                except Exception as e:
                    self.error.emit(str(e))
        
        def calculate():
            try:
                rule = rule_combo.currentText()
                separator = separator_edit.text()
                max_length = int(max_length_edit.text())
                
                # 设置编码生成配置
                config = {
                    'rule': 'custom',  # 始终使用custom规则
                    'separator': separator,
                    'max_length': max_length
                }
                self.dict_service.code_generator.set_config(config)
                
                # 保存当前选择的规则
                config_manager.set("code_rule", rule)
                
                # 显示进度条
                progress_bar.setVisible(True)
                calculate_button.setEnabled(False)
                
                # 创建并启动线程
                thread = CalculateThread(self.dict_service)
                
                def on_progress(progress, message):
                    progress_bar.setValue(progress)
                    dialog.setWindowTitle(f"计算编码 - {message}")
                
                def on_finished(result):
                    progress_bar.setVisible(False)
                    calculate_button.setEnabled(True)
                    dialog.setWindowTitle("批量计算编码")
                    
                    QMessageBox.information(
                        self, "成功", 
                        f"批量计算编码完成:\n" +
                        f"总词条数: {result['total']}\n" +
                        f"成功更新: {result['updated']}\n" +
                        f"更新失败: {result['failed']}"
                    )
                    
                    # 刷新词表
                    self.refresh_words()
                    dialog.accept()
                
                def on_error(error_msg):
                    progress_bar.setVisible(False)
                    calculate_button.setEnabled(True)
                    dialog.setWindowTitle("批量计算编码")
                    
                    QMessageBox.critical(self, "错误", f"批量计算编码失败: {error_msg}")
                
                thread.progress_updated.connect(on_progress)
                thread.finished.connect(on_finished)
                thread.error.connect(on_error)
                thread.start()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"批量计算编码失败: {e}")
        
        calculate_button.clicked.connect(calculate)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(calculate_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def refresh_stats(self):
        """刷新统计信息"""
        self.status_bar.showMessage("加载统计信息...")
        
        try:
            report = self.stats_service.generate_report()
            
            # 更新基本统计
            self.total_words_label.setText(f"总词条数: {report['word_length_stats']['total_words']}")
            self.average_length_label.setText(f"平均词长: {report['word_length_stats']['average_length']:.2f}")
            self.conflict_count_label.setText(f"编码冲突数: {report['code_stats']['conflict_count']}")
            self.average_weight_label.setText(f"平均权重: {report['weight_stats']['average_weight']:.2f}")
            
            # 获取统计设置
            stats_field = self.stats_field_combo.currentText()
            try:
                stats_count = int(self.stats_count_edit.text())
                if stats_count <= 0:
                    stats_count = 10
            except:
                stats_count = 10
            
            # 更新高频词标签
            self.high_freq_label.setText(f"按{stats_field}排序前{stats_count}名")
            
            # 获取并排序数据
            words = report.get('all_words', [])
            
            # 根据选择的字段排序
            if stats_field == "权重值":
                sorted_words = sorted(words, key=lambda x: x.get('weight', 0), reverse=True)
            elif stats_field == "词长":
                sorted_words = sorted(words, key=lambda x: len(x.get('word', '')), reverse=True)
            elif stats_field == "编码频次":
                # 获取编码统计信息
                code_stats = report.get('code_stats', {})
                code_frequency = code_stats.get('code_frequency', {})
                
                # 按编码频次排序，合并同一编码的词条
                code_groups = {}
                for word in words:
                    code = word.get('code', '')
                    if code not in code_groups:
                        code_groups[code] = {
                            'code': code,
                            'words': [],
                            'frequency': code_frequency.get(code, 0)
                        }
                    code_groups[code]['words'].append(word)
                
                # 按频次排序
                sorted_codes = sorted(code_groups.values(), key=lambda x: x['frequency'], reverse=True)
                
                # 准备显示数据
                display_data = []
                for code_info in sorted_codes[:stats_count]:
                    # 将同一编码的词合并显示
                    words_list = [w['word'] for w in code_info['words']]
                    words_str = '、'.join(words_list[:5])  # 只显示前5个词，避免过长
                    if len(words_list) > 5:
                        words_str += f"...等{len(words_list)}个词"
                    
                    display_data.append({
                        'word': words_str,
                        'code': code_info['code'],
                        'weight': code_info['frequency']  # 显示频次作为权重
                    })
                
                # 更新表格
                self.high_freq_table.setRowCount(0)
                
                for i, item in enumerate(display_data, 1):
                    self.high_freq_table.insertRow(i-1)
                    self.high_freq_table.setItem(i-1, 0, QTableWidgetItem(str(i)))
                    self.high_freq_table.setItem(i-1, 1, QTableWidgetItem(item['word']))
                    self.high_freq_table.setItem(i-1, 2, QTableWidgetItem(item['code']))
                    self.high_freq_table.setItem(i-1, 3, QTableWidgetItem(str(item['weight'])))
                
                # 跳过后续的表格更新
                self.status_bar.showMessage("统计信息加载完成")
                return
            else:
                sorted_words = sorted(words, key=lambda x: x.get('weight', 0), reverse=True)
            
            # 更新表格
            self.high_freq_table.setRowCount(0)
            
            for i, word in enumerate(sorted_words[:stats_count], 1):
                self.high_freq_table.insertRow(i-1)
                self.high_freq_table.setItem(i-1, 0, QTableWidgetItem(str(i)))
                self.high_freq_table.setItem(i-1, 1, QTableWidgetItem(word['word']))
                self.high_freq_table.setItem(i-1, 2, QTableWidgetItem(word['code']))
                self.high_freq_table.setItem(i-1, 3, QTableWidgetItem(str(word['weight'])))
            
            self.status_bar.showMessage("统计信息加载完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取统计信息失败: {e}")
            self.status_bar.showMessage("统计信息加载失败")
    
    def import_data(self):
        """导入数据"""
        # 尝试使用系统原生文件选择对话框
        try:
            # 创建文件对话框
            file_dialog = QFileDialog(self)
            file_dialog.setWindowTitle("选择导入文件")
            file_dialog.setNameFilters(["所有文件 (*.*)", "文本文件 (*.txt)", "CSV文件 (*.csv)", "JSON文件 (*.json)"])
            
            # 尝试使用原生对话框
            file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog, False)
            
            if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
                file_path = file_dialog.selectedFiles()[0]
            else:
                file_path = ""
        except Exception:
            # 如果原生对话框失败，使用Qt内置对话框
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择导入文件", "", "所有文件 (*.*);;文本文件 (*.txt);;CSV文件 (*.csv);;JSON文件 (*.json)"
            )
        
        if file_path:
            # 自动检测文件格式
            if file_path.endswith(".txt"):
                format = "txt"
            elif file_path.endswith(".csv"):
                format = "csv"
            elif file_path.endswith(".json"):
                format = "json"
            else:
                QMessageBox.critical(self, "错误", "不支持的文件格式")
                return
            
            self.import_path_edit.setText(file_path)
            self.import_format_combo.setCurrentText(format)
            self.import_file()
    
    def import_file(self):
        """导入文件"""
        file_path = self.import_path_edit.text()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择文件")
            return
        
        format = self.import_format_combo.currentText()
        
        # 创建进度对话框
        progress_dialog = QProgressDialog("开始导入...", "取消", 0, 100, self)
        progress_dialog.setWindowTitle("导入进度")
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        
        # 创建导入线程
        self.import_thread = ImportThread(self.filter_service, file_path, format)
        
        # 连接信号
        self.import_thread.progress.connect(lambda progress, message: self.on_import_progress(progress, message, progress_dialog))
        self.import_thread.finished.connect(lambda result: self.on_import_finished(result, progress_dialog))
        self.import_thread.error.connect(lambda error: self.on_import_error(error, progress_dialog))
        
        # 开始线程
        self.import_thread.start()
        
        # 显示进度对话框
        progress_dialog.exec()
    
    def on_import_progress(self, progress, message, progress_dialog):
        """导入进度回调"""
        progress_dialog.setValue(progress)
        progress_dialog.setLabelText(message)
    
    def on_import_finished(self, result, progress_dialog):
        """导入完成回调"""
        progress_dialog.accept()
        # 显示导入数据条数和用时
        total_time = result.get('total_time', 0)
        avg_time_per_1000 = result.get('avg_time_per_1000', 0)
        total_count = result.get('total_count', 0)
        
        message = f"导入成功: 添加了 {result['added']} 条，跳过了 {result['existing']} 条\n"
        message += f"总数据量: {total_count} 条\n"
        message += f"总耗时: {total_time:.2f} 秒\n"
        message += f"每千条平均耗时: {avg_time_per_1000:.2f} 秒"
        
        QMessageBox.information(
            self, "成功", message
        )
        self.refresh_words()
        self.status_bar.showMessage("导入完成")
    
    def on_import_error(self, error, progress_dialog):
        """导入错误回调"""
        progress_dialog.accept()
        QMessageBox.critical(self, "错误", f"导入失败: {error}")
        self.status_bar.showMessage("导入失败")
    
    def export_data(self):
        """导出数据"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择导出文件", "", "文本文件 (*.txt);;CSV文件 (*.csv);;JSON文件 (*.json)"
        )
        
        if file_path:
            # 自动检测文件格式
            if file_path.endswith(".txt"):
                format = "txt"
            elif file_path.endswith(".csv"):
                format = "csv"
            elif file_path.endswith(".json"):
                format = "json"
            else:
                QMessageBox.critical(self, "错误", "不支持的文件格式")
                return
            
            self.export_path_edit.setText(file_path)
            self.export_format_combo.setCurrentText(format)
            self.export_file()
    
    def export_file(self):
        """导出文件"""
        file_path = self.export_path_edit.text()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择文件")
            return
        
        format = self.export_format_combo.currentText()
        
        self.status_bar.showMessage(f"导出 {format} 文件...")
        
        try:
            if format == "txt":
                count = self.filter_service.export_to_txt(file_path)
            elif format == "csv":
                count = self.filter_service.export_to_csv(file_path)
            elif format == "json":
                count = self.filter_service.export_to_json(file_path)
            else:
                QMessageBox.critical(self, "错误", "不支持的格式")
                return
            
            QMessageBox.information(self, "成功", f"导出成功: 共导出 {count} 条数据")
            self.status_bar.showMessage("导出完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")
            self.status_bar.showMessage("导出失败")
    
    def refresh_chars(self):
        """刷新字表"""
        self.status_bar.showMessage("加载字表...")
        
        # 清空表格
        self.char_table.setRowCount(0)
        
        try:
            words = self.dict_service.get_all_words()
            # 只获取字表（is_character=True）
            chars = [word for word in words if word["is_character"]]
            # 只显示前100条
            display_chars = chars[:100]
            self.char_table.setRowCount(len(display_chars))
            
            for i, char in enumerate(display_chars):
                self.char_table.setItem(i, 0, QTableWidgetItem(char["word"]))
                self.char_table.setItem(i, 1, QTableWidgetItem(char["code"]))
                self.char_table.setItem(i, 2, QTableWidgetItem(str(char["weight"])))
                self.char_table.setItem(i, 3, QTableWidgetItem("是" if char["manual"] else "否"))
            
            self.status_bar.showMessage(f"加载完成，共 {len(chars)} 条汉字，显示前100条")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载字表失败: {e}")
            self.status_bar.showMessage("加载失败")
    
    def search_chars(self):
        """搜索汉字"""
        keyword = self.char_search_edit.text()
        if not keyword:
            self.refresh_chars()
            return
        
        # 获取选择的搜索字段
        field_map = {"字": "word", "编码": "code", "权重": "weight", "手动": "manual"}
        field = field_map.get(self.char_search_field.currentText(), "word")
        
        self.status_bar.showMessage(f"搜索 '{keyword}'...")
        
        # 清空表格
        self.char_table.setRowCount(0)
        
        try:
            results = self.dict_service.search_words(keyword, field)
            # 只获取单个字符的词条
            chars = [result for result in results if len(result["word"]) == 1]
            self.char_table.setRowCount(len(chars))
            
            for i, char in enumerate(chars):
                self.char_table.setItem(i, 0, QTableWidgetItem(char["word"]))
                self.char_table.setItem(i, 1, QTableWidgetItem(char["code"]))
                self.char_table.setItem(i, 2, QTableWidgetItem(str(char["weight"])))
                self.char_table.setItem(i, 3, QTableWidgetItem("是" if char["manual"] else "否"))
            
            self.status_bar.showMessage(f"搜索完成，找到 {len(chars)} 条结果")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败: {e}")
            self.status_bar.showMessage("搜索失败")
    
    def add_char(self):
        """添加汉字"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加汉字")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        char_edit = QLineEdit()
        char_edit.setPlaceholderText("请输入单个汉字")
        code_edit = QLineEdit()
        weight_edit = QLineEdit()
        weight_edit.setText("1.0")
        
        form_layout.addRow("字:", char_edit)
        form_layout.addRow("编码:", code_edit)
        form_layout.addRow("权重:", weight_edit)
        
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        cancel_button = QPushButton("取消")
        
        def save_char():
            try:
                char = char_edit.text().strip()
                if len(char) != 1:
                    QMessageBox.warning(self, "警告", "请输入单个汉字")
                    return
                
                code = code_edit.text()
                weight = float(weight_edit.text())
                
                # 如果没有输入编码，自动计算编码
                if not code:
                    code = self.dict_service.generate_code(char)
                    if code:
                        QMessageBox.information(self, "提示", f"自动计算编码为: {code}")
                    else:
                        QMessageBox.warning(self, "警告", "无法自动计算编码，请手动输入")
                        return
                
                self.dict_service.add_word(char, code, weight)
                QMessageBox.information(self, "成功", "汉字添加成功")
                dialog.accept()
                self.refresh_chars()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加失败: {e}")
        
        save_button.clicked.connect(save_char)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def edit_char(self):
        """编辑汉字"""
        selected_row = self.char_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要编辑的汉字")
            return
        
        char = self.char_table.item(selected_row, 0).text()
        code = self.char_table.item(selected_row, 1).text()
        weight = float(self.char_table.item(selected_row, 2).text())
        
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑汉字")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        char_edit = QLineEdit(char)
        char_edit.setReadOnly(True)
        code_edit = QLineEdit(code)
        weight_edit = QLineEdit(str(weight))
        
        form_layout.addRow("字:", char_edit)
        form_layout.addRow("编码:", code_edit)
        form_layout.addRow("权重:", weight_edit)
        
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        cancel_button = QPushButton("取消")
        
        def save_edit():
            try:
                new_code = code_edit.text()
                new_weight = float(weight_edit.text())
                
                update_data = {}
                if new_code != code:
                    update_data["code"] = new_code
                if new_weight != weight:
                    update_data["weight"] = new_weight
                
                if update_data:
                    self.dict_service.update_word(char, **update_data)
                    QMessageBox.information(self, "成功", "汉字更新成功")
                    dialog.accept()
                    self.refresh_chars()
                else:
                    dialog.reject()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新失败: {e}")
        
        save_button.clicked.connect(save_edit)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def delete_char(self):
        """删除汉字"""
        selected_row = self.char_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请选择要删除的汉字")
            return
        
        char = self.char_table.item(selected_row, 0).text()
        
        reply = QMessageBox.question(
            self, "确认", f"确定要删除汉字 '{char}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                result = self.dict_service.delete_word(char)
                if result:
                    QMessageBox.information(self, "成功", "汉字删除成功")
                    self.refresh_chars()
                else:
                    QMessageBox.warning(self, "警告", "汉字不存在")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
    
    def create_settings_tab(self, parent):
        """创建设置标签页"""
        layout = QHBoxLayout(parent)
        
        # 创建分割器
        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Horizontal)
        
        # 左侧设置类型列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        settings_types = QTreeWidget()
        settings_types.setHeaderLabel("设置类型")
        
        # 添加设置类型（直接添加所有设置项，不需要子目录）
        QTreeWidgetItem(settings_types, ["主题设置"])
        QTreeWidgetItem(settings_types, ["语言设置"])
        QTreeWidgetItem(settings_types, ["编码规则"])
        QTreeWidgetItem(settings_types, ["编码长度"])
        QTreeWidgetItem(settings_types, ["数据库路径"])
        QTreeWidgetItem(settings_types, ["缓存设置"])
        QTreeWidgetItem(settings_types, ["删除表"])
        QTreeWidgetItem(settings_types, ["导出格式"])
        QTreeWidgetItem(settings_types, ["导出路径"])
        
        left_layout.addWidget(settings_types)
        splitter.addWidget(left_widget)
        
        # 右侧设置内容
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 设置标题
        self.settings_title = QLabel("选择设置类型")
        self.settings_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        right_layout.addWidget(self.settings_title)
        
        # 设置内容区域
        self.settings_content = QWidget()
        self.settings_content_layout = QFormLayout(self.settings_content)
        right_layout.addWidget(self.settings_content)
        
        # 保存按钮
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.save_settings)
        right_layout.addWidget(save_button)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器大小
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter)
        
        # 连接信号
        settings_types.itemClicked.connect(self.on_settings_type_clicked)
    
    def on_settings_type_clicked(self, tree_item, column):
        """设置类型点击事件"""
        # 清空设置内容
        for i in reversed(range(self.settings_content_layout.count())):
            item = self.settings_content_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                else:
                    # 处理布局项
                    layout = item.layout()
                    if layout:
                        # 清空布局中的所有控件
                        for j in reversed(range(layout.count())):
                            layout_item = layout.itemAt(j)
                            if layout_item:
                                layout_widget = layout_item.widget()
                                if layout_widget:
                                    layout_widget.deleteLater()
                        # 移除布局
                        self.settings_content_layout.removeItem(item)
        
        # 获取选中的设置类型
        settings_type = tree_item.text(column)
        
        # 更新标题
        self.settings_title.setText(settings_type)
        
        # 根据选中的设置类型显示对应的设置内容
        if settings_type == "主题设置":
            # 主题设置
            theme_label = QLabel("主题:")
            theme_combo = QComboBox()
            theme_combo.addItems(["经典", "Material3"])
            
            # 模式设置
            mode_label = QLabel("模式:")
            mode_combo = QComboBox()
            mode_combo.addItems(["跟随系统", "浅色", "深色"])
            
            # 主题颜色设置（仅对Material3有效）
            color_label = QLabel("主题颜色:")
            color_combo = QComboBox()
            color_combo.addItems(["蓝色", "绿色", "红色", "紫色", "橙色"])
            
            # 加载当前设置
            current_theme = config_manager.get("theme_name", "经典")
            current_mode = config_manager.get("theme_mode", "auto")
            current_color = config_manager.get("theme_color", "蓝色")
            
            theme_combo.setCurrentText(current_theme)
            
            # 映射内部模式值到显示名称
            mode_map = {
                "auto": "跟随系统",
                "light": "浅色",
                "dark": "深色"
            }
            display_mode = mode_map.get(current_mode, "跟随系统")
            mode_combo.setCurrentText(display_mode)
            
            color_combo.setCurrentText(current_color)
            
            # 连接信号
            def on_theme_changed():
                theme = theme_combo.currentText()
                mode = mode_combo.currentText()
                color = color_combo.currentText()
                
                # 映射模式显示名称到内部值
                mode_map_reverse = {
                    "跟随系统": "auto",
                    "浅色": "light",
                    "深色": "dark"
                }
                internal_mode = mode_map_reverse.get(mode, "auto")
                
                # 保存设置
                config_manager.set("theme_name", theme)
                config_manager.set("theme_mode", internal_mode)
                config_manager.set("theme_color", color)
                
                # 应用主题
                self.set_theme(internal_mode, theme, color)
                self.show_toast(f"主题已更改为: {theme} - {mode} - {color}")
            
            theme_combo.currentTextChanged.connect(on_theme_changed)
            mode_combo.currentTextChanged.connect(on_theme_changed)
            color_combo.currentTextChanged.connect(on_theme_changed)
            
            self.settings_content_layout.addRow(theme_label, theme_combo)
            self.settings_content_layout.addRow(mode_label, mode_combo)
            self.settings_content_layout.addRow(color_label, color_combo)
        elif settings_type == "语言设置":
            # 语言设置
            language_label = QLabel("语言:")
            language_combo = QComboBox()
            language_combo.addItems(["中文", "English"])
            language_combo.setCurrentText(config_manager.get("language", "中文"))
            # 连接信号，自动保存
            language_combo.currentTextChanged.connect(lambda text: config_manager.set("language", text))
            self.settings_content_layout.addRow(language_label, language_combo)
        elif settings_type == "编码规则":
            # 编码规则设置
            rule_label = QLabel("编码规则:")
            rule_combo = QComboBox()
            
            # 加载自定义规则列表
            rules = config_manager.get("custom_rules", {})
            # 检查规则格式是否为新格式（包含content和python_mode字段）
            # 如果是旧格式，转换为新格式
            new_rules = {}
            for rule_name, rule_value in rules.items():
                if isinstance(rule_value, str):
                    # 旧格式，转换为新格式
                    new_rules[rule_name] = {
                        "content": rule_value,
                        "python_mode": False
                    }
                else:
                    # 新格式，直接使用
                    new_rules[rule_name] = rule_value
            rules = new_rules
            config_manager.set("custom_rules", rules)
            rule_names = list(rules.keys())
            if not rule_names:
                # 默认规则
                rules = {
                    "默认规则": {
                        "content": "v[2]=s[1][1]+s[1][2]+s[2][1]+s[2][2]\nv[3]=s[1][1]+s[2][1]+s[3][1]",
                        "python_mode": False
                    }
                }
                config_manager.set("custom_rules", rules)
                rule_names = list(rules.keys())
            
            # 自定义编码规则设置
            custom_rule_group = QGroupBox("自定义编码规则")
            custom_rule_layout = QVBoxLayout()
            
            # 规则名称
            rule_name_layout = QHBoxLayout()
            rule_name_label = QLabel("规则名称:")
            rule_name_edit = QLineEdit()
            rule_name_layout.addWidget(rule_name_label)
            rule_name_layout.addWidget(rule_name_edit)
            custom_rule_layout.addLayout(rule_name_layout)
            
            # Python模式勾选框
            python_mode_layout = QHBoxLayout()
            python_mode_checkbox = QCheckBox("开启Python模式")
            python_mode_layout.addWidget(python_mode_checkbox)
            custom_rule_layout.addLayout(python_mode_layout)
            
            # 规则内容
            rule_content_layout = QVBoxLayout()
            rule_content_label = QLabel("规则内容:")
            rule_content_edit = QTextEdit()
            rule_content_layout.addWidget(rule_content_label)
            rule_content_layout.addWidget(rule_content_edit)
            custom_rule_layout.addLayout(rule_content_layout)
            
            # 为默认规则添加标识
            default_rule = config_manager.get("default_code_rule", "")
            for name in rule_names:
                if name == default_rule:
                    rule_combo.addItem(f"{name} [默认]")
                else:
                    rule_combo.addItem(name)
            
            current_rule = config_manager.get("code_rule", rule_names[0] if rule_names else "")
            if current_rule in rule_names:
                # 检查是否为默认规则和Python模式
                display_name = current_rule
                if rules[current_rule].get("python_mode", False):
                    display_name += " *python"
                if current_rule == default_rule:
                    display_name += " [默认]"
                rule_combo.setCurrentText(display_name)
                # 初始化显示当前规则内容和Python模式状态
                rule_name_edit.setText(current_rule)
                rule_content_edit.setPlainText(rules.get(current_rule, {}).get("content", ""))
                python_mode_checkbox.setChecked(rules.get(current_rule, {}).get("python_mode", False))
            # 连接信号，自动保存
            def on_rule_changed(text):
                # 移除默认标识和Python模式标识
                if " [默认]" in text:
                    rule_name = text.replace(" [默认]", "")
                else:
                    rule_name = text
                if " *python" in rule_name:
                    rule_name = rule_name.replace(" *python", "")
                config_manager.set("code_rule", rule_name)
                # 切换规则时，自动填充规则名称、内容和Python模式状态
                rule_name_edit.setText(rule_name)
                rule_content_edit.setPlainText(rules.get(rule_name, {}).get("content", ""))
                python_mode_checkbox.setChecked(rules.get(rule_name, {}).get("python_mode", False))
            
            rule_combo.currentTextChanged.connect(on_rule_changed)
            self.settings_content_layout.addRow(rule_label, rule_combo)
            
            # 语法说明
            syntax_layout = QHBoxLayout()
            syntax_label = QLabel("语法说明:")
            syntax_button = QPushButton("?")
            syntax_button.setFixedSize(20, 20)
            syntax_button.setStyleSheet("QPushButton { border-radius: 10px; background-color: #4CAF50; color: white; }")
            
            def show_syntax_help():
                help_text = """编码规则语法说明：

普通模式：
v[n] = 表达式 表示词长度为n时的编码规则

v[n+] = 表达式 表示词长度为n及以上时的编码规则（如v[4+]表示四个字及以上的词）

s[i][j] 表示第i个字的第j个编码字符（1-based索引，从1开始）

s[-1][j] 表示词的最后一个字的第j个编码字符

+ 表示连接字符串

Python模式：
开启Python模式后，可以使用Python代码来生成编码

默认变量：
- vac：单条词条
- code['字']：表示字的编码（例如code['测']表示"测"字的编码）
- result：用于存储生成的编码

默认编码规则：
在规则名称后添加 [default] 后缀，表示该规则为默认编码规则，用于加词时自动计算编码

Python模式标识：
在规则名称后添加 *python 后缀，表示该规则启用了Python模式

普通模式示例：
v[2] = s[1][1] + s[1][2] + s[2][1] + s[2][2]
表示词长度为2时，取前两个字的前两个编码

v[3] = s[1][1] + s[2][1] + s[3][1]
表示词长度为3时，取前三个字的每个字第一个编码

v[4+] = s[1][1] + s[2][1] + s[3][1] + s[4][1]
表示词长度为4及以上时，取前四个字的每个字第一个编码

v[2] = s[1][1] + s[-1][1]
表示词长度为2时，取第一个字和最后一个字的第一个编码

Python模式示例：
# 取每个字的第一个编码
result = ''
for char in vac:
    if char in code:
        result += code[char][0]

# 取第一个字和最后一个字的编码
if len(vac) >= 2:
    result = code[vac[0]] + code[vac[-1]]
else:
    result = code.get(vac[0], '')

# 自定义复杂逻辑
if len(vac) == 2:
    result = code[vac[0]][:2] + code[vac[1]][:2]
elif len(vac) == 3:
    result = code[vac[0]][0] + code[vac[1]][0] + code[vac[2]][:2]
elif len(vac) >= 4:
    result = code[vac[0]][0] + code[vac[1]][0] + code[vac[2]][0] + code[vac[3]][0]"""
                QMessageBox.information(self, "语法说明", help_text)
            
            syntax_button.clicked.connect(show_syntax_help)
            syntax_layout.addWidget(syntax_label)
            syntax_layout.addWidget(syntax_button)
            custom_rule_layout.addLayout(syntax_layout)
            
            # 添加、删除和设为默认按钮
            button_layout = QHBoxLayout()
            add_button = QPushButton("添加规则")
            delete_button = QPushButton("删除规则")
            set_default_button = QPushButton("设为默认")
            
            def add_rule():
                rule_name = rule_name_edit.text().strip()
                rule_content = rule_content_edit.toPlainText().strip()
                python_mode = python_mode_checkbox.isChecked()
                
                if rule_name and rule_content:
                    rules = config_manager.get("custom_rules", {})
                    # 保存规则内容和Python模式状态
                    rules[rule_name] = {
                        "content": rule_content,
                        "python_mode": python_mode
                    }
                    config_manager.set("custom_rules", rules)
                    # 更新下拉框
                    rule_combo.clear()
                    rule_names = list(rules.keys())
                    # 为默认规则和Python模式添加标识
                    default_rule = config_manager.get("default_code_rule", "")
                    for name in rule_names:
                        display_name = name
                        if rules[name].get("python_mode", False):
                            display_name += " *python"
                        if name == default_rule:
                            display_name += " [默认]"
                        rule_combo.addItem(display_name)
                    # 设置当前规则的显示名称
                    current_display_name = rule_name
                    if python_mode:
                        current_display_name += " *python"
                    rule_combo.setCurrentText(current_display_name)
                    self.show_toast(f"规则 '{rule_name}' 添加成功")
                else:
                    self.show_toast("请输入规则名称和内容")
            
            def delete_rule():
                current_rule = rule_combo.currentText()
                # 移除默认标识和Python模式标识
                if " [默认]" in current_rule:
                    current_rule = current_rule.replace(" [默认]", "")
                if " *python" in current_rule:
                    current_rule = current_rule.replace(" *python", "")
                
                if current_rule:
                    rules = config_manager.get("custom_rules", {})
                    if current_rule in rules:
                        # 如果删除的是默认规则，清除默认规则设置
                        if current_rule == config_manager.get("default_code_rule", ""):
                            config_manager.set("default_code_rule", "")
                        
                        del rules[current_rule]
                        config_manager.set("custom_rules", rules)
                        # 更新下拉框
                        rule_combo.clear()
                        rule_names = list(rules.keys())
                        # 为默认规则和Python模式添加标识
                        default_rule = config_manager.get("default_code_rule", "")
                        for name in rule_names:
                            display_name = name
                            if rules[name].get("python_mode", False):
                                display_name += " *python"
                            if name == default_rule:
                                display_name += " [默认]"
                            rule_combo.addItem(display_name)
                        if rule_names:
                            rule_combo.setCurrentIndex(0)
                            config_manager.set("code_rule", rule_names[0])
                            # 更新规则编辑框
                            rule_name_edit.setText(rule_names[0])
                            rule_content_edit.setPlainText(rules.get(rule_names[0], {}).get("content", ""))
                            # 更新Python模式勾选框
                            python_mode_checkbox.setChecked(rules.get(rule_names[0], {}).get("python_mode", False))
                        else:
                            config_manager.set("code_rule", "")
                            # 清空规则编辑框
                            rule_name_edit.setText("")
                            rule_content_edit.setPlainText("")
                            python_mode_checkbox.setChecked(False)
                        self.show_toast(f"规则 '{current_rule}' 删除成功")
            
            def set_default():
                current_rule = rule_combo.currentText()
                # 移除默认标识和Python模式标识
                if " [默认]" in current_rule:
                    current_rule = current_rule.replace(" [默认]", "")
                if " *python" in current_rule:
                    current_rule = current_rule.replace(" *python", "")
                
                if current_rule:
                    # 设置默认规则
                    config_manager.set("default_code_rule", current_rule)
                    # 更新下拉框，为默认规则和Python模式添加标识
                    rules = config_manager.get("custom_rules", {})
                    rule_names = list(rules.keys())
                    rule_combo.clear()
                    for name in rule_names:
                        display_name = name
                        if rules[name].get("python_mode", False):
                            display_name += " *python"
                        if name == current_rule:
                            display_name += " [默认]"
                        rule_combo.addItem(display_name)
                    # 设置当前规则的显示名称
                    current_display_name = current_rule
                    if rules.get(current_rule, {}).get("python_mode", False):
                        current_display_name += " *python"
                    current_display_name += " [默认]"
                    rule_combo.setCurrentText(current_display_name)
                    self.show_toast(f"规则 '{current_rule}' 已设为默认")
            
            add_button.clicked.connect(add_rule)
            delete_button.clicked.connect(delete_rule)
            set_default_button.clicked.connect(set_default)
            button_layout.addWidget(add_button)
            button_layout.addWidget(delete_button)
            button_layout.addWidget(set_default_button)
            custom_rule_layout.addLayout(button_layout)
            
            custom_rule_group.setLayout(custom_rule_layout)
            self.settings_content_layout.addRow(custom_rule_group)
        elif settings_type == "编码长度":
            # 编码长度设置
            length_label = QLabel("最大编码长度:")
            length_spin = QLineEdit()
            length_spin.setText(config_manager.get("max_code_length", "10"))
            # 连接信号，自动保存
            length_spin.textChanged.connect(lambda text: config_manager.set("max_code_length", text))
            self.settings_content_layout.addRow(length_label, length_spin)
        elif settings_type == "数据库路径":
            # 数据库路径设置
            path_label = QLabel("数据库路径:")
            path_edit = QLineEdit()
            path_edit.setText(config_manager.get("database_path", "./vmtool.db"))
            # 连接信号，自动保存
            path_edit.textChanged.connect(lambda text: config_manager.set("database_path", text))
            browse_button = QPushButton("浏览")
            # 连接浏览按钮点击事件
            def browse_database_path():
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "选择数据库文件", "", "SQLite数据库文件 (*.db)"
                )
                if file_path:
                    path_edit.setText(file_path)
                    config_manager.set("database_path", file_path)
            browse_button.clicked.connect(browse_database_path)
            browse_layout = QHBoxLayout()
            browse_layout.addWidget(path_edit)
            browse_layout.addWidget(browse_button)
            self.settings_content_layout.addRow(path_label, browse_layout)
        elif settings_type == "缓存设置":
            # 缓存设置
            cache_label = QLabel("缓存大小 (MB):")
            cache_spin = QLineEdit()
            cache_spin.setText(config_manager.get("cache_size", "100"))
            # 连接信号，自动保存
            cache_spin.textChanged.connect(lambda text: config_manager.set("cache_size", text))
            self.settings_content_layout.addRow(cache_label, cache_spin)
        elif settings_type == "导出格式":
            # 导出格式设置
            format_label = QLabel("默认导出格式:")
            format_combo = QComboBox()
            format_combo.addItems(["txt", "csv", "json"])
            format_combo.setCurrentText(config_manager.get("default_export_format", "txt"))
            # 连接信号，自动保存
            format_combo.currentTextChanged.connect(lambda text: config_manager.set("default_export_format", text))
            self.settings_content_layout.addRow(format_label, format_combo)
        elif settings_type == "导出路径":
            # 导出路径设置
            export_path_label = QLabel("默认导出路径:")
            export_path_edit = QLineEdit()
            export_path_edit.setText(config_manager.get("default_export_path", "./"))
            # 连接信号，自动保存
            export_path_edit.textChanged.connect(lambda text: config_manager.set("default_export_path", text))
            export_browse_button = QPushButton("浏览")
            # 连接浏览按钮点击事件
            def browse_export_path():
                directory = QFileDialog.getExistingDirectory(
                    self, "选择导出目录", "./"
                )
                if directory:
                    export_path_edit.setText(directory)
                    config_manager.set("default_export_path", directory)
            export_browse_button.clicked.connect(browse_export_path)
            export_browse_layout = QHBoxLayout()
            export_browse_layout.addWidget(export_path_edit)
            export_browse_layout.addWidget(export_browse_button)
            self.settings_content_layout.addRow(export_path_label, export_browse_layout)
        elif settings_type == "删除表":
            # 删除表设置
            delete_table_label = QLabel("删除表:")
            delete_table_combo = QComboBox()
            delete_table_combo.addItems(["字表", "词表", "全部表"])
            self.settings_content_layout.addRow(delete_table_label, delete_table_combo)
            
            # 添加删除按钮
            delete_button = QPushButton("删除表")
            delete_button.clicked.connect(lambda: self.delete_table(delete_table_combo.currentText()))
            self.settings_content_layout.addRow(delete_button)
    
    def save_settings(self):
        """保存设置"""
        # 这里可以实现保存设置的逻辑
        self.show_toast("设置保存成功")
    
    def show_toast(self, message, duration=2000):
        """显示toast消息
        
        Args:
            message: 消息内容
            duration: 显示时长（毫秒）
        """
        toast = QWidget(self)
        toast.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        toast.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
            }
        """)
        
        label = QLabel(message, toast)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout = QVBoxLayout(toast)
        layout.addWidget(label)
        
        # 计算位置（屏幕中央）
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        toast_geometry = toast.sizeHint()
        x = (screen_geometry.width() - toast_geometry.width()) // 2
        y = (screen_geometry.height() - toast_geometry.height()) // 2
        toast.move(x, y)
        
        toast.show()
        
        # 设置定时器，自动关闭
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(duration, toast.close)
    
    def on_theme_changed(self, theme):
        """主题变更事件"""
        # 映射主题名称到内部值
        theme_map = {
            "跟随系统": "auto",
            "浅色": "light",
            "深色": "dark"
        }
        internal_theme = theme_map.get(theme, "auto")
        config_manager.set("theme", internal_theme)
        self.set_theme(internal_theme)
        self.show_toast(f"主题已更改为: {theme}")
    
    def delete_table(self, table_type):
        """删除表"""
        # 显示确认对话框
        reply = QMessageBox.question(
            self, "确认", f"确定要删除{table_type}吗？此操作将永久删除所有数据，不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 导入数据库初始化模块
                from app.dal.init_db import engine, Base
                from app.dal.models import Word
                
                # 删除表
                if table_type == "字表":
                    # 删除所有单个字符的词条
                    from sqlalchemy.orm import Session
                    from app.dal.database import SessionLocal
                    db = SessionLocal()
                    try:
                        db.query(Word).filter(Word.is_character == True).delete()
                        db.commit()
                    finally:
                        db.close()
                elif table_type == "词表":
                    # 删除所有多个字符的词条
                    from sqlalchemy.orm import Session
                    from app.dal.database import SessionLocal
                    db = SessionLocal()
                    try:
                        db.query(Word).filter(Word.is_character == False).delete()
                        db.commit()
                    finally:
                        db.close()
                elif table_type == "全部表":
                    # 删除所有表
                    Base.metadata.drop_all(bind=engine)
                    # 重新创建表
                    Base.metadata.create_all(bind=engine)
                    # 重新初始化配置
                    from app.dal.init_db import init_database
                    init_database()
                
                # 刷新表格
                self.refresh_chars()
                self.refresh_words()
                
                QMessageBox.information(self, "成功", f"{table_type}删除成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除表失败: {e}")
    
    def add_batch_chars(self):
        """批量添加汉字"""
        dialog = QDialog(self)
        dialog.setWindowTitle("批量添加汉字")
        dialog.setGeometry(200, 200, 500, 300)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("请输入要添加的汉字，每个汉字占一行:")
        layout.addWidget(label)
        
        text_edit = QTextEdit()
        layout.addWidget(text_edit)
        
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        cancel_button = QPushButton("取消")
        
        def add_chars():
            text = text_edit.toPlainText()
            chars = [char.strip() for char in text.split('\n') if char.strip()]
            
            if not chars:
                QMessageBox.warning(self, "警告", "请输入要添加的汉字")
                return
            
            # 验证输入是否都是单个汉字
            for char in chars:
                if len(char) != 1:
                    QMessageBox.warning(self, "警告", f"'{char}' 不是单个汉字，请检查输入")
                    return
            
            # 创建进度对话框
            progress_dialog = QProgressDialog("开始批量添加...", "取消", 0, 100, self)
            progress_dialog.setWindowTitle("添加进度")
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            
            # 创建批量添加线程
            self.add_batch_thread = AddBatchThread(self.dict_service, chars, is_character=True)
            
            # 连接信号
            self.add_batch_thread.progress.connect(lambda progress, message: self.on_add_batch_progress(progress, message, progress_dialog))
            self.add_batch_thread.finished.connect(lambda result: self.on_add_batch_finished(result, progress_dialog, "汉字"))
            self.add_batch_thread.error.connect(lambda error: self.on_add_batch_error(error, progress_dialog))
            
            # 开始线程
            self.add_batch_thread.start()
            
            # 显示进度对话框
            progress_dialog.exec()
            
            dialog.accept()
        
        add_button.clicked.connect(add_chars)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def add_batch_words(self):
        """批量添加词条"""
        dialog = QDialog(self)
        dialog.setWindowTitle("批量添加词条")
        dialog.setGeometry(200, 200, 500, 300)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("请输入要添加的词条，每个词条占一行:")
        layout.addWidget(label)
        
        text_edit = QTextEdit()
        layout.addWidget(text_edit)
        
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        cancel_button = QPushButton("取消")
        
        def add_words():
            text = text_edit.toPlainText()
            words = [word.strip() for word in text.split('\n') if word.strip()]
            
            if not words:
                QMessageBox.warning(self, "警告", "请输入要添加的词条")
                return
            
            # 创建进度对话框
            progress_dialog = QProgressDialog("开始批量添加...", "取消", 0, 100, self)
            progress_dialog.setWindowTitle("添加进度")
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            
            # 创建批量添加线程
            self.add_batch_thread = AddBatchThread(self.dict_service, words, is_character=False)
            
            # 连接信号
            self.add_batch_thread.progress.connect(lambda progress, message: self.on_add_batch_progress(progress, message, progress_dialog))
            self.add_batch_thread.finished.connect(lambda result: self.on_add_batch_finished(result, progress_dialog, "词条"))
            self.add_batch_thread.error.connect(lambda error: self.on_add_batch_error(error, progress_dialog))
            
            # 开始线程
            self.add_batch_thread.start()
            
            # 显示进度对话框
            progress_dialog.exec()
            
            dialog.accept()
        
        add_button.clicked.connect(add_words)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def on_add_batch_progress(self, progress, message, progress_dialog):
        """批量添加进度回调"""
        progress_dialog.setValue(progress)
        progress_dialog.setLabelText(message)
    
    def on_add_batch_finished(self, result, progress_dialog, item_type):
        """批量添加完成回调"""
        progress_dialog.accept()
        QMessageBox.information(
            self, "成功", f"批量添加{item_type}完成: 添加了 {result['added']} 个，跳过了 {result['existing']} 个"
        )
        if item_type == "汉字":
            self.refresh_chars()
        else:
            self.refresh_words()
        self.status_bar.showMessage(f"批量添加{item_type}完成")
    
    def on_add_batch_error(self, error, progress_dialog):
        """批量添加错误回调"""
        progress_dialog.accept()
        QMessageBox.critical(self, "错误", f"批量添加失败: {error}")
        self.status_bar.showMessage("批量添加失败")
    
    def browse_file(self, edit):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "所有文件 (*.*)"
        )
        if file_path:
            edit.setText(file_path)
    
    def browse_save_file(self, edit):
        """浏览保存文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择保存文件", "", "文本文件 (*.txt);;CSV文件 (*.csv);;JSON文件 (*.json)"
        )
        if file_path:
            edit.setText(file_path)
    
    def calculate_weight(self):
        """计算权重"""
        reply = QMessageBox.question(
            self, "确认", "确定要重新计算所有词条的权重吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.status_bar.showMessage("计算权重...")
            try:
                # 这里需要实现批量计算权重的逻辑
                QMessageBox.information(self, "成功", "权重计算完成")
                self.refresh_words()
                self.refresh_stats()
                self.status_bar.showMessage("权重计算完成")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"计算失败: {e}")
                self.status_bar.showMessage("计算失败")
    
    def detect_conflicts(self):
        """检测编码冲突"""
        self.status_bar.showMessage("检测编码冲突...")
        
        try:
            conflicts = self.stats_service.detect_code_conflicts()
            
            if conflicts:
                # 创建冲突窗口
                conflict_window = QDialog(self)
                conflict_window.setWindowTitle("编码冲突")
                conflict_window.setGeometry(200, 200, 600, 400)
                
                layout = QVBoxLayout(conflict_window)
                
                tree = QTreeWidget()
                tree.setHeaderLabels(["编码", "冲突数量", "词条"])
                
                for conflict in conflicts:
                    parent = QTreeWidgetItem([conflict['code'], str(conflict['count']), ""])
                    for word in conflict['words']:
                        child = QTreeWidgetItem(["", "", word['word']])
                        parent.addChild(child)
                    tree.addTopLevelItem(parent)
                
                layout.addWidget(tree)
                
                close_button = QPushButton("关闭")
                close_button.clicked.connect(conflict_window.accept)
                layout.addWidget(close_button)
                
                conflict_window.exec()
            else:
                QMessageBox.information(self, "信息", "未发现编码冲突")
            
            self.status_bar.showMessage("编码冲突检测完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"检测失败: {e}")
            self.status_bar.showMessage("检测失败")
    
    def migrate_data(self):
        """数据迁移"""
        reply = QMessageBox.question(
            self, "确认", "确定要执行数据迁移吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.status_bar.showMessage("执行数据迁移...")
            try:
                from app.dal.migration import full_migration
                result = full_migration()
                QMessageBox.information(self, "成功", f"数据迁移完成: {result}")
                self.refresh_words()
                self.refresh_stats()
                self.status_bar.showMessage("数据迁移完成")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"迁移失败: {e}")
                self.status_bar.showMessage("迁移失败")
    
    def show_about(self):
        """显示关于信息"""
        QMessageBox.about(
            self, "关于", "VM-TOOL v2.0.0\n现代化码表处理工具\n\n支持词表管理、权重计算、数据导入导出等功能"
        )
    
    def load_config(self):
        """加载配置"""
        # 加载窗口大小
        window_size = config_manager.get("window_size", [1000, 700])
        self.resize(window_size[0], window_size[1])
        
        # 加载窗口位置
        window_position = config_manager.get("window_position", [100, 100])
        self.move(window_position[0], window_position[1])
    
    def save_config(self):
        """保存配置"""
        # 保存窗口大小
        config_manager.set("window_size", [self.width(), self.height()])
        
        # 保存窗口位置
        config_manager.set("window_position", [self.x(), self.y()])
    
    def set_theme(self, theme_mode, theme_name="经典", theme_color="蓝色"):
        """设置主题
        
        Args:
            theme_mode: 主题模式 (auto, light, dark)
            theme_name: 主题名称 (经典, Material3)
            theme_color: 主题颜色 (蓝色, 绿色, 红色, 紫色, 橙色)
        """
        from PyQt6.QtCore import Qt
        
        # 获取应用实例
        app = QApplication.instance()
        
        if theme_mode == "auto":
            # 跟随系统主题
            is_dark = self._detect_system_theme()
            if is_dark:
                if theme_name == "Material3":
                    self._set_material3_dark_theme(theme_color)
                else:
                    self._set_dark_theme()
            else:
                if theme_name == "Material3":
                    self._set_material3_light_theme(theme_color)
                else:
                    self._set_light_theme()
        elif theme_mode == "dark":
            # 深色主题
            if theme_name == "Material3":
                self._set_material3_dark_theme(theme_color)
            else:
                self._set_dark_theme()
        else:
            # 浅色主题
            if theme_name == "Material3":
                self._set_material3_light_theme(theme_color)
            else:
                self._set_light_theme()
    
    def _detect_system_theme(self):
        """检测系统主题"""
        import os
        from PyQt6.QtCore import Qt
        
        # 获取应用实例
        app = QApplication.instance()
        
        # 方法1: 使用Qt的内置方法
        try:
            if app.styleHints().colorScheme() == Qt.ColorScheme.Dark:
                return True
        except Exception:
            pass
        
        # 方法2: 检查环境变量
        # 检查GNOME环境变量
        if os.environ.get("GTK_THEME") and "dark" in os.environ.get("GTK_THEME", "").lower():
            return True
        if os.environ.get("GNOME_THEME" ) and "dark" in os.environ.get("GNOME_THEME", "").lower():
            return True
        
        # 检查XDG环境变量
        if os.environ.get("XDG_CURRENT_DESKTOP"):
            desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
            
            # 对于Niri桌面环境
            if "niri" in desktop:
                # 检查Niri特定的环境变量或配置
                if os.environ.get("NIRI_THEME") and "dark" in os.environ.get("NIRI_THEME", "").lower():
                    return True
                # 尝试读取Niri配置文件
                try:
                    config_path = os.path.expanduser("~/.config/niri/config.kdl")
                    if os.path.exists(config_path):
                        with open(config_path, 'r') as f:
                            content = f.read().lower()
                            if "dark" in content:
                                return True
                except Exception:
                    pass
        
        # 默认返回浅色主题
        return False
    
    def closeEvent(self, event):
        """关闭事件"""
        # 保存配置
        self.save_config()
        # 接受事件
        event.accept()
    
    def _set_light_theme(self):
        """设置浅色主题"""
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        # 浅色主题调色板
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
        
        app.setPalette(palette)
    
    def _set_dark_theme(self):
        """设置深色主题"""
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        # 深色主题调色板
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        
        app.setPalette(palette)
    
    def _set_material3_light_theme(self, theme_color="蓝色"):
        """设置Material3浅色主题"""
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        # 主题颜色映射
        color_map = {
            "蓝色": QColor(37, 99, 235),  # Material3蓝
            "绿色": QColor(16, 185, 129),  # Material3绿
            "红色": QColor(239, 68, 68),   # Material3红
            "紫色": QColor(139, 92, 246),  # Material3紫
            "橙色": QColor(249, 115, 22)   # Material3橙
        }
        
        # 获取主题颜色
        accent_color = color_map.get(theme_color, QColor(37, 99, 235))
        
        # Material3浅色主题调色板
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(230, 230, 230))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, accent_color)
        
        app.setPalette(palette)
    
    def _set_material3_dark_theme(self, theme_color="蓝色"):
        """设置Material3深色主题"""
        app = QApplication.instance()
        app.setStyle("Fusion")
        
        # 主题颜色映射（深色模式下的浅色版本）
        color_map = {
            "蓝色": QColor(96, 165, 250),  # Material3蓝（浅色）
            "绿色": QColor(52, 211, 153),  # Material3绿（浅色）
            "红色": QColor(252, 165, 165),  # Material3红（浅色）
            "紫色": QColor(186, 180, 254),  # Material3紫（浅色）
            "橙色": QColor(251, 146, 60)   # Material3橙（浅色）
        }
        
        # 获取主题颜色
        accent_color = color_map.get(theme_color, QColor(96, 165, 250))
        
        # Material3深色主题调色板
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(17, 24, 39))  # Material3深色背景
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(31, 41, 55))  # Material3深色表面
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(55, 65, 81))  # Material3深色表面变体
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(55, 65, 81))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, accent_color)
        
        app.setPalette(palette)
    
    def show_char_context_menu(self, position):
        """显示字符表格的右键菜单"""
        menu = QMenu()
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")
        
        action = menu.exec(self.char_table.mapToGlobal(position))
        if action == edit_action:
            self.edit_char()
        elif action == delete_action:
            self.delete_char()
    
    def show_word_context_menu(self, position):
        """显示词表表格的右键菜单"""
        menu = QMenu()
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")
        
        action = menu.exec(self.word_table.mapToGlobal(position))
        if action == edit_action:
            self.edit_word()
        elif action == delete_action:
            self.delete_word()
    
    def show_high_freq_context_menu(self, position):
        """显示高频词表格的右键菜单"""
        menu = QMenu()
        edit_action = menu.addAction("编辑")
        
        action = menu.exec(self.high_freq_table.mapToGlobal(position))
        if action == edit_action:
            # 获取选中的行
            selected_rows = self.high_freq_table.selectionModel().selectedRows()
            if selected_rows:
                row = selected_rows[0].row()
                word = self.high_freq_table.item(row, 1).text()
                # 查找并编辑该词
                self.edit_word_by_text(word)
    
    def edit_word_by_text(self, word_text):
        """根据词的文本查找并编辑该词"""
        try:
            # 在词表中查找该词
            word = self.dict_service.get_word_by_text(word_text)
            if word:
                # 调用编辑方法
                self.edit_word_by_id(word.id)
            else:
                QMessageBox.warning(self, "警告", f"未找到词: {word_text}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"编辑词失败: {e}")
    
    def edit_word_by_id(self, word_id):
        """根据词的ID编辑该词"""
        try:
            # 根据ID获取词
            word = self.dict_service.get_word_by_id(word_id)
            if word:
                # 显示编辑对话框
                dialog = QDialog(self)
                dialog.setWindowTitle("编辑词条")
                dialog.setGeometry(200, 200, 400, 200)
                
                layout = QVBoxLayout(dialog)
                
                form_layout = QFormLayout()
                
                word_edit = QLineEdit(word.word)
                word_edit.setReadOnly(True)
                code_edit = QLineEdit(word.code)
                weight_edit = QLineEdit(str(word.weight))
                
                form_layout.addRow("词:", word_edit)
                form_layout.addRow("编码:", code_edit)
                form_layout.addRow("权重:", weight_edit)
                
                button_layout = QHBoxLayout()
                save_button = QPushButton("保存")
                cancel_button = QPushButton("取消")
                
                def save_edit():
                    try:
                        new_code = code_edit.text()
                        new_weight = float(weight_edit.text())
                        
                        update_data = {}
                        if new_code != word.code:
                            update_data["code"] = new_code
                        if new_weight != word.weight:
                            update_data["weight"] = new_weight
                        
                        if update_data:
                            self.dict_service.update_word(word.word, **update_data)
                            QMessageBox.information(self, "成功", "词条更新成功")
                            dialog.accept()
                            self.refresh_words()
                        else:
                            dialog.reject()
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"保存失败: {e}")
                
                save_button.clicked.connect(save_edit)
                cancel_button.clicked.connect(dialog.reject)
                
                button_layout.addWidget(save_button)
                button_layout.addWidget(cancel_button)
                
                layout.addLayout(form_layout)
                layout.addLayout(button_layout)
                
                dialog.exec()
            else:
                QMessageBox.warning(self, "警告", f"未找到ID为 {word_id} 的词")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"编辑词失败: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VMTOOLPyQtApp()
    window.show()
    sys.exit(app.exec())
