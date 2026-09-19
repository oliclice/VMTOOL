#!/usr/bin/env python3
"""VM-TOOL 安装器与命令行入口。

设计目标：部署一次之后，任何人直接敲 ``vmtool``（即 ``~/.local/bin/vmtool``）
即可使用，不需要关心解释器、虚拟环境或依赖版本。

为此 ``--install`` 与「当前解释器」彻底解耦：

1. 在项目根目录下创建或复用 ``.venv``；
2. 一律使用**该 venv 的解释器**执行 pip——这样 pyproject.toml 里
   PyQt6 与 Qt6 运行库的版本上界才会真正生效；
3. 在 ``~/.local/bin/`` 写入启动器，其内容固定 exec 到该 venv 的解释器。

因此即便有人用系统 python 执行 ``python3 vmtool.py --install``，也不会再出现
「装进用户级 site-packages、入口指向系统 python、进而加载到版本不匹配的
PyQt6/Qt 而崩溃」的老问题。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv"
LAUNCHER_NAME = "vmtool"

_LAUNCHER_TEMPLATE = """#!/bin/sh
# VMtool 启动器 —— 由 `python3 vmtool.py --install` 生成，请勿手工编辑。
# 解释器固定指向项目自带 venv，避免加载系统或用户级 site-packages 中
# 版本不匹配的 PyQt6 与 Qt 运行库（否则会报 undefined symbol / Qt_6_PRIVATE_API）。
VMTOOL_ROOT='{root}'
VMTOOL_PY='{python}'
VMTOOL_BIN="$VMTOOL_ROOT/.venv/bin/{name}"
# 优先走 venv 自己的入口脚本，这样 --help 显示的是 vmtool 而非 python -m ui.cli
if [ -x "$VMTOOL_BIN" ]; then
  exec "$VMTOOL_BIN" "$@"
fi
if [ ! -x "$VMTOOL_PY" ]; then
  echo "vmtool: 项目环境缺失：$VMTOOL_PY" >&2
  echo "vmtool: 请重新初始化：python3 '$VMTOOL_ROOT/vmtool.py' --install" >&2
  exit 1
fi
exec "$VMTOOL_PY" -m ui.cli "$@"
"""


def venv_python() -> Path:
    """返回项目 venv 中解释器的路径（跨平台）。"""
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_venv() -> Path:
    """确保项目 venv 存在，返回其解释器路径。"""
    python = venv_python()
    if python.exists():
        print(f"[1/4] 复用已有虚拟环境：{VENV_DIR}")
        return python

    print(f"[1/4] 创建虚拟环境：{VENV_DIR}")
    result = subprocess.run(
        [sys.executable, "-m", "venv", str(VENV_DIR)],
        cwd=PROJECT_ROOT,
    )
    if result.returncode != 0 or not python.exists():
        raise SystemExit(
            "创建虚拟环境失败（请确认系统已安装 python3-venv），"
            f"或手工执行：{sys.executable} -m venv {VENV_DIR}"
        )
    return python


def install_project(python: Path) -> None:
    """在 venv 中安装项目及其依赖（版本约束由 pyproject.toml 决定）。"""
    print("[2/4] 安装依赖与项目（版本以 pyproject.toml 为准）……")
    result = subprocess.run(
        [str(python), "-m", "pip", "install", "-e", "."],
        cwd=PROJECT_ROOT,
    )
    if result.returncode != 0:
        raise SystemExit(
            "安装失败。请检查网络后重试，或手工执行以查看详细错误：\n"
            f"    {python} -m pip install -e {PROJECT_ROOT}"
        )


def write_launcher(python: Path) -> Path | None:
    """在 ~/.local/bin 写入固定指向 venv 的启动器。"""
    if os.name == "nt":
        print("[3/4] Windows 平台跳过启动器写入；请改用 scripts/build.py 打包")
        return None

    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    launcher = bin_dir / LAUNCHER_NAME
    launcher.write_text(
        _LAUNCHER_TEMPLATE.format(root=PROJECT_ROOT, python=python, name=LAUNCHER_NAME),
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    print(f"[3/4] 启动器已写入：{launcher}")
    return launcher


def verify(python: Path) -> bool:
    """验证 CLI 与 GUI 依赖在 venv 中确实可用。"""
    gui_probe = "from PyQt6.QtWidgets import QPushButton"
    checks: list[tuple[str, list[str]]] = [
        ("命令行", [str(python), "-m", "ui.cli", "--help"]),
        ("图形界面依赖", [str(python), "-c", gui_probe]),
    ]
    all_ok = True
    for label, cmd in checks:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"      {label}：OK")
            continue
        all_ok = False
        print(f"      {label}：失败")
        detail = (result.stderr or result.stdout).strip().splitlines()
        if detail:
            print(f"        {detail[-1]}")
    return all_ok


def _warn_if_not_on_path(directory: Path) -> None:
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    if str(directory) not in path_dirs:
        print(f"      注意：{directory} 不在 PATH 中，请先把它加入 PATH。")


def cmd_install() -> int:
    """创建 venv、安装项目，并写好全局启动器。"""
    print(f"VM-Tool 安装器\n      项目目录：{PROJECT_ROOT}")
    python = ensure_venv()
    install_project(python)
    launcher = write_launcher(python)

    print("[4/4] 验证安装：")
    ok = verify(python)
    if launcher is not None:
        _warn_if_not_on_path(launcher.parent)

    if ok:
        print("\n安装完成。之后直接使用：\n    vmtool --help\n    vmtool gui")
        return 0
    print("\n安装完成，但验证未全部通过，请查看上面的输出。")
    return 1


def cmd_install_completion(argv: list[str]) -> int:
    """输出 shell 补全脚本（绕过 shell 自动探测）。"""
    try:
        from typer.completion import get_completion_script
    except Exception as exc:
        print(f"补全生成失败: {exc}")
        return 1

    shell = argv[1] if len(argv) > 1 else "zsh"
    script = get_completion_script(
        prog_name=LAUNCHER_NAME,
        complete_var=f"_{LAUNCHER_NAME.upper()}_COMPLETE",
        shell=shell,
    )
    print(script)

    print("\n=== 补全安装说明 ===")
    if shell == "zsh":
        print("1. 将上述输出保存到 ~/.zsh/completions/_vmtool")
        print("2. 确保 ~/.zsh/completions 目录在你的 fpath 中")
        print("3. 重新启动 zsh 或执行 'source ~/.zshrc' 来激活补全")
    elif shell == "bash":
        print("1. 将上述输出保存到 ~/.bash_completion.d/vmtool")
        print("2. 执行 'source ~/.bash_completion.d/vmtool' 来激活补全")
    else:
        print(f"请将上述输出保存到适合 {shell} 的补全目录中")
    return 0


def main() -> int:
    """脚本入口：--install / --install-completion / 其余交给 Typer。"""
    argv = sys.argv[1:]
    if "--install" in argv:
        return cmd_install()
    if "--install-completion" in argv:
        return cmd_install_completion(argv)

    # 延迟导入：--install 时不需要加载全部运行时依赖
    from ui.cli.__main__ import app

    app()
    return 0


if __name__ == "__main__":
    sys.exit(main())
