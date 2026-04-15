#!/usr/bin/env python3
"""VM-TOOL 命令行工具入口"""
import sys
import subprocess
import os
from ui.cli.__main__ import app

if __name__ == "__main__":
    # 检查是否执行 --install 命令
    if "--install" in sys.argv:
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
    
    # 检查是否执行 --install-completion 命令
    if "--install-completion" in sys.argv:
        # 尝试直接生成补全脚本，绕过 shell 检测
        try:
            from typer.completion import get_completion_script
            
            # 尝试获取 shell 类型
            shell = None
            if len(sys.argv) > 2:
                shell = sys.argv[2]
            else:
                # 默认使用 zsh
                shell = "zsh"
            
            # 生成补全脚本
            prog_name = "vmtool"
            complete_var = f"_{prog_name.upper()}_COMPLETE"
            completion_script = get_completion_script(
                prog_name=prog_name,
                complete_var=complete_var,
                shell=shell
            )
            
            # 输出补全脚本到标准输出
            print(completion_script)
            
            # 打印安装说明
            print("\n=== 补全安装说明 ===")
            if shell == "zsh":
                print("1. 将上述输出保存到 ~/.zsh/completions/_vmtool")
                print("2. 确保 ~/.zsh/completions 目录在你的 fpath 中")
                print("3. 重新启动 zsh 或执行 'source ~/.zshrc' 来激活补全")
            elif shell == "bash":
                print("1. 将上述输出保存到 ~/.bash_completion.d/vmtool")
                print("2. 重新启动 bash 或执行 'source ~/.bash_completion.d/vmtool' 来激活补全")
            else:
                print(f"请将上述输出保存到适合 {shell} 的补全目录中")
            
            sys.exit(0)
        except Exception as e:
            print(f"补全生成失败: {e}")
            sys.exit(1)
    
    # 执行原有的命令
    app()
