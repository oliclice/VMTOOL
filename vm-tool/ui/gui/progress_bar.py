"""统一的进度条组件"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal


class ProgressBarWidget(QWidget):
    """统一的进度条组件
    
    用于显示所有异步操作的进度，包括：
    - 数据导入
    - 数据导出
    - 批量添加
    - 计算编码
    - 刷新页面
    - 其他耗时操作
    """
    
    # 进度信号
    progress_updated = pyqtSignal(int, str)  # (进度值 0-100, 消息)
    cancel_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置 UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("QLabel { color: #666; }")
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setMaximumHeight(20)
        layout.addWidget(self.progress_bar)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setMaximumWidth(60)
        self.cancel_button.setMaximumHeight(25)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        layout.addWidget(self.cancel_button)
        
        # 隐藏进度条（初始状态）
        self.set_visible(False)
    
    def set_visible(self, visible):
        """设置进度条可见性"""
        self.progress_bar.setVisible(visible)
        self.cancel_button.setVisible(visible)
        if not visible:
            self.status_label.setText("就绪")
            self.status_label.setStyleSheet("QLabel { color: #666; }")
    
    def start_progress(self, message="正在处理..."):
        """开始进度
        
        Args:
            message: 显示的消息
        """
        self.set_visible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(message)
        
        # 使用主题色
        from app.core.theme_manager import theme_manager
        theme_color = theme_manager.get_theme_color()
        color_map = {
            "blue": "#1976D2",
            "green": "#4CAF50",
            "red": "#F44336",
            "purple": "#9C27B0",
            "orange": "#FF9800"
        }
        color = color_map.get(theme_color, "#1976D2")
        
        self.status_label.setStyleSheet(f"QLabel {{ color: {color}; font-weight: bold; }}")
        self.cancel_button.setEnabled(True)
        
    def update_progress(self, value, message=None):
        """更新进度
        
        Args:
            value: 进度值 (0-100)
            message: 可选的消息，如果不提供则保持原消息
        """
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)
    
    def finish_progress(self, message="完成", success=True):
        """完成进度
        
        Args:
            message: 完成消息
            success: 是否成功
        """
        self.set_visible(True)
        self.progress_bar.setValue(100)
        if success:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("QLabel { color: #4CAF50; font-weight: bold; }")
        else:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("QLabel { color: #F44336; font-weight: bold; }")
        self.cancel_button.setEnabled(False)
        
        # 2 秒后隐藏
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.set_visible(False))
    
    def error_progress(self, message="错误"):
        """显示错误
        
        Args:
            message: 错误消息
        """
        self.set_visible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(message)
        self.status_label.setStyleSheet("QLabel { color: #F44336; font-weight: bold; }")
        self.cancel_button.setEnabled(False)
        
        # 3 秒后隐藏
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.set_visible(False))
    
    def on_cancel_clicked(self):
        """处理取消按钮点击"""
        self.cancel_clicked.emit()
    
    def set_cancel_enabled(self, enabled):
        """设置取消按钮是否可用"""
        self.cancel_button.setEnabled(enabled)
