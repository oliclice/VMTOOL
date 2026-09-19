"""隔离装置自检（T24）：conftest.py 的哨兵必须真的武装，且区分得出来

**区分力证据的载体**：把 ``tests/unit/conftest.py`` 移走再跑本模块，
第一个用例 ``test_sentinel_is_armed`` 必须失败。其余用例都先核对哨兵函数名、
再走封锁路径，所以「未武装」时它们会在断言处停下，**不会真的连上用户库**。

三道边界各有一条用例，另加两条「不过度封锁」用例（tmp_path 临时库仍可用）
与三条缓存清理用例（用例之间不串味）。
"""
import importlib
import sys

import pytest

from app.core.cache import cache
from app.dal import database, init_db, migration
from app.dal.models import Word


def _armed(func, probe) -> bool:
    """哨兵是否已武装（按函数名判定）。未武装时用例必须停在这里，不许走封锁路径。"""
    return getattr(func, "__name__", "") == probe["guard_name"]


def test_sentinel_is_armed(isolation_probe):
    """三道边界的哨兵都已安装；conftest.py 缺失时本用例首先失败。"""
    assert _armed(database._get_engine, isolation_probe)
    assert _armed(database._get_session_factory, isolation_probe)
    assert _armed(database.create_engine, isolation_probe)


def test_real_database_session_is_blocked(isolation_probe):
    """第 1 道：不重定向路径时，任何会话工厂调用都被拦下。"""
    assert _armed(database._get_engine, isolation_probe), "哨兵未武装：已中止"
    with pytest.raises(AssertionError, match="禁止访问真实数据库"):
        database.get_db()


def test_explicit_user_db_path_is_blocked(isolation_probe, monkeypatch):
    """第 1 道：用例显式把路径指回用户库，同样被拦（路径由用例给出，无副作用）。"""
    monkeypatch.setattr(database, "_database_path", isolation_probe["user_db_paths"][0])
    monkeypatch.setattr(database, "_engine", None)
    monkeypatch.setattr(database, "_SessionFactory", None)
    with pytest.raises(AssertionError, match="禁止访问真实数据库"):
        database._get_engine()


def test_create_engine_guard_blocks_user_db(isolation_probe):
    """第 3 道：收口点不给用户库建引擎。（直接传 URL，不依赖任何哨兵是否武装）"""
    url = f"sqlite:///{isolation_probe['user_db_paths'][0]}"
    with pytest.raises(AssertionError, match="禁止访问真实数据库"):
        database.create_engine(url)


def test_original_engine_factory_cannot_bypass_the_fence(isolation_probe, monkeypatch):
    """第 3 道：即使用例把 ``_get_engine`` 换回原函数（``real_temp_db`` 的写法）
    且**没有**重定向路径，收口点仍拦住用户库。"""
    monkeypatch.setattr(database, "_get_engine", isolation_probe["original_get_engine"])
    monkeypatch.setattr(database, "_engine", None)
    monkeypatch.setattr(database, "_SessionFactory", None)
    with pytest.raises(AssertionError, match="禁止访问真实数据库"):
        database._get_engine()


def test_import_time_bindings_are_rewritten(isolation_probe):
    """第 2 道（T14 缺口）：migration.py / init_db.py 的导入期按名绑定已被改写。"""
    assert _armed(init_db._get_engine, isolation_probe), "哨兵未武装：已中止"
    assert _armed(migration._get_session_factory, isolation_probe)
    rewritten = isolation_probe["rewritten_bindings"]
    assert "app.dal.init_db._get_engine" in rewritten
    assert "app.dal.migration._get_session_factory" in rewritten
    with pytest.raises(AssertionError, match="禁止访问真实数据库"):
        init_db._get_engine()
    with pytest.raises(AssertionError, match="禁止访问真实数据库"):
        migration._get_session_factory()


def test_late_import_binds_an_armed_sentinel(isolation_probe):
    """夹具安装之后才首次导入的模块，导入期绑定读到的已经是哨兵。"""
    sys.modules.pop("app.dal.init_db", None)
    late = importlib.import_module("app.dal.init_db")
    assert getattr(late._get_engine, "__name__", "") == isolation_probe["guard_name"]
    with pytest.raises(AssertionError, match="禁止访问真实数据库"):
        late._get_engine()


def test_tmp_path_database_still_works(tmp_path, monkeypatch):
    """不过度封锁：指向 tmp_path 的临时库仍可建表 / 写 / 读。"""
    db_path = tmp_path / "isolation_probe.db"
    monkeypatch.setattr(database, "_database_path", str(db_path))
    monkeypatch.setattr(database, "_engine", None)
    monkeypatch.setattr(database, "_SessionFactory", None)
    engine = database._get_engine()
    database.Base.metadata.create_all(bind=engine)
    db = database.get_db()
    try:
        db.add(Word(word="隔离探针", code="gltz", weight=1.0))
        db.commit()
        assert db.query(Word).count() == 1
    finally:
        db.close()


def test_global_cache_is_empty_at_test_start():
    """缓存清理：上一个用例写入的键不得留到本用例（顺序：本条 → 下条写入）。"""
    assert cache.get("t24-cache-probe") is None


def test_global_cache_works_within_a_test():
    cache.set("t24-cache-probe", 1)
    assert cache.get("t24-cache-probe") == 1


def test_global_cache_is_cleared_again_for_the_next_test():
    """若上一条写入的键还在，说明 autouse 装置没有按用例清空缓存。"""
    assert cache.get("t24-cache-probe") is None
