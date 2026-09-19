"""GUI 工作线程的静态约定检查 + 信号契约运行时用例（T19 防复发，T25 补强）。

只修当前的接线点、不留约束，下一个人新增线程时还会重犯。因此把约定写成可执行的检查：

规则 1（签名）  ``*Thread`` 类构造签名不得出现服务实例参数（``dict_service`` /
                ``filter_service`` / ``weight_calc`` / ``stats_service`` …）；
规则 2（归属）  线程类内不得出现 ``self.<服务>``（含赋值与读取）；
规则 3（工厂）  自定义 ``run()`` 的线程类必须用 ``service_factory`` 的 ``*_scope()``
                创建服务（在 with 中创建 + 释放）；
规则 4（构造点）``ui/gui/`` 下任何 ``*Thread(...)`` 构造都不得传入服务实例：既看
                ``self.<服务>`` 这类属性实参，也看**裸名字**实参（该名字若在本文件里由
                ``X = DictService(...)`` / ``X = get_db()`` 之类调用赋值，
                或在服务名单里，即判失败）；
规则 5（信号）  方法体里 ``self.<name>.emit(...)`` 的 ``<name>`` 必须是本类/基类声明的
                ``pyqtSignal``，或是 QThread/QObject 内建信号（started/finished/…）。
                T25 的教训：``calculate_weight_thread.py`` 在 T19 重构中丢了三个类级信号
                声明，而 ``run()`` 仍在 emit —— ``pyqt_app`` 接线时 AttributeError，
                「计算权重」入口整条不可用；当时已有的 4 条规则与全部用例都没抓到它。

覆盖边界与已知漏报（显式列出，不掩饰）
--------------------------------------
* 规则 1–3 的扫描根已从 ``ui/gui/threads/`` 扩到 ``ui/gui/``，按 ``*Thread`` 基类筛类。
  当前仓库所有 QThread 子类都在 ``ui/gui/threads/``
  （实测 ``grep -rn "^class .*Thread" ui/gui`` 在包外无命中），故扩容不改变既有结论，
  只是防止将来把线程类挪到别处时漏检。
* 规则 4 只能看实参的**语法形态**：经局部变量中转、字典取值、工厂返回值等方式传入服务
  实例时看不到（静态检查固有边界）。本版比 T19 多了裸名字判定，覆盖 ``Thread(svc)``。
* 规则 5 只识别 ``self.<name>.emit`` 这一形态；
  ``getattr(self, name).emit``、先把信号赋给局部变量再 emit 的写法看不到。
* 规则 3 只要求 ``run()`` 里出现过 ``*_scope()`` 的 with，不保证覆盖所有数据库访问点。
* 运行期兜底：``tests/unit/test_thread_service_ownership.py`` 用真实临时库断言
  「每线程独立会话、落库数不丢」；本模块末尾的运行时用例固定 ``CalculateWeightThread``
  的信号契约。
"""
import ast
import contextlib
import pathlib

from PyQt6.QtCore import pyqtBoundSignal, pyqtSignal

GUI_ROOT = pathlib.Path(__file__).resolve().parents[2] / "ui" / "gui"
THREADS_DIR = GUI_ROOT / "threads"

# 会被误当作「长驻服务实例」注入的参数/属性名
SERVICE_NAMES = {
    "dict_service",
    "filter_service",
    "weight_calc",
    "weight_calculator",
    "stats_service",
}
# 允许用来在工作线程内创建服务的工厂
SCOPE_FACTORIES = {
    "dict_service_scope",
    "filter_service_scope",
    "weight_calculator_scope",
}
# 构造这些对象的结果被视为「服务/会话」
SERVICE_CONSTRUCTORS = {
    "DictService",
    "FilterService",
    "WeightCalculator",
    "StatsService",
    "get_db",
    "get_session",
}
# QThread / QObject 内建信号：不需要在类里声明
BUILTIN_SIGNALS = {"started", "finished", "destroyed", "objectNameChanged"}


