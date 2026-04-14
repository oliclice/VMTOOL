#!/usr/bin/env python3
"""GUI 启动测试脚本 - 显示详细日志"""
import sys
import os

# 强制标准输出无缓冲
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80, flush=True)
print("VM-TOOL GUI 详细诊断日志", flush=True)
print("=" * 80, flush=True)

try:
    print("\n[步骤 1] 导入 PyQt6...", flush=True)
    from PyQt6.QtWidgets import QApplication
    print("✓ PyQt6 导入成功", flush=True)
    
    print("\n[步骤 2] 创建 QApplication...", flush=True)
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        print("✓ 创建新的 QApplication", flush=True)
    else:
        print("✓ 使用已存在的 QApplication", flush=True)
    
    print("\n[步骤 3] 导入 VMTOOLPyQtApp...", flush=True)
    from ui.gui.pyqt_app import VMTOOLPyQtApp
    print("✓ VMTOOLPyQtApp 导入成功", flush=True)
    
    print("\n[步骤 4] 创建主窗口（这可能会显示详细日志）...", flush=True)
    print("-" * 80, flush=True)
    window = VMTOOLPyQtApp()
    print("-" * 80, flush=True)
    print("✓ 主窗口创建成功", flush=True)
    
    print(f"\n[步骤 5] 窗口信息:", flush=True)
    print(f"  - 标题: {window.windowTitle()}", flush=True)
    print(f"  - 大小: {window.size().width()}x{window.size().height()}", flush=True)
    print(f"  - 标签页数: {window.tab_widget.count() if hasattr(window, 'tab_widget') else 'N/A'}", flush=True)
    
    print("\n[步骤 6] 显示窗口...", flush=True)
    window.show()
    print("✓ 窗口已显示", flush=True)
    
    print("\n" + "=" * 80, flush=True)
    print("GUI 启动成功！现在应该能看到窗口了。", flush=True)
    print("按 Ctrl+C 退出。", flush=True)
    print("=" * 80, flush=True)
    
    # 启动事件循环
    sys.exit(app.exec())
    
except Exception as e:
    print(f"\n✗ 错误: {e}", flush=True)
    import traceback
    print("\n详细错误堆栈:", flush=True)
    traceback.print_exc()
    sys.exit(1)
