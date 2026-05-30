#!/usr/bin/env python3
"""VM-TOOL 命令行工具入口"""
import sys
import subprocess
import os

if __name__ == "__main__":
    # 检查是否执行 --install 命令
    if "--install" in sys.argv:
        import importlib.metadata

        # 需要检查的依赖（与 pyproject.toml [project].dependencies 对齐）
        REQUIRED_DEPS = [
            "pydantic", "pydantic-settings", "sqlalchemy", "alembic",
            "typer", "rich", "fastapi", "uvicorn", "jinja2", "PyQt6",
        ]

        def _check_dep(pkg_name: str) -> bool:
            """检查依赖是否已安装"""
            try:
                importlib.metadata.distribution(pkg_name)
                return True
            except importlib.metadata.PackageNotFoundError:
                return False

        # 1) 检测缺失的依赖
        missing = [p for p in REQUIRED_DEPS if not _check_dep(p)]

        if missing:
            print(f"检测到缺失依赖: {', '.join(missing)}")
            print("正在安装缺失依赖...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", *missing],
                cwd=sys.path[0],
                capture_output=False,
            )
            if result.returncode != 0:
                print("依赖安装失败")
                sys.exit(1)
        else:
            print("所有依赖已安装，跳过依赖安装")

        # 2) 以 editable 模式安装项目本身（--no-deps 跳过依赖解析）
        print("正在安装项目...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", ".", "--no-deps"],
            cwd=sys.path[0],
            capture_output=True,
            text=True,
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
    
    # 执行原有的命令（延迟导入，避免 --install 时加载全部依赖）
    from ui.cli.__main__ import app
    app()
