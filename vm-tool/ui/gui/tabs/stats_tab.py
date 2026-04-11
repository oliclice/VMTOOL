from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QLabel, QComboBox, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt
from app.services.stats import StatsService

class StatsTab(QWidget):
    """统计分析标签页"""
    def __init__(self, parent=None, stats_service=None):
        super().__init__(parent)
        self.stats_service = stats_service
        self.init_ui()
        self.refresh_stats()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 统计数据展示
        stats_group = QGroupBox("统计数据")
        stats_layout = QVBoxLayout()
        
        # 总词条数
        self.total_words_label = QLabel("总词条数: 0")
        stats_layout.addWidget(self.total_words_label)
        
        # 总字符数
        self.total_chars_label = QLabel("总字符数: 0")
        stats_layout.addWidget(self.total_chars_label)
        
        # 总特殊字符数
        self.total_special_label = QLabel("总特殊字符数: 0")
        stats_layout.addWidget(self.total_special_label)
        
        # 编码冲突数
        self.conflicts_label = QLabel("编码冲突数: 0")
        stats_layout.addWidget(self.conflicts_label)
        
        # 平均词长
        self.avg_word_length_label = QLabel("平均词长: 0")
        stats_layout.addWidget(self.avg_word_length_label)
        
        # 平均编码长度
        self.avg_code_length_label = QLabel("平均编码长度: 0")
        stats_layout.addWidget(self.avg_code_length_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # 编码长度分布
        code_length_group = QGroupBox("编码长度分布")
        code_length_layout = QVBoxLayout()
        
        self.code_length_table = QTableWidget()
        self.code_length_table.setColumnCount(2)
        self.code_length_table.setHorizontalHeaderLabels(["编码长度", "数量"])
        code_length_layout.addWidget(self.code_length_table)
        
        code_length_group.setLayout(code_length_layout)
        layout.addWidget(code_length_group)
        
        # 词长分布
        word_length_group = QGroupBox("词长分布")
        word_length_layout = QVBoxLayout()
        
        self.word_length_table = QTableWidget()
        self.word_length_table.setColumnCount(2)
        self.word_length_table.setHorizontalHeaderLabels(["词长", "数量"])
        word_length_layout.addWidget(self.word_length_table)
        
        word_length_group.setLayout(word_length_layout)
        layout.addWidget(word_length_group)
        
        # 刷新按钮
        refresh_button = QPushButton("刷新统计")
        refresh_button.clicked.connect(self.refresh_stats)
        layout.addWidget(refresh_button)
    
    def refresh_stats(self):
        """刷新统计数据"""
        if not self.stats_service:
            return
        
        try:
            # 获取统计数据
            stats = self.stats_service.get_stats()
            
            # 更新统计标签
            self.total_words_label.setText(f"总词条数: {stats.get('total_words', 0)}")
            self.total_chars_label.setText(f"总字符数: {stats.get('total_chars', 0)}")
            self.total_special_label.setText(f"总特殊字符数: {stats.get('total_special', 0)}")
            self.conflicts_label.setText(f"编码冲突数: {stats.get('conflicts', 0)}")
            self.avg_word_length_label.setText(f"平均词长: {stats.get('avg_word_length', 0):.2f}")
            self.avg_code_length_label.setText(f"平均编码长度: {stats.get('avg_code_length', 0):.2f}")
            
            # 更新编码长度分布
            code_length_dist = stats.get('code_length_distribution', {})
            self.code_length_table.setRowCount(len(code_length_dist))
            for i, (length, count) in enumerate(code_length_dist.items()):
                self.code_length_table.setItem(i, 0, QTableWidgetItem(str(length)))
                self.code_length_table.setItem(i, 1, QTableWidgetItem(str(count)))
            
            # 更新词长分布
            word_length_dist = stats.get('word_length_distribution', {})
            self.word_length_table.setRowCount(len(word_length_dist))
            for i, (length, count) in enumerate(word_length_dist.items()):
                self.word_length_table.setItem(i, 0, QTableWidgetItem(str(length)))
                self.word_length_table.setItem(i, 1, QTableWidgetItem(str(count)))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新统计数据失败: {e}")