"""GUI 工作线程服务归属回归用例（T19）。

缺陷
----
GUI 的工作线程此前直接使用**主线程创建的长驻服务实例**（``DictService`` /
``FilterService`` / ``WeightCalculator``），等于多个线程共用同一个 SQLAlchemy
``Session``。``Session`` 不是线程安全的：

* 本模块 ``test_shared_service_mode_is_destructive`` 在隔离子进程里复现了修复前的写法，
  实测 8 线程 ×20 条：部分写入丢失、抛
  ``This session is provisioning a new connection; concurrent operations are not
  permitted``，并且**进程还会直接崩掉**（segfault，故该用例必须在子进程里跑，
  否则会带走整个 pytest 进程）；
* T8 的独立实测基线：2 线程 → 20/40、3 线程 → 20/60、8 线程 → 22/160 落库。

修复
----
``ui/gui/threads/service_factory.py`` 提供线程私有的服务 scope：线程在 ``run()`` 内
创建服务、``with`` 退出时释放（谁创建、谁关闭，与 T5 的显式所有权模型一致）。
本模块锁定该行为。

隔离约定
--------
**不使用真实用户数据库**：夹具把 DAL 全局（``_database_path`` / ``_engine`` /
``_SessionFactory``）指向 ``tmp_path`` 临时库，测试结束由 monkeypatch 自动还原；
写入走真实的 ``Session`` / ``WordRepository`` 路径（不是桩）。
"""
import os
import pathlib
import subprocess
import sys
import textwrap
import threading

import pytest

from app.dal import database as dbmod
from app.dal.models import Word
from app.services.stats import StatsService
from ui.gui.threads import AddBatchThread, service_factory

N_THREADS = 8
WORDS_PER_THREAD = 20
VMTOOL_ROOT = pathlib.Path(__file__).resolve().parents[2]

# 修复前的写法：所有线程共用同一个 DictService（= 同一个 Session）。
# 放在子进程里跑：这种共享实测除了丢写还会导致进程级崩溃（segfault）。
SHARED_MODE_SCRIPT = textwrap.dedent(
    """
    import os, threading
    from app.dal import database as dbmod
    from app.dal.models import Word

    dbmod._database_path = os.environ["T19_DB"]
    dbmod._engine = None
    dbmod._SessionFactory = None
    dbmod.Base.metadata.create_all(bind=dbmod._get_engine())

    from app.services.dict import DictService

    N, PER = 8, 20
    shared = DictService()
    errors = []

    def worker(tid):
        try:
            for i in range(PER):
                shared.add_word(f"w{tid}_{i}", f"c{tid}{i}")
        except Exception as e:
            errors.append(type(e).__name__)

    ts = [threading.Thread(target=worker, args=(t,)) for t in range(N)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()

    db = dbmod.get_db()
    landed = db.query(Word).count()
    db.close()
    print(f"LANDED={landed} EXPECTED={N * PER} ANOMALIES={len(errors)}")
    print("SAMPLE=" + (errors[0] if errors else "none"))
"""
)


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """把 DAL 指向临时库文件（不触碰 ~/.config/vm-tool/vm_tool.db）。"""
    path = tmp_path / "thread_ownership.db"
    monkeypatch.setattr(dbmod, "_database_path", str(path))
    monkeypatch.setattr(dbmod, "_engine", None)
    monkeypatch.setattr(dbmod, "_SessionFactory", None)
    dbmod.Base.metadata.create_all(bind=dbmod._get_engine())
    # 缓存失效回调是模块级全局，测试后必须还原，避免渗到其它用例
    monkeypatch.setattr(service_factory, "_stats_cache_invalidator", None)
    return path


def _count_words() -> int:
    """用独立会话统计行数（调用方负责关闭）。"""
    db = dbmod.get_db()
    try:
        return db.query(Word).count()
    finally:
        db.close()


def _spy_on_creation(monkeypatch):
    """记录每次服务创建：``(创建线程 ident, 实例)``。"""
    created = []
    real_create = service_factory.create_dict_service

    def spy():
        service = real_create()
        created.append((threading.get_ident(), service))
        return service

    monkeypatch.setattr(service_factory, "create_dict_service", spy)
    return created


def test_scoped_threads_persist_all_writes(temp_db):
    """每个线程自持服务并发写：全部落库，且无异常（修复后的行为）。"""
    errors = []

    def worker(tid):
        try:
            with service_factory.dict_service_scope() as dict_service:
                for i in range(WORDS_PER_THREAD):
                    dict_service.add_word(f"独立{tid}_{i}", f"dl{tid}{i}")
        except Exception as e:  # pragma: no cover - 修复后不应走到这里
            errors.append(f"{type(e).__name__}: {e}")

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"并发写入出现异常：{errors}"
    assert (
        _count_words() == N_THREADS * WORDS_PER_THREAD
    ), "落库数与期望不符 —— 说明又出现了跨线程共享会话导致的丢写"


