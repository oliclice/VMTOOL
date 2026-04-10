#!/usr/bin/env python3
"""VM-TOOL 工具入口"""
import sys
import os

# 检测是否是 GUI 模式运行
is_gui_mode = os.path.basename(sys.argv[0]) == "vmtool-gui"

if is_gui_mode:
    # 启动 GUI 界面
    from ui.gui.pyqt_app import main as gui_main
    if __name__ == "__main__":
        gui_main()
else:
    # 启动命令行界面
    from ui.cli.__main__ import app
    if __name__ == "__main__":
        app()
