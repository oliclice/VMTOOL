"""依赖声明一致性检查：代码实际 import 的第三方包必须被 pyproject 声明。

为什么需要这个检查
------------------
T10 独立验证发现：``ui/cli/__main__.py`` 在运行期路径里 ``from click.testing import
CliRunner``，而 ``click`` 从未出现在 pyproject.toml / requirements.txt 里；它能跑通
只是因为 quality extra 的 black 顺带装了 click —— 与最初的 P0-1（psutil 未声明导致
核心链路不可用）是同一类缺陷。人工审计会漏，所以这里做成**会失败**的可执行检查。

判据（有意从严）
----------------
1. **运行期代码**（``vmtool.py`` / ``app/`` / ``ui/`` / ``plugins/``）直接 import 的
   第三方顶层模块，必须由 ``[project].dependencies`` **直接**声明；仅由测试/质量 extra
   或传递依赖提供不算通过 —— 干净运行期安装（``pip install .``）会缺包。
2. **测试代码**（``tests/``）直接 import 的第三方顶层模块，必须由
   ``[project].dependencies`` 或 ``test`` extra 直接声明。
3. 判定用 ``importlib.metadata.packages_distributions()`` 做「import 名 → 发行版名」
   映射（如 ``pydantic_settings`` → ``pydantic-settings``、``PyQt6`` → ``PyQt6``）。

没有豁免名单：任何未声明项都必须修声明或改代码。
"""
from __future__ import annotations

import ast
import re
import sys
from importlib import metadata
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[2]
PYPROJECT = PROJECT_DIR / "pyproject.toml"

#: 项目自有顶层模块名（不算第三方）。
FIRST_PARTY = {"app", "ui", "plugins", "tests", "scripts", "main", "vmtool", "conftest"}

#: 解释器自带、但版本相关的模块名：tomllib 是 3.11+ 标准库，CI 用 3.10 时它不存在，
#: 会被 AST 扫到却不在 sys.stdlib_module_names 里 —— 这是解释器差异，不是第三方包。
STDLIB_BY_VERSION = {"tomllib"}

RUNTIME_FILES = [
    PROJECT_DIR / "vmtool.py",
    *sorted((PROJECT_DIR / "app").rglob("*.py")),
    *sorted((PROJECT_DIR / "ui").rglob("*.py")),
    *sorted((PROJECT_DIR / "plugins").rglob("*.py")),
]
TEST_FILES = sorted((PROJECT_DIR / "tests").rglob("*.py"))


# ── pyproject 解析（3.10 无 tomllib，故带定点回落解析器） ──────────────────────
def _parse_declarations_fallback(text: str) -> dict[str, list[str]]:
    """定点解析 [project].dependencies 与 [project.optional-dependencies].<group>。

    Python 3.10（CI 的解释器）没有 tomllib，这里只按本项目 pyproject 的写法取值；
    与 tomllib 路径的等价性由 test_fallback_parser_matches_tomllib 逐项比对。
    """
    sections: dict[str, list[str]] = {}
    header = ""
    current: str | None = None
    in_array = False
    for raw in text.splitlines():
        line = "" if raw.lstrip().startswith("#") else raw.split("#", 1)[0]
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("["):
            header = stripped.strip("[]").strip()
            current = None
            in_array = False
            continue
        if in_array:
            if stripped.startswith("]"):
                in_array = False
                current = None
                continue
            assert current is not None
            sections[current].extend(re.findall(r'"([^"]+)"', stripped))
            continue
        match = re.fullmatch(r"([A-Za-z0-9_-]+)\s*=\s*\[", stripped)
        if not match:
            continue
        key = match.group(1)
        if header == "project" and key == "dependencies":
            current = "runtime"
        elif header == "project.optional-dependencies":
            current = f"extra:{key}"
        else:
            current = None
        if current is not None:
            sections.setdefault(current, [])
            in_array = True
    return sections


def _declared_requirements(pyproject: Path = PYPROJECT) -> dict[str, list[str]]:
    """返回 {'runtime': [...], 'extra:test': [...], ...}（保持声明原样字符串）。"""
    text = pyproject.read_text(encoding="utf-8")
    try:
        import tomllib
    except ImportError:  # pragma: no cover - 仅在 Python 3.10（CI）走到
        return _parse_declarations_fallback(text)
    data = tomllib.loads(text)
    project = data["project"]
    declared = {"runtime": list(project.get("dependencies", []))}
    for group, items in project.get("optional-dependencies", {}).items():
        declared[f"extra:{group}"] = list(items)
    return declared


def _normalize(name: str) -> str:
    """PEP 503 规范化：小写 + 连续 [-_.] 折叠为单个 '-'。"""
    return re.sub(r"[-_.]+", "-", name.strip()).lower()