def test_scope_creates_one_instance_per_thread_and_releases_it(temp_db, monkeypatch):
    """归属断言：每个线程拿到**自己**的实例（创建于本线程），with 退出即释放。"""
    created = _spy_on_creation(monkeypatch)
    runner_idents = []

    def worker(tid):
        runner_idents.append(threading.get_ident())
        with service_factory.dict_service_scope() as dict_service:
            assert dict_service.db is not None, "with 作用域内会话必须可用"
            dict_service.add_word(f"归属{tid}", f"gs{tid}")
        assert dict_service.db is None, "with 退出后服务必须已释放会话"

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(created) == N_THREADS, "每个线程应各自创建一次服务"
    assert (
        len({id(service) for _, service in created}) == N_THREADS
    ), "不同线程拿到了同一个服务实例 —— 跨线程共享会话又回来了"
    main_ident = threading.get_ident()
    assert all(
        ident != main_ident for ident, _ in created
    ), "服务实例不能在主线程创建后再交给工作线程使用"
    assert sorted(ident for ident, _ in created) == sorted(
        runner_idents
    ), "服务实例必须在真正使用它的那个线程内创建"
    assert _count_words() == N_THREADS


def test_thread_class_owns_and_releases_its_service(temp_db, monkeypatch):
    """线程类自身：run() 内创建服务、退出后释放，且不在 self 上留实例。"""
    created = _spy_on_creation(monkeypatch)
    items = [f"批量{i}" for i in range(5)]
    thread = AddBatchThread(items)
    runner_ident = {}

    def run_in_worker():
        runner_ident["ident"] = threading.get_ident()
        thread.run()  # 直接跑 run()，不依赖 Qt 事件循环

    runner = threading.Thread(target=run_in_worker)
    runner.start()
    runner.join()

    assert not hasattr(
        thread, "dict_service"
    ), "线程类不得把服务实例存在 self 上（那会重新变成跨线程共享）"
    assert len(created) == 1
    create_ident, service = created[0]
    assert create_ident == runner_ident["ident"] != threading.get_ident()
    assert service.db is None, "run() 结束必须释放服务持有的会话"
    assert _count_words() == len(items)


def test_stats_cache_invalidator_still_fires_from_worker_thread(temp_db):
    """统计缓存回调保活：工作线程内经工厂写入后，stats 缓存确实被清空。"""
    stats = StatsService()
    stats._stats_cache = {"stale": True}
    stats._cache_timestamp = 123
    service_factory.register_stats_cache_invalidator(stats.clear_cache)

    observed = {}

    def worker():
        with service_factory.dict_service_scope() as dict_service:
            dict_service.add_word("缓存失效验证", "hcsx")
        observed["cache"] = stats._stats_cache

    runner = threading.Thread(target=worker)
    runner.start()
    runner.join()

    registered = service_factory.get_stats_cache_invalidator()
    assert registered is not None
    # 绑定方法每次访问都是新对象，故比较 __self__/__func__ 而不是 is
    assert (
        registered.__self__ is stats and registered.__func__ is StatsService.clear_cache
    )
    assert observed["cache"] is None, "工作线程写入后统计缓存未被清空"
    assert stats._cache_timestamp == 0


def test_shared_service_mode_is_destructive(temp_db):
    """区分力对照：修复前的「共享一个服务实例」写法确实会丢写/报错/崩溃。

    放在隔离子进程里执行，避免共享 Session 触发的 segfault 带走 pytest 进程本身。
    """
    env = dict(os.environ, T19_DB=str(temp_db))
    proc = subprocess.run(
        [sys.executable, "-c", SHARED_MODE_SCRIPT],
        cwd=VMTOOL_ROOT,
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
    )

    degraded = proc.returncode != 0  # 崩溃同样算「被破坏」
    details = (
        f"returncode={proc.returncode} stdout={proc.stdout!r} "
        f"stderr={proc.stderr[-400:]!r}"
    )
    for line in proc.stdout.splitlines():
        if line.startswith("LANDED="):
            landed, expected, anomalies = (
                int(part.split("=")[1]) for part in line.split()[:3]
            )
            degraded = degraded or landed < expected or anomalies > 0
    assert degraded, f"共享 Session 模式未表现出破坏性：{details}"
