#!/usr/bin/env python3
"""VM-TOOL 命令行工具入口"""
import sys
import subprocess
from ui.cli.__main__ import app

if __name__ == "__main__":
    # 检查是否执行 --install 或 --install-completion 命令
    if "--install" in sys.argv or "--install-completion" in sys.argv:
        # 执行 pip install -e . 命令
        print("正在安装项目...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd=sys.path[0],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("项目安装成功！")
        else:
            print(f"项目安装失败: {result.stderr}")
        
        # 直接退出，避免执行其他命令
        sys.exit(0)
    
    # 执行原有的命令
    app()
