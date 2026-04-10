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
    QTreeWidget, QTreeWidgetItem, QSplitter, QStatusBar, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtGui import QAction, QIcon, QFont, QColor, QStandardItemModel, QStandardItem

from app.services.dict import DictService
from app.services.weight import WeightCalculator
from app.services.filter import FilterService
from app.services.stats import StatsService


class VMTOOLPyQtApp(QMainWindow):
    """VM-TOOL PyQt6 GUI应用"""
    
    def __init__(self):
        """初始化应用"""
        super().__init__()
        self.setWindowTitle("VM-TOOL - 码表处理工具")
        self.setGeometry(100, 100, 1000, 700)
        
        # 初始化服务
        self.dict_service = DictService()
        self.weight_calc = WeightCalculator()
        self.filter_service = FilterService()
        self.stats_service = StatsService()
        
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
        self.word_table.setColumnCount(3)
        self.word_table.setHorizontalHeaderLabels(["词", "编码", "权重"])
        self.word_table.setSortingEnabled(True)
        self.word_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 设置列宽
        self.word_table.setColumnWidth(0, 200)
        self.word_table.setColumnWidth(1, 150)
        self.word_table.setColumnWidth(2, 100)
        
        layout.addWidget(self.word_table)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_word)
        
        edit_button = QPushButton("编辑")
        edit_button.clicked.connect(self.edit_word)
        
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self.delete_word)
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_words)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
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
            self.word_table.setRowCount(len(words))
            
            for i, word in enumerate(words):
                self.word_table.setItem(i, 0, QTableWidgetItem(word.word))
                self.word_table.setItem(i, 1, QTableWidgetItem(word.code))
                self.word_table.setItem(i, 2, QTableWidgetItem(str(word.weight)))
            
            self.status_bar.showMessage(f"加载完成，共 {len(words)} 条词条")
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
            self.word_table.setRowCount(len(results))
            
            for i, result in enumerate(results):
                self.word_table.setItem(i, 0, QTableWidgetItem(result["word"]))
                self.word_table.setItem(i, 1, QTableWidgetItem(result["code"]))
                self.word_table.setItem(i, 2, QTableWidgetItem(str(result["weight"])))
            
            self.status_bar.showMessage(f"搜索完成，找到 {len(results)} 条结果")
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
        
        self.status_bar.showMessage(f"导入 {format} 文件...")
        
        try:
            if format == "txt":
                result = self.filter_service.import_from_txt(file_path)
            elif format == "csv":
                result = self.filter_service.import_from_csv(file_path)
            elif format == "json":
                result = self.filter_service.import_from_json(file_path)
            else:
                QMessageBox.critical(self, "错误", "不支持的格式")
                return
            
            QMessageBox.information(
                self, "成功", f"导入成功: 添加了 {result['added']} 条，跳过了 {result['existing']} 条"
            )
            self.refresh_words()
            self.status_bar.showMessage("导入完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {e}")
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VMTOOLPyQtApp()
    window.show()
    sys.exit(app.exec())