def _requirement_name(requirement: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
    assert match, f"无法解析依赖名: {requirement!r}"
    return match.group(1)


def _declared_names(
    declared: dict[str, list[str]], groups: tuple[str, ...]
) -> set[str]:
    names: set[str] = set()
    for group in groups:
        names.update(
            _normalize(_requirement_name(req)) for req in declared.get(group, [])
        )
    return names


def _third_party_imports(files: list[Path]) -> dict[str, set[str]]:
    """扫描文件，返回 {第三方顶层模块名: {出现该 import 的文件}}。"""
    stdlib = set(sys.stdlib_module_names) | STDLIB_BY_VERSION
    found: dict[str, set[str]] = {}
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module.split(".")[0]]
            for name in names:
                if name in stdlib or name in FIRST_PARTY:
                    continue
                found.setdefault(name, set()).add(str(path.relative_to(PROJECT_DIR)))
    return found


def _providing_distributions(module: str) -> set[str]:
    """import 名 → 发行版名（规范化后）。"""
    mapping = metadata.packages_distributions()
    return {_normalize(dist) for dist in mapping.get(module, [])}


def _undeclared_imports(
    files: list[Path], declared: set[str]
) -> dict[str, tuple[set[str], set[str]]]:
    """返回 {模块名: (提供它的发行版, 出现文件)}，即声明集合覆盖不到的第三方 import。"""
    offenders: dict[str, tuple[set[str], set[str]]] = {}
    for module, where in sorted(_third_party_imports(files).items()):
        candidates = _providing_distributions(module) | {_normalize(module)}
        if candidates & declared:
            continue
        offenders[module] = (candidates, where)
    return offenders


def _format(offenders: dict[str, tuple[set[str], set[str]]]) -> str:
    lines = ["存在未被声明覆盖的第三方 import（干净安装下会 ImportError）："]
    for module, (dists, where) in offenders.items():
        lines.append(
            f"  - import {module}  （发行版: {', '.join(sorted(dists)) or '未知'}）"
        )
        lines.append(f"    位置: {', '.join(sorted(where))}")
    return "\n".join(lines)


# ── 检查本体 ─────────────────────────────────────────────────────────────────
def test_runtime_imports_are_declared_runtime_dependencies():
    """运行期代码的 import 必须在 [project].dependencies 里直接声明。"""
    declared = _declared_names(_declared_requirements(), ("runtime",))
    offenders = _undeclared_imports(RUNTIME_FILES, declared)
    assert not offenders, _format(offenders)


def test_test_imports_are_declared_in_runtime_or_test_extra():
    """测试代码的 import 必须由运行期依赖或 test extra 声明。"""
    declared = _declared_names(_declared_requirements(), ("runtime", "extra:test"))
    offenders = _undeclared_imports(TEST_FILES, declared)
    assert not offenders, _format(offenders)


def test_click_is_declared_as_runtime_dependency():
    """回归固定 T10-F1：ui/cli 运行期使用 click.testing，故 click 必须是运行期依赖。

    typer 0.27 起把 click vendor 进 ``typer._click``，其 Requires-Dist 不再包含 click，
    因此这条 import 只能由我们自己声明。
    """
    declared = _declared_names(_declared_requirements(), ("runtime",))
    assert "click" in declared, "click 必须出现在 [project].dependencies（运行期依赖）"
    assert "click" not in _declared_names(
        _declared_requirements(), ("extra:test",)
    ), "click 不是测试专用依赖：ui/cli/__main__.py 的运行期路径也在用"


def test_declared_versions_are_pinned_for_ci_critical_packages():
    """声明里必须能解析出版本约束（防止把依赖写成空字符串之类的低级错误）。"""
    for group, requirements in _declared_requirements().items():
        for requirement in requirements:
            assert _requirement_name(
                requirement
            ), f"{group} 中存在无法解析的依赖项: {requirement!r}"
            assert any(
                op in requirement for op in ("=", ">", "<", "~")
            ), f"{group} 中的 {requirement!r} 未带版本约束"


@pytest.mark.skipif(
    "tomllib" not in sys.stdlib_module_names,
    reason="本机无 tomllib（3.10），回落解析器就是唯一路径，无需比对",
)
def test_fallback_parser_matches_tomllib():
    """3.10 回落解析器与 tomllib 的解析结果必须逐项一致（保证 CI 与本机同判据）。"""
    text = PYPROJECT.read_text(encoding="utf-8")
    fallback = _parse_declarations_fallback(text)

    import tomllib

    data = tomllib.loads(text)
    expected = {"runtime": list(data["project"].get("dependencies", []))}
    for group, items in data["project"].get("optional-dependencies", {}).items():
        expected[f"extra:{group}"] = list(items)

    assert {key: sorted(value) for key, value in fallback.items()} == {
        key: sorted(value) for key, value in expected.items()
    }
