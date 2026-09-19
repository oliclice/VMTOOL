"""并发写库回归用例：多线程各持独立会话写不同词条（P1-2）

隔离约定：**不使用真实用户数据库**。本模块的夹具把 DAL 的模块全局
（``_database_path`` / ``_engine`` / ``_SessionFactory``）注入到 pytest 的
``tmp_path`` 临时库，测试结束由 monkeypatch 自动还原；建表与写入都发生在临时库上，
并且走真实的 ``Session`` / ``WordRepository`` 写路径（不是桩）。

模型约定（与 T5 一致）：``database.get_db()`` 是显式会话工厂——谁创建谁 ``close()``；
连接池为 NullPool，因此每个会话各自 checkout 一条连接，不再像 StaticPool 那样
全进程共用一条连接。
"""
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy.pool import NullPool

from app.dal import database as dbmod
from app.dal.models import Word
from app.dal.repositories import WordRepository

N_THREADS = 8
WORDS_PER_THREAD = 25


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """把 DAL 指向临时库文件（不触碰 ~/.config/vm-tool/vm_tool.db）。"""
    path = tmp_path / "concurrency.db"
    monkeypatch.setattr(dbmod, "_database_path", str(path))
    monkeypatch.setattr(dbmod, "_engine", None)
    monkeypatch.setattr(dbmod, "_SessionFactory", None)
    dbmod.Base.metadata.create_all(bind=dbmod._get_engine())
    assert dbmod.get_database_path() == str(path)
    return path


def _count_words() -> int:
    """用独立会话统计行数（调用方负责关闭）。"""
    db = dbmod.get_db()
    try:
        return db.query(Word).count()
    finally:
        db.close()


def test_engine_uses_null_pool_and_wal(temp_db):
    """连接模型与 SQLite PRAGMA：NullPool + journal_mode=wal + busy_timeout。"""
    engine = dbmod._get_engine()
    assert isinstance(
        engine.pool, NullPool
    ), "连接池必须是 NullPool：每会话独立连接，避免多线程共用一条连接"
    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA journal_mode").scalar() == "wal"
        assert conn.exec_driver_sql("PRAGMA busy_timeout").scalar() >= 30000


def test_concurrent_writes_all_persisted(temp_db):
    """N 个线程并发写不同词条：全部落库，且不出现 database is locked。"""
    errors = []
    barrier = threading.Barrier(N_THREADS)

    def worker(tid: int) -> None:
        db = dbmod.get_db()  # 每个线程一条独立会话（NullPool → 独立连接）
        try:
            barrier.wait(timeout=10)  # 尽量让写入真正重叠
            repo = WordRepository(db)
            for i in range(WORDS_PER_THREAD):
                repo.create(word=f"t{tid}-{i}", code=f"c{tid}-{i}", weight=1.0)
        except Exception as e:  # noqa: BLE001 - 收集任何线程内的失败用于断言
            errors.append(f"thread {tid}: {type(e).__name__}: {e}")
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=N_THREADS) as pool:
        list(pool.map(worker, range(N_THREADS)))

    assert errors == [], f"并发写库出现异常: {errors[:3]}"
    assert not any("locked" in e for e in errors)
    assert _count_words() == N_THREADS * WORDS_PER_THREAD


def test_concurrent_writers_with_concurrent_reader(temp_db):
    """WAL 下的读写并发：写线程运行时，读线程不得报 database is locked。"""
    errors = []
    stop = threading.Event()
    barrier = threading.Barrier(N_THREADS)
    reader_rounds = []

    def writer(tid: int) -> None:
        db = dbmod.get_db()
        try:
            barrier.wait(timeout=10)
            repo = WordRepository(db)
            for i in range(WORDS_PER_THREAD):
                repo.create(word=f"w{tid}-{i}", code=f"d{tid}-{i}", weight=1.0)
        except Exception as e:  # noqa: BLE001
            errors.append(f"writer {tid}: {type(e).__name__}: {e}")
        finally:
            db.close()

    def reader() -> None:
        rounds = 0
        while not stop.is_set():
            try:
                _count_words()
                rounds += 1
            except Exception as e:  # noqa: BLE001
                errors.append(f"reader: {type(e).__name__}: {e}")
                return
        reader_rounds.append(rounds)

    reader_thread = threading.Thread(target=reader, name="t8-reader")
    reader_thread.start()
    try:
        with ThreadPoolExecutor(max_workers=N_THREADS) as pool:
            list(pool.map(writer, range(N_THREADS)))
    finally:
        stop.set()
        reader_thread.join(timeout=10)

    assert errors == [], f"读写并发出现异常: {errors[:3]}"
    assert reader_rounds and reader_rounds[0] > 0, "读线程未能完成任何一次读取"
    assert _count_words() == N_THREADS * WORDS_PER_THREAD