def _parse(path: pathlib.Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _iter_py(root: pathlib.Path):
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _args(func: ast.FunctionDef) -> set:
    args = (
        list(func.args.posonlyargs) + list(func.args.args) + list(func.args.kwonlyargs)
    )
    return {a.arg for a in args} - {"self", "cls"}


def _class_bases(cls: ast.ClassDef) -> set:
    names = set()
    for base in cls.bases:
        if isinstance(base, ast.Name):
            names.add(base.id)
        elif isinstance(base, ast.Attribute):
            names.add(base.attr)
    return names


def _thread_classes(root: pathlib.Path = GUI_ROOT):
    """产出 ``(path, cls)``：扫描根内所有以 ``*Thread`` 为基类的类。"""
    for path in _iter_py(root):
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and any(
                b.endswith("Thread") for b in _class_bases(node)
            ):
                yield path, node


def _signal_registry(root: pathlib.Path = GUI_ROOT):
    """``{类名: {"signals": {...}, "bases": {...}}}`` —— 支持跨文件解析基类信号。"""
    registry: dict = {}
    for path in _iter_py(root):
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            signals = {
                item.targets[0].id
                for item in node.body
                if isinstance(item, ast.Assign)
                and len(item.targets) == 1
                and isinstance(item.targets[0], ast.Name)
                and isinstance(item.value, ast.Call)
                and getattr(item.value.func, "id", None) == "pyqtSignal"
            }
            entry = registry.setdefault(node.name, {"signals": set(), "bases": set()})
            entry["signals"] |= signals
            entry["bases"] |= _class_bases(node)
    return registry


def _declared_signals(cls_name: str, registry, _seen=None) -> set:
    """本类 + 基类（传递闭包）声明的信号名。"""
    _seen = _seen if _seen is not None else set()
    if cls_name in _seen:
        return set()
    _seen.add(cls_name)
    entry = registry.get(cls_name)
    if not entry:
        return set()
    names = set(entry["signals"])
    for base in entry["bases"]:
        names |= _declared_signals(base, registry, _seen)
    return names


def _service_like_names(tree: ast.Module) -> set:
    """文件内「疑似服务/会话」的名字。

    服务名单 + 由服务构造器 / ``get_db()`` 赋值得到的名字。
    """
    names = set(SERVICE_NAMES)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not isinstance(node.value, ast.Call):
            continue
        func = node.value.func
        called = (
            func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        )
        if called in SERVICE_CONSTRUCTORS or called == "next":
            names.add(target.id)
    return names


def test_thread_classes_do_not_accept_injected_services():
    """规则 1：``*Thread`` 类构造签名里不得出现服务实例参数。"""
    violations = []
    for path, cls in _thread_classes():
        for item in cls.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                bad = _args(item) & SERVICE_NAMES
                if bad:
                    violations.append(
                        f"{path.name}:{cls.name}.__init__ 注入 {sorted(bad)}"
                    )
    assert not violations, (
        "工作线程不得接受外部注入的长驻服务实例，请改用 service_factory 的 scope：\n"
        + "\n".join(violations)
    )


def test_thread_classes_never_store_services_on_self():
    """规则 2：线程类内不得出现 ``self.<服务>``（含赋值与读取）。"""
    violations = []
    for path, cls in _thread_classes():
        for node in ast.walk(cls):
            if (
                isinstance(node, ast.Attribute)
                and node.attr in SERVICE_NAMES
                and isinstance(node.value, ast.Name)
                and node.value.id == "self"
            ):
                violations.append(f"{path.name}:{node.lineno} self.{node.attr}")
    assert not violations, (
        "线程不得把服务实例挂在 self 上（会重新变成跨线程共享会话）：\n"
        + "\n".join(violations)
    )


def test_custom_run_uses_service_scope_factory():
    """规则 3：自定义 ``run()`` 必须用 ``*_scope()`` 工厂创建并释放服务。"""
    violations = []
    for path, cls in _thread_classes():
        run = next(
            (i for i in cls.body if isinstance(i, ast.FunctionDef) and i.name == "run"),
            None,
        )
        if run is None:
            continue
        used = {
            call.func.id
            for with_node in ast.walk(run)
            if isinstance(with_node, ast.With)
            for item in with_node.items
            for call in [item.context_expr]
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
        }
        if not (used & SCOPE_FACTORIES):
            violations.append(f"{path.name}:{cls.name}.run 未使用 *_scope()")
    assert not violations, (
        "线程 run() 必须用 service_factory 的 *_scope() 取得服务"
        "（线程内创建 + 释放）：\n" + "\n".join(violations)
    )


def test_no_thread_construction_passes_a_service_instance():
    """规则 4：``ui/gui/`` 下任何 ``*Thread(...)`` 构造都不得传入服务实例。

    既查 ``self.<服务>`` 这类属性实参，也查裸名字实参
    （本文件中由服务构造器赋值得到的名字）。
    """
    violations = []
    for path in _iter_py(GUI_ROOT):
        tree = _parse(path)
        service_like = _service_like_names(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = (
                func.attr
                if isinstance(func, ast.Attribute)
                else getattr(func, "id", "")
            )
            if not (isinstance(name, str) and name.endswith("Thread")):
                continue
            if name == "QThread":  # 基类本身，不是我们接入的线程
                continue
            args = list(node.args) + [kw.value for kw in node.keywords]
            for arg in args:
                if isinstance(arg, ast.Attribute) and arg.attr in SERVICE_NAMES:
                    violations.append(
                        f"{path.relative_to(GUI_ROOT)}:{node.lineno} "
                        f"{name}(... {arg.attr} ...)"
                    )
                elif isinstance(arg, ast.Name) and arg.id in service_like:
                    violations.append(
                        f"{path.relative_to(GUI_ROOT)}:{node.lineno} "
                        f"{name}(... {arg.id} ...)"
                    )
    assert not violations, "构造线程时不得传入主线程的长驻服务实例：\n" + "\n".join(
        violations
    )


def test_threads_only_emit_declared_signals():
    """规则 5：``self.<name>.emit(...)`` 的 name 必须是已声明的 pyqtSignal 或内建信号。

    T25 的缺陷（``CalculateWeightThread`` 丢信号声明）正是这条规则要拦住的形态。
    """
    registry = _signal_registry()
    violations = []
    for path, cls in _thread_classes():
        declared = _declared_signals(cls.name, registry) | BUILTIN_SIGNALS
        for node in ast.walk(cls):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute) or func.attr != "emit":
                continue
            target = func.value
            if not (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            ):
                continue
            if target.attr not in declared:
                violations.append(
                    f"{path.name}:{node.lineno} self.{target.attr}.emit(...) —— "
                    f"{cls.name} 及其基类都没有声明 {target.attr} 信号"
                )
    assert not violations, (
        "线程 emit 了未声明的信号（调用方 connect 时会 AttributeError；"
        "T25 的 calculate_weight_thread 就是这样坏掉的）：\n" + "\n".join(violations)
    )


def test_calculate_weight_thread_declares_and_emits_signals(monkeypatch):
    """运行时契约（T25 回归）：三个信号必须由**本类**声明。

    并验证 ``run()`` 成功路径把 dict 载荷发到 ``finished``。

    缺信号时的表现：``self.progress.emit`` → AttributeError → 被 except 捕获后又
    ``self.error.emit`` → 再 AttributeError 逃出 run()，调用方连错误提示都收不到。
    """
    from ui.gui.threads import calculate_weight_thread as weight_mod

    cls = weight_mod.CalculateWeightThread
    for name in ("progress", "finished", "error"):
        assert name in cls.__dict__, (
            f"CalculateWeightThread 缺少类级信号声明 {name!r}"
            "（继承不到 QThread 的同名内建信号，pyqt_app 接线会 AttributeError）"
        )
        assert isinstance(cls.__dict__[name], pyqtSignal), f"{name} 不是 pyqtSignal"

    thread = cls()
    for name in ("progress", "finished", "error"):
        assert isinstance(getattr(thread, name), pyqtBoundSignal)

    seen: dict = {}
    thread.progress.connect(lambda p, m: seen.__setitem__("progress", (p, m)))
    thread.finished.connect(lambda payload: seen.__setitem__("finished", payload))
    thread.error.connect(lambda msg: seen.__setitem__("error", msg))

    class _StubCalculator:
        def recalculate_all_weights(self, progress_callback):
            progress_callback(42, "半数")
            return {"updated": 3, "total": 5}

    @contextlib.contextmanager
    def _stub_scope():
        yield _StubCalculator()

    # 线程模块里是 `from .service_factory import weight_calculator_scope`，
    # 因此要 patch 它的本地引用（模块级名字），而非 service_factory 内的同名函数
    monkeypatch.setattr(weight_mod, "weight_calculator_scope", _stub_scope)

    thread.run()  # 直接跑 run()，不依赖 Qt 事件循环；同线程 emit 走直连

    assert seen.get("finished") == {"updated": 3, "total": 5}
    assert seen.get("progress") == (42, "半数")
    assert "error" not in seen, f"成功路径不应触发 error：{seen.get('error')}"
