#!/usr/bin/env python3
"""VM-TOOL 命令行工具入口"""
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

# 依赖清单的唯一来源是 pyproject.toml [project].dependencies。
# 下面的兜底清单仅在 vm-tool 自身尚未安装（读不到发行版元数据）时使用，
# 必须与 pyproject.toml [project].dependencies 保持逐项一致。
_FALLBACK_REQUIRED_DEPS = [
    "pydantic",
    "pydantic-settings",
    "sqlalchemy",
    "psutil",
    "typer",
    "click",
    "rich",
    "PyQt6",
    "PyQt6-Qt6",
    "PyQt6-Charts",
    "PyQt6-Charts-Qt6",
]


def _base_requirement_name(requirement: str) -> str | None:
    """从 PEP 508 依赖串中取出发行包名。

    extras 依赖（如 ``pytest==7.4.3; extra == "test"``）不是运行时基础依赖，
    返回 None 以便调用方过滤。
    """
    import re

    spec, _, marker = requirement.partition(";")
    if "extra" in marker:
        return None
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", spec)
    return match.group(1) if match else None


def get_required_deps() -> list[str]:
    """返回 --install 需要检查的依赖包名。

    从已安装发行版元数据 ``importlib.metadata.requires("vm-tool")`` 派生，
    与 pyproject.toml 共用一份清单；vm-tool 未安装时退回与 pyproject.toml
    [project].dependencies 一致的硬编码清单。
    """
    import importlib.metadata

    try:
        requirements = importlib.metadata.requires("vm-tool") or []
    except importlib.metadata.PackageNotFoundError:
        requirements = []
    names = [name for name in map(_base_requirement_name, requirements) if name]
    return names or list(_FALLBACK_REQUIRED_DEPS)


if __name__ == "__main__":
    # 检查是否执行 --install 命令
    if "--install" in sys.argv:
        # 需要检查的依赖（派生自 pyproject.toml [project].dependencies）
        REQUIRED_DEPS = get_required_deps()

        def _check_dep(pkg_name: str) -> bool:
            """检查依赖是否已安装"""
            import importlib.metadata

            try:
                importlib.metadata.distribution(pkg_name)
                return True
            except importlib.metadata.PackageNotFoundError:
                return False

        # 1) 检测缺失的依赖
        missing = [p for p in REQUIRED_DEPS if not _check_dep(p)]

        if missing:
            logger.info(f"检测到缺失依赖: {', '.join(missing)}")
            logger.info("正在安装缺失依赖...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", *missing],
                cwd=sys.path[0],
                capture_output=False,
            )
            if result.returncode != 0:
                logger.error("依赖安装失败")
                sys.exit(1)
        else:
            logger.info("所有依赖已安装，跳过依赖安装")

        # 2) 以 editable 模式安装项目本身（--no-deps 跳过依赖解析）
        logger.info("正在安装项目...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", ".", "--no-deps"],
            cwd=sys.path[0],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("项目安装成功！")
        else:
            logger.error(f"项目安装失败: {result.stderr}")

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
                prog_name=prog_name, complete_var=complete_var, shell=shell
            )

            # 输出补全脚本到标准输出
            logger.info(completion_script)

            # 打印安装说明
            logger.info("\n=== 补全安装说明 ===")
            if shell == "zsh":
                logger.info("1. 将上述输出保存到 ~/.zsh/completions/_vmtool")
                logger.info("2. 确保 ~/.zsh/completions 目录在你的 fpath 中")
                logger.info("3. 重新启动 zsh 或执行 'source ~/.zshrc' 来激活补全")
            elif shell == "bash":
                logger.info("1. 将上述输出保存到 ~/.bash_completion.d/vmtool")
                logger.info(
                    "2. 重新启动 bash 或执行 "
                    "'source ~/.bash_completion.d/vmtool' 来激活补全"
                )
            else:
                logger.info(f"请将上述输出保存到适合 {shell} 的补全目录中")

            sys.exit(0)
        except Exception as e:
            logger.error(f"补全生成失败: {e}")
            sys.exit(1)

    # 执行原有的命令（延迟导入，避免 --install 时加载全部依赖）
    from ui.cli.__main__ import app

    app()
