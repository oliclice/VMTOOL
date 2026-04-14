#!/usr/bin/env python3
"""GUI 诊断脚本"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.gui.pyqt_app import VMTOOLPyQtApp

def diagnose():
    """诊断 GUI 问题"""
    print("=" * 60)
    print("VM-TOOL GUI 诊断工具")
    print("=" * 60)
    
    # 1. 检查 QApplication
    print("\n[1] 检查 QApplication...")
    app = QApplication.instance()
    if app is None:
        print("  ✓ 创建新的 QApplication")
        app = QApplication(sys.argv)
    else:
        print("  ✓ QApplication 已存在")
    
    # 2. 检查数据库初始化
    print("\n[2] 检查数据库初始化...")
    try:
        from app.dal.init_db import init_database
        init_database()
        print("  ✓ 数据库初始化成功")
    except Exception as e:
        print(f"  ✗ 数据库初始化失败: {e}")
        return
    
    # 3. 检查服务初始化
    print("\n[3] 检查服务初始化...")
    try:
        from app.services.dict import DictService
        from app.services.weight import WeightCalculator
        from app.services.filter import FilterService
        from app.services.stats import StatsService
        
        dict_service = DictService()
        print("  ✓ DictService 初始化成功")
        
        weight_calc = WeightCalculator()
        print("  ✓ WeightCalculator 初始化成功")
        
        filter_service = FilterService()
        print("  ✓ FilterService 初始化成功")
        
        stats_service = StatsService()
        print("  ✓ StatsService 初始化成功")
    except Exception as e:
        print(f"  ✗ 服务初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. 检查主窗口创建
    print("\n[4] 检查主窗口创建...")
    try:
        window = VMTOOLPyQtApp()
        print("  ✓ 主窗口创建成功")
        
        # 检查组件
        print("\n[5] 检查窗口组件...")
        print(f"  - 窗口标题: {window.windowTitle()}")
        print(f"  - 窗口大小: {window.size().width()}x{window.size().height()}")
        print(f"  - 中央组件: {'✓' if window.centralWidget() else '✗'}")
        print(f"  - 菜单栏: {'✓' if window.menuBar() else '✗'}")
        print(f"  - 状态栏: {'✓' if window.statusBar() else '✗'}")
        
        if hasattr(window, 'tab_widget'):
            print(f"  - 标签页组件: ✓")
            print(f"    - 标签页数量: {window.tab_widget.count()}")
            for i in range(window.tab_widget.count()):
                print(f"      - 标签 {i}: {window.tab_widget.tabText(i)}")
        else:
            print(f"  - 标签页组件: ✗ (未找到)")
        
        if hasattr(window, 'dict_service'):
            print(f"  - dict_service: {'✓' if window.dict_service else '✗'}")
        if hasattr(window, 'stats_service'):
            print(f"  - stats_service: {'✓' if window.stats_service else '✗'}")
        
        print("\n" + "=" * 60)
        print("诊断完成！正在启动 GUI...")
        print("=" * 60)
        
        window.show()
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"  ✗ 主窗口创建失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()
