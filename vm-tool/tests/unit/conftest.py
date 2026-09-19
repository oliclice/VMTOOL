"""tests/unit 公共隔离装置（T24：从 3 个测试模块的内联装置上移而来）

目标：**tests/unit 下的任何用例都不可能读写真实用户库**
（``~/.config/vm-tool/vm_tool.db``），也不会带着上一个用例遗留的全局缓存状态开跑。

三道边界，由外到内：

1. **公共哨兵**：``app.dal.database._get_engine`` / ``_get_session_factory`` 换成
   路径感知守卫——目标仍是真实用户库时抛 ``AssertionError``；被 ``temp_db`` 夹具
   重定向到 ``tmp_path`` 时放行（``test_concurrent_writes`` /
   ``test_session_ownership`` / ``test_thread_service_ownership`` /
   ``test_cache_invalidation`` 都依赖这一点）。
2. **导入期绑定**（T14 发现的缺口）：``app/dal/migration.py`` 与 ``app/dal/init_db.py``
   用 ``from app.dal.database import _get_engine / _get_session_factory`` 在**导入期
   按名绑定**，直接调用会绕过第 1 道。夹具安装时扫描 ``sys.modules``，把 app/ui/tests
   模块里的同名属性一并换成哨兵（``app/dal/__init__.py`` 的再导出同样覆盖）。
   夹具安装**之后**才首次导入的模块，其绑定读到的已经是哨兵，无需额外处理。
3. **收口点**：``app.dal.database.create_engine`` 本身也换成路径感知守卫。任何指向用户库
   的引擎创建都逃不过它 —— 包括「用例自己把 ``_get_engine`` 换回原函数」这种写法
   （见 ``test_cache_invalidation.real_temp_db``）。

自检：``tests/unit/test_isolation_guard.py``。把本文件移走，该模块必须失败。
"""
import os
import sys

import pytest

from app.core.cache import cache
from app.dal import database

#: 三个哨兵函数的 ``__name__``：自检用例据此判断隔离装置是否已武装。
GUARD_NAME = "_guard_real_database_access"

#: 判定「用户库」的路径基准：默认用户库 + conftest 导入时生效的路径。
_USER_DB_PATHS = frozenset(
    {
        os.path.realpath(database.DEFAULT_DATABASE_PATH),
        os.path.realpath(database.get_database_path()),
    }
)

_ORIGINAL_GET_ENGINE = database._get_engine
_ORIGINAL_GET_SESSION_FACTORY = database._get_session_factory
_ORIGINAL_CREATE_ENGINE = database.create_engine

_FENCE_TEMPLATE = (
    "单元测试禁止访问真实数据库（来源：{origin}，目标：{target}）。"
    "tests/unit/conftest.py 的隔离装置只放行重定向到 tmp_path 的临时库："
    "需要真实会话的用例请用 temp_db 夹具 monkeypatch app.dal.database 的 "
    "_database_path/_engine/_SessionFactory；其余用例请 patch 被测模块的 get_db，"
    "或直接注入桩 Session。"
)


def _fence(origin: str, target: str) -> None:
    """抛出隔离违规错误。"""
    raise AssertionError(_FENCE_TEMPLATE.format(origin=origin, target=target))


def _current_path_is_user_db() -> bool:
    return os.path.realpath(database.get_database_path()) in _USER_DB_PATHS


def _url_is_user_db(url: object) -> bool:
    text = str(url)
    prefix = "sqlite:///"
    if not text.startswith(prefix):
        return False
    return os.path.realpath(text[len(prefix) :]) in _USER_DB_PATHS


def _cached_engine_is_user_db() -> bool:
    """已缓存的引擎是否仍指向用户库（用例只改路径、没清缓存时会踩到）。"""
    engine = database._engine
    if engine is None:
        return False
    try:
        return _url_is_user_db(engine.url)
    except Exception:  # pragma: no cover - 引擎对象异常时按“不可信”处理
        return True


def _assert_not_user_db(origin: str, target: str) -> None:
    if _current_path_is_user_db():
        _fence(origin, f"{target}（当前数据库路径 {database.get_database_path()}）")
    if _cached_engine_is_user_db():
        _fence(origin, f"{target}（已缓存引擎指向用户库）")


def _guard_get_engine():
    """路径感知的引擎守卫：临时库放行，用户库拦下。"""
    _assert_not_user_db("app.dal.database._get_engine()", "创建引擎")
    return _ORIGINAL_GET_ENGINE()


_guard_get_engine.__name__ = GUARD_NAME


def _guard_get_session_factory():
    """路径感知的会话工厂守卫。"""
    _assert_not_user_db("app.dal.database._get_session_factory()", "创建会话工厂")
    return _ORIGINAL_GET_SESSION_FACTORY()


_guard_get_session_factory.__name__ = GUARD_NAME


def _guard_create_engine(url, *args, **kwargs):
    """收口点守卫：不给用户库建引擎，其余（tmp_path 等）照常。"""
    if _url_is_user_db(url):
        _fence("app.dal.database.create_engine(url)", f"引擎 URL {url}")
    return _ORIGINAL_CREATE_ENGINE(url, *args, **kwargs)


_guard_create_engine.__name__ = GUARD_NAME

#: 需要在其它模块里一并改写的「导入期按名绑定」。
_BOUND_NAMES = {
    "_get_engine": (_ORIGINAL_GET_ENGINE, _guard_get_engine),
    "_get_session_factory": (_ORIGINAL_GET_SESSION_FACTORY, _guard_get_session_factory),
}

_REWRITTEN: list[str] = []


def _rewrite_import_time_bindings(monkeypatch) -> list[str]:
    """把已导入模块里按名绑定的 DAL 引擎/会话工厂换成哨兵。"""
    rewritten: list[str] = []
    for module in list(sys.modules.values()):
        if module is None or module is database:
            continue
        module_name = getattr(module, "__name__", "")
        if not module_name.startswith(("app.", "ui.", "tests.")):
            continue
        for attr, (original, guard) in _BOUND_NAMES.items():
            if getattr(module, attr, None) is original:
                monkeypatch.setattr(module, attr, guard)
                rewritten.append(f"{module_name}.{attr}")
    return rewritten


@pytest.fixture(autouse=True)
def _isolate_db_and_cache(monkeypatch):
    """隔离真实用户库与全局缓存（tests/unit 下所有用例自动生效）。"""
    cache.clear()
    monkeypatch.setattr(database, "create_engine", _guard_create_engine)
    monkeypatch.setattr(database, "_get_engine", _guard_get_engine)
    monkeypatch.setattr(database, "_get_session_factory", _guard_get_session_factory)
    rewritten = _rewrite_import_time_bindings(monkeypatch)
    _REWRITTEN.clear()
    _REWRITTEN.extend(rewritten)
    yield
    cache.clear()


@pytest.fixture
def isolation_probe(_isolate_db_and_cache):
    """供 tests/unit/test_isolation_guard.py 自检：暴露哨兵状态与原始入口。"""
    return {
        "guard_name": GUARD_NAME,
        "user_db_paths": sorted(_USER_DB_PATHS),
        "rewritten_bindings": list(_REWRITTEN),
        "original_get_engine": _ORIGINAL_GET_ENGINE,
    }
