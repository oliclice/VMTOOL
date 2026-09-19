"""GUI 工作线程的服务工厂（T19）。

背景
----
QThread 里若使用**主线程创建的长驻服务实例**，等于跨线程共用同一个 SQLAlchemy
``Session``。``Session`` 不是线程安全的，并发写会**静默丢写**（T8 实测：共享一个
``DictService`` 并发 ``add_word``，8 线程 ×20 条只落库 22/160，且伴随
``This session is provisioning a new connection; concurrent operations are not
permitted`` / ``commit() is already in progress``）。

约定（防复发，由 ``tests/unit/test_gui_thread_conventions.py`` 静态强制）
--------------------------------------------------------------------
1. ``ui/gui/threads/`` 下的线程类**不得**接受外部注入的长驻服务实例——构造签名里
   不出现 ``dict_service`` / ``filter_service`` / ``weight_calc`` / ``stats_service``
   这类参数；
2. 需要在工作线程访问数据库的线程，必须在 ``run()`` 内用本模块的 ``*_scope()``
   工厂创建服务，并在 ``with`` 退出时释放（谁创建、谁关闭）。

这与 T5 建立的显式所有权模型一致：``database.get_db()`` 是显式会话工厂，调用方
负责 ``close()``。本模块只是把这个责任搬进工作线程，**没有**引入 scoped_session、
线程局部会话代理之类的隐式会话魔法。
"""
from __future__ import annotations

import contextlib
import threading
from collections.abc import Callable, Iterator

from app.dal.database import get_db
from app.services.dict import DictService
from app.services.filter import FilterService
from app.services.weight import WeightCalculator

# ── 统计缓存失效回调 ──────────────────────────────────────────────
# GUI 主线程启动时注册。典型实参是 ``StatsService.clear_cache`` —— 注意它是**绑定
# 方法**：``invalidator.__self__`` 正是持有主线程会话的那个 StatsService 实例
# （``StatsService.__init__`` 里 ``self.db = get_db()``）。它之所以能被工作线程调用，
# 前提是**被调方法本身不触碰 Session**：``clear_cache`` 只把 ``_stats_cache`` /
# ``_cache_timestamp`` 两个内存属性置空。一旦换成会访问 ``self.db`` / ``self.repo``
# 的方法，就等于把主线程会话交给工作线程使用 —— 正是 T19 要消除的静默丢写缺陷。
# 因此注册时会做一次防御性检查（见 ``register_stats_cache_invalidator``）。
_stats_cache_invalidator: Callable[[], None] | None = None
_registry_lock = threading.Lock()

# 允许注册的方法名白名单：必须是不触碰 Session 的纯内存失效操作
_SESSION_FREE_INVALIDATOR_METHODS = frozenset({"clear_cache"})
# 方法体的名字表里出现这些名字，即判定为「可能触碰会话」
_SESSION_ATTRIBUTE_NAMES = frozenset({"db", "repo", "session", "_session"})


def _method_touches_session(func: object) -> bool:
    """粗粒度静态判定：方法体的名字表里是否出现会话属性（db / repo / session）。

    只能看到直接名字引用；透过 helper 间接访问 ``self.db`` 的情形看不到。故这是
    **防御性检查**，真正的约束是模块约定 + 评审。无法判定时（无 ``__code__``，例如
    内置可调用对象）一律放行，避免误伤。
    """
    code = getattr(func, "__code__", None)
    if code is None:
        return False
    return bool(_SESSION_ATTRIBUTE_NAMES.intersection(code.co_names))


def register_stats_cache_invalidator(invalidator: Callable[[], None] | None) -> None:
    """由 GUI 主线程注册统计缓存失效回调（幂等，重复注册即覆盖）。

    绑定方法必须通过安全检查：方法名在白名单内，且方法体不引用会话属性；否则抛
    ``ValueError``。这类回调会在**工作线程**里执行，若它触碰 Session，就等于把主线程
    的会话交给工作线程使用。

    已知边界：普通函数 / lambda 没有 ``__self__``，检查看不到其闭包内容（例如
    ``lambda: stats_service.session_bound_method()`` 仍可能越过检查）。彻底方案是在
    服务层提供一个**不依赖会话**的静态失效入口（属 app/services，不在本任务范围内，
    已作为建议上报）。
    """
    global _stats_cache_invalidator
    if invalidator is not None:
        owner = getattr(invalidator, "__self__", None)
        if owner is not None:
            func = getattr(invalidator, "__func__", invalidator)
            name = getattr(func, "__name__", "")
            if name not in _SESSION_FREE_INVALIDATOR_METHODS or _method_touches_session(
                func
            ):
                raise ValueError(
                    "统计缓存失效回调必须是「不触碰 Session 的纯内存操作」："
                    f"{type(owner).__name__}.{name} 不在白名单 "
                    f"{sorted(_SESSION_FREE_INVALIDATOR_METHODS)} 中，"
                    f"或方法体引用了会话属性 {sorted(_SESSION_ATTRIBUTE_NAMES)}。"
                    "该回调会在工作线程里执行，把持有主线程会话的服务方法当回调跨线程"
                    "使用正是 T19 要消除的缺陷；如需新的失效入口，请在服务层提供不依赖"
                    "会话的静态方法。"
                )
    with _registry_lock:
        _stats_cache_invalidator = invalidator


def get_stats_cache_invalidator() -> Callable[[], None] | None:
    """取出当前注册的统计缓存失效回调（未注册时为 None）。"""
    with _registry_lock:
        return _stats_cache_invalidator


# ── 线程私有服务 ──────────────────────────────────────────────────
def create_dict_service() -> DictService:
    """在**当前线程**内新建 DictService，并接回统计缓存失效回调。"""
    return DictService(on_data_changed=get_stats_cache_invalidator())


@contextlib.contextmanager
def dict_service_scope() -> Iterator[DictService]:
    """工作线程内自持 DictService：创建于当前线程，退出时 close（含异常路径）。"""
    service = create_dict_service()
    try:
        yield service
    finally:
        service.close()


@contextlib.contextmanager
def weight_calculator_scope() -> Iterator[WeightCalculator]:
    """工作线程内自持 WeightCalculator。

    ``WeightCalculator`` 自身没有 ``close()``，故按 T5 的显式所有权模型由本工厂创建
    会话并负责关闭。
    """
    db = get_db()
    try:
        yield WeightCalculator(db=db)
    finally:
        db.close()


@contextlib.contextmanager
def filter_service_scope() -> Iterator[FilterService]:
    """工作线程内自持 FilterService（同理：会话由工厂创建，工厂负责关闭）。"""
    db = get_db()
    try:
        yield FilterService(db=db)
    finally:
        db.close()
