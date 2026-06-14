"""Toast 通知组件

从右下角滑入的短暂消息提示，支持 4 种类型。
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont


class Toast(QWidget):
    """从右下角滑入的短暂消息提示

    用法:
        Toast.show(parent, "保存成功", type="success", duration=3000)

    type: "info" | "success" | "error" | "warning"
    """

    @staticmethod
    def show(parent, message: str, type: str = "info", duration: int = 3000):
        """在 parent 右下角显示 toast"""
        toast = Toast(parent, message, type, duration)
        toast.show()
        return toast

    def __init__(self, parent, message: str, type: str = "info", duration: int = 3000):
        super().__init__(parent)
        self.type = type
        self.duration = duration
        self._setup_ui(message)
        self._setup_animation()

    def _setup_ui(self, message: str):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(48)
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 内容容器
        container = QWidget()
        container.setObjectName("toast_container")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(12, 8, 12, 8)
        container_layout.setSpacing(8)

        # 类型图标
        icon_map = {
            "info": "ℹ",
            "success": "✓",
            "error": "✗",
            "warning": "⚠"
        }
        icon_label = QLabel(icon_map.get(self.type, "ℹ"))
        icon_label.setObjectName("toast_icon")
        icon_label.setFixedWidth(20)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(icon_label)

        # 消息文本
        msg_label = QLabel(message)
        msg_label.setObjectName("toast_message")
        msg_label.setWordWrap(True)
        container_layout.addWidget(msg_label, 1)

        layout.addWidget(container)

        # 应用样式
        self._apply_style()

    def _apply_style(self):
        """应用类型相关的样式"""
        # 颜色映射
        color_map = {
            "info": "#5e6ad2",
            "success": "#27a644",
            "error": "#ef4444",
            "warning": "#f97316"
        }
        accent = color_map.get(self.type, "#5e6ad2")

        self.setStyleSheet(f"""
            #toast_container {{
                background-color: #191a1b;
                border: 1px solid rgba(255,255,255,0.08);
                border-left: 3px solid {accent};
                border-radius: 8px;
            }}
            #toast_icon {{
                color: {accent};
                font-size: 14px;
                border: none;
                background: transparent;
            }}
            #toast_message {{
                color: #f7f8f8;
                font-size: 13px;
                border: none;
                background: transparent;
            }}
        """)

    def _setup_animation(self):
        """设置动画"""
        # 位置动画
        self._pos_anim = QPropertyAnimation(self, b"pos")
        self._pos_anim.setDuration(200)
        self._pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 透明度动画 (通过 opacity effect)
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)

        self._opacity_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._opacity_anim.setDuration(200)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def showEvent(self, event):
        super().showEvent(event)

        # 定位到父窗口右下角
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.width() - self.width() - 16
            y = parent_rect.height() - self.height() - 16
            self.move(x, y + self.height())  # 从下方滑入

        # 播放滑入动画
        start_pos = self.pos()
        end_pos = self.pos() - __import__('PyQt6.QtCore', fromlist=['QPoint']).QPoint(0, self.height())

        self._pos_anim.setStartValue(start_pos)
        self._pos_anim.setEndValue(end_pos)

        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)

        self._pos_anim.start()
        self._opacity_anim.start()

        # 自动关闭计时器
        QTimer.singleShot(self.duration, self._close)

    def _close(self):
        """关闭 toast"""
        # 淡出动画
        self._opacity_anim.setStartValue(1.0)
        self._opacity_anim.setEndValue(0.0)
        self._opacity_anim.finished.connect(self.deleteLater)
        self._opacity_anim.start()
