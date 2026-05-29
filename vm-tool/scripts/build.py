#!/usr/bin/env python3
"""多平台打包脚本"""
import os
import sys
import subprocess
import argparse

# 切换到项目根目录（vm-tool/ 目录）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

# 不需要打包的模块列表（项目不需要但被自动拉入的依赖）
EXCLUDE_MODULES = [
    # Qt 冲突
    "PyQt5",
    # 科学计算
    "numpy", "scipy", "pandas", "numba", "llvmlite", "pyarrow",
    # 数据处理
    "lxml", "rapidfuzz", "openpyxl", "xlrd", "xlwt",
    # 云服务/AWS
    "botocore", "boto3", "s3transfer", "awscli",
    # 数据库客户端（项目只需要 sqlite3）
    "psycopg", "psycopg2", "psycopg_binary", "mysqlclient", "pymysql",
    # Web 框架
    "django", "flask", "fastapi", "uvicorn", "starlette",
    # 可视化
    "matplotlib", "seaborn", "plotly", "bokeh",
    # 图像处理
    "PIL", "pillow", "opencv",
    # Jupyter/IPython
    "IPython", "ipykernel", "ipywidgets", "nbformat", "nbconvert", "jupyter",
    # 测试/代码质量
    "pytest", "hypothesis", "black", "isort", "ruff", "mypy",
    # 深度学习
    "torch", "torchvision", "torchaudio", "tensorflow", "keras",
    # 消息队列/网络
    "zmq", "celery", "redis", "kafka",
    # 其他不需要的
    "jedi", "parso", "tkinter", "_tkinter",
    "setuptools", "pkg_resources", "wheel", "pip",
    "cryptography", "paramiko", "bcrypt",
    "aiohttp", "httpx", "requests",
    "jsonschema", "pydantic_extra_types",
]


def _build_common_args(name: str, distpath: str, workpath: str, windowed: bool = False):
    """构建通用参数"""
    args = [
        "pyinstaller",
        "vmtool.py",
        "--name", name,
        "--distpath", distpath,
        "--workpath", workpath,
        "--noconfirm",
    ]
    for mod in EXCLUDE_MODULES:
        args.extend(["--exclude-module", mod])
    if windowed:
        args.append("--windowed")
    else:
        args.append("--console")
    return args


def build_linux():
    """构建 Linux 版本"""
    print("构建 Linux 版本...")
    subprocess.run(_build_common_args("vmtool", "dist/linux", "build/linux"), check=True)
    subprocess.run(_build_common_args("vmtool-gui", "dist/linux", "build/linux", windowed=True), check=True)
    print("Linux 版本构建完成")


def build_windows():
    """构建 Windows 版本"""
    print("构建 Windows 版本...")
    subprocess.run(_build_common_args("vmtool", "dist/windows", "build/windows"), check=True)
    subprocess.run(_build_common_args("vmtool-gui", "dist/windows", "build/windows", windowed=True), check=True)
    print("Windows 版本构建完成")


def build_macos():
    """构建 macOS 版本"""
    print("构建 macOS 版本...")
    subprocess.run(_build_common_args("vmtool", "dist/macos", "build/macos"), check=True)
    subprocess.run(_build_common_args("vmtool-gui", "dist/macos", "build/macos", windowed=True), check=True)
    print("macOS 版本构建完成")


def build_all():
    """构建所有平台版本"""
    build_linux()
    build_windows()
    build_macos()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="多平台打包脚本")
    parser.add_argument("--linux", action="store_true", help="构建Linux版本")
    parser.add_argument("--windows", action="store_true", help="构建Windows版本")
    parser.add_argument("--macos", action="store_true", help="构建macOS版本")
    parser.add_argument("--all", action="store_true", help="构建所有平台版本")
    
    args = parser.parse_args()
    
    if args.linux:
        build_linux()
    elif args.windows:
        build_windows()
    elif args.macos:
        build_macos()
    elif args.all:
        build_all()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
