#!/usr/bin/env python3
"""最小化 PyQt6 测试 - 验证 PyQt6 是否能正常显示窗口"""
import sys

print("[Test] 导入 PyQt6...", flush=True)
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

print("[Test] 创建 QApplication...", flush=True)
app = QApplication(sys.argv)

print("[Test] 创建主窗口...", flush=True)
window = QMainWindow()
window.setWindowTitle("PyQt6 测试窗口")
window.resize(800, 600)

print("[Test] 创建中央组件...", flush=True)
central_widget = QWidget()
layout = QVBoxLayout(central_widget)
label = QLabel("如果看到这个窗口，说明 PyQt6 工作正常！")
label.setAlignment(0x0004 | 0x0080)  # AlignCenter
layout.addWidget(label)
window.setCentralWidget(central_widget)

print("[Test] 移动窗口到屏幕中心...", flush=True)
from PyQt6.QtGui import QGuiApplication
screen = QGuiApplication.primaryScreen().geometry()
x = (screen.width() - 800) // 2
y = (screen.height() - 600) // 2
window.move(x, y)

print(f"[Test] 窗口位置: ({x}, {y})", flush=True)
print(f"[Test] 屏幕大小: {screen.width()}x{screen.height()}", flush=True)

print("[Test] 调用 window.show()...", flush=True)
window.show()

print(f"[Test] window.isVisible(): {window.isVisible()}", flush=True)
print(f"[Test] window.isHidden(): {window.isHidden()}", flush=True)

print("[Test] ===== 准备进入事件循环 =====", flush=True)
print("[Test] 你应该能看到一个测试窗口了！", flush=True)
print("[Test] 如果看不到窗口，请检查任务栏是否有窗口图标", flush=True)

# 强制提升窗口
window.raise_()
window.activateWindow()

print("[Test] 调用 app.exec()...", flush=True)
exit_code = app.exec()
print(f"[Test] 退出码: {exit_code}", flush=True)
sys.exit(exit_code)
