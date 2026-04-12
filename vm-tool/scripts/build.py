#!/usr/bin/env python3
"""多平台打包脚本"""
import os
import sys
import subprocess
import argparse


def build_linux():
    """构建 Linux 版本"""
    print("构建 Linux 版本...")
    # 构建命令行工具
    subprocess.run([
        "pyinstaller",
        "vm-tool/vmtool.py",
        "--name", "vmtool",
        "--distpath", "dist/linux",
        "--workpath", "build/linux",
        "--noconfirm",
        "--console"
    ], check=True)
    # 构建 GUI 工具
    subprocess.run([
        "pyinstaller",
        "vm-tool/vmtool.py",
        "--name", "vmtool-gui",
        "--distpath", "dist/linux",
        "--workpath", "build/linux",
        "--noconfirm",
        "--windowed"
    ], check=True)
    print("Linux 版本构建完成")


def build_windows():
    """构建 Windows 版本"""
    print("构建 Windows 版本...")
    # 构建命令行工具
    subprocess.run([
        "pyinstaller",
        "vm-tool/vmtool.py",
        "--name", "vmtool",
        "--distpath", "dist/windows",
        "--workpath", "build/windows",
        "--noconfirm",
        "--console"
    ], check=True)
    # 构建 GUI 工具
    subprocess.run([
        "pyinstaller",
        "vm-tool/vmtool.py",
        "--name", "vmtool-gui",
        "--distpath", "dist/windows",
        "--workpath", "build/windows",
        "--noconfirm",
        "--windowed"
    ], check=True)
    print("Windows 版本构建完成")


def build_macos():
    """构建 macOS 版本"""
    print("构建 macOS 版本...")
    # 构建命令行工具
    subprocess.run([
        "pyinstaller",
        "vm-tool/vmtool.py",
        "--name", "vmtool",
        "--distpath", "dist/macos",
        "--workpath", "build/macos",
        "--noconfirm",
        "--console"
    ], check=True)
    # 构建 GUI 工具
    subprocess.run([
        "pyinstaller",
        "vm-tool/vmtool.py",
        "--name", "vmtool-gui",
        "--distpath", "dist/macos",
        "--workpath", "build/macos",
        "--noconfirm",
        "--windowed"
    ], check=True)
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
