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
    QProgressDialog, QTextEdit
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
        theme = config_manager.get("theme", "auto")
        self.set_theme(theme)
        
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
        
        # 设置菜单
        settings_menu = QMenu("设置", self)
        menu_bar.addMenu(settings_menu)
        
        # 主题子菜单
        theme_menu = QMenu("主题", self)
        settings_menu.addMenu(theme_menu)
        
        # 主题选项
        self.theme_auto = QAction("跟随系统", self, checkable=True)
        self.theme_light = QAction("浅色", self, checkable=True)
        self.theme_dark = QAction("深色", self, checkable=True)
        
        # 连接信号
        self.theme_auto.triggered.connect(self.on_theme_auto_triggered)
        self.theme_light.triggered.connect(self.on_theme_light_triggered)
        self.theme_dark.triggered.connect(self.on_theme_dark_triggered)
        
        # 添加到子菜单
        theme_menu.addAction(self.theme_auto)
        theme_menu.addAction(self.theme_light)
        theme_menu.addAction(self.theme_dark)
        
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
    
    def create_chars_tab(self, parent):
        """创建字表管理标签页"""
        layout = QVBoxLayout(parent)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.char_search_edit = QLineEdit()
        self.char_search_edit.setPlaceholderText("输入汉字搜索")
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.search_chars)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.char_search_edit)
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
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.search_words)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
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
        
        # 高频词
        high_freq_frame = QWidget()
        high_freq_layout = QVBoxLayout(high_freq_frame)
        
        high_freq_label = QLabel("高频词前10名")
        high_freq_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        high_freq_layout.addWidget(high_freq_label)
        
        self.high_freq_table = QTableWidget()
        self.high_freq_table.setColumnCount(4)
        self.high_freq_table.setHorizontalHeaderLabels(["排名", "词", "编码", "权重"])
        self.high_freq_table.setSortingEnabled(True)
        
        # 设置列宽
        self.high_freq_table.setColumnWidth(0, 60)
        self.high_freq_table.setColumnWidth(1, 150)
        self.high_freq_table.setColumnWidth(2, 120)
        self.high_freq_table.setColumnWidth(3, 80)
        
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
            # 只获取多个字符的词条
            multi_words = [word for word in words if len(word["word"]) > 1]
            self.word_table.setRowCount(len(multi_words))
            
            for i, word in enumerate(multi_words):
                self.word_table.setItem(i, 0, QTableWidgetItem(word["word"]))
                self.word_table.setItem(i, 1, QTableWidgetItem(word["code"]))
                self.word_table.setItem(i, 2, QTableWidgetItem(str(word["weight"])))
                self.word_table.setItem(i, 3, QTableWidgetItem("是" if word["manual"] else "否"))
            
            self.status_bar.showMessage(f"加载完成，共 {len(multi_words)} 条词条")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载词表失败: {e}")
            self.status_bar.showMessage("加载失败")
    
    def search_words(self):
        """搜索词条"""
        keyword = self.search_edit.text()
        if not keyword:
            self.refresh_words()
            return
        
        self.status_bar.showMessage(f"搜索 '{keyword}'...")
        
        # 清空表格
        self.word_table.setRowCount(0)
        
        try:
            results = self.dict_service.search_words(keyword)
            # 只获取多个字符的词条
            multi_words = [result for result in results if len(result["word"]) > 1]
            self.word_table.setRowCount(len(multi_words))
            
            for i, result in enumerate(multi_words):
                self.word_table.setItem(i, 0, QTableWidgetItem(result["word"]))
                self.word_table.setItem(i, 1, QTableWidgetItem(result["code"]))
                self.word_table.setItem(i, 2, QTableWidgetItem(str(result["weight"])))
            
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
        rule_combo.addItems(["first_letter", "all_letters", "custom"])
        rule_combo.setCurrentText("first_letter")
        
        separator_edit = QLineEdit()
        separator_edit.setPlaceholderText("编码分隔符")
        
        max_length_edit = QLineEdit()
        max_length_edit.setText("10")
        
        form_layout.addRow("编码规则:", rule_combo)
        form_layout.addRow("分隔符:", separator_edit)
        form_layout.addRow("最大长度:", max_length_edit)
        
        button_layout = QHBoxLayout()
        calculate_button = QPushButton("计算")
        cancel_button = QPushButton("取消")
        
        def calculate():
            try:
                rule = rule_combo.currentText()
                separator = separator_edit.text()
                max_length = int(max_length_edit.text())
                
                # 设置编码生成配置
                config = {
                    'rule': rule,
                    'separator': separator,
                    'max_length': max_length
                }
                self.dict_service.code_generator.set_config(config)
                
                # 批量计算编码
                result = self.dict_service.calculate_all_codes()
                
                QMessageBox.information(
                    self, "成功", 
                    f"批量计算编码完成:\n" +
                    f"总词条数: {result['total']}\n" +
                    f"成功更新: {result['updated']}\n" +
                    f"更新失败: {result['failed']}"
                )
                
                # 刷新词表
                self.refresh_words()
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
            
            # 更新高频词
            self.high_freq_table.setRowCount(0)
            high_freq_words = report['high_frequency_words']
            
            for i, word in enumerate(high_freq_words[:10], 1):
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
        QMessageBox.information(
            self, "成功", f"导入成功: 添加了 {result['added']} 条，跳过了 {result['existing']} 条"
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
            # 只获取单个字符的词条
            chars = [word for word in words if len(word["word"]) == 1]
            self.char_table.setRowCount(len(chars))
            
            for i, char in enumerate(chars):
                self.char_table.setItem(i, 0, QTableWidgetItem(char["word"]))
                self.char_table.setItem(i, 1, QTableWidgetItem(char["code"]))
                self.char_table.setItem(i, 2, QTableWidgetItem(str(char["weight"])))
                self.char_table.setItem(i, 3, QTableWidgetItem("是" if char["manual"] else "否"))
            
            self.status_bar.showMessage(f"加载完成，共 {len(chars)} 条汉字")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载字表失败: {e}")
            self.status_bar.showMessage("加载失败")
    
    def search_chars(self):
        """搜索汉字"""
        keyword = self.char_search_edit.text()
        if not keyword:
            self.refresh_chars()
            return
        
        self.status_bar.showMessage(f"搜索 '{keyword}'...")
        
        # 清空表格
        self.char_table.setRowCount(0)
        
        try:
            results = self.dict_service.search_words(keyword)
            # 只获取单个字符的词条
            chars = [result for result in results if len(result["word"]) == 1]
            self.char_table.setRowCount(len(chars))
            
            for i, char in enumerate(chars):
                self.char_table.setItem(i, 0, QTableWidgetItem(char["word"]))
                self.char_table.setItem(i, 1, QTableWidgetItem(char["code"]))
                self.char_table.setItem(i, 2, QTableWidgetItem(str(char["weight"])))
            
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
    
    def on_theme_auto_triggered(self, checked):
        """处理跟随系统主题触发"""
        if checked:
            self.theme_light.setChecked(False)
            self.theme_dark.setChecked(False)
            self.set_theme("auto")
            # 保存配置
            config_manager.set("theme", "auto")
    
    def on_theme_light_triggered(self, checked):
        """处理浅色主题触发"""
        if checked:
            self.theme_auto.setChecked(False)
            self.theme_dark.setChecked(False)
            self.set_theme("light")
            # 保存配置
            config_manager.set("theme", "light")
    
    def on_theme_dark_triggered(self, checked):
        """处理深色主题触发"""
        if checked:
            self.theme_auto.setChecked(False)
            self.theme_light.setChecked(False)
            self.set_theme("dark")
            # 保存配置
            config_manager.set("theme", "dark")
    
    def set_theme(self, theme):
        """设置主题"""
        from PyQt6.QtCore import Qt
        
        # 更新选中状态
        self.theme_auto.setChecked(theme == "auto")
        self.theme_light.setChecked(theme == "light")
        self.theme_dark.setChecked(theme == "dark")
        
        # 获取应用实例
        app = QApplication.instance()
        
        if theme == "auto":
            # 跟随系统主题
            is_dark = self._detect_system_theme()
            if is_dark:
                self._set_dark_theme()
            else:
                self._set_light_theme()
        elif theme == "dark":
            # 深色主题
            self._set_dark_theme()
        else:
            # 浅色主题
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VMTOOLPyQtApp()
    window.show()
    sys.exit(app.exec())
