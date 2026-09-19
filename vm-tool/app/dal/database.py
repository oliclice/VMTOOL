"""数据库引擎与会话管理

分层约定：本模块属于 DAL，**不得反向依赖 app.core**。
数据库文件路径由组合根（CLI / GUI）经 :func:`set_database_path` 注入。
"""
import os

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

Base = declarative_base()

_engine = None
_SessionFactory = None

#: 由组合根注入的数据库文件路径；未注入时为 None。
_database_path: str | None = None

#: 未注入时的环境变量名。
DATABASE_PATH_ENV = "VMTOOL_DATABASE_PATH"

#: 未注入且无环境变量时的默认路径（与 ConfigManager 的默认值保持一致）。
DEFAULT_DATABASE_PATH = os.path.join(
    os.path.expanduser("~"), ".config", "vm-tool", "vm_tool.db"
)


def set_database_path(path: str | None) -> None:
    """注入数据库文件路径（由组合根 CLI / GUI 调用）。

    路径发生变化时丢弃旧的引擎与会话工厂，下次访问数据库时按新路径重建。

    Args:
        path: 数据库文件路径；None 表示回到环境变量 / 默认路径。
    """
    global _database_path, _engine, _SessionFactory
    if path == _database_path:
        return
    if _engine is not None:
        _engine.dispose()
    _database_path = path
    _engine = None
    _SessionFactory = None


def get_database_path() -> str:
    """返回当前生效的数据库文件路径。

    优先级：注入值 > 环境变量 ``VMTOOL_DATABASE_PATH`` > :data:`DEFAULT_DATABASE_PATH`。
    """
    return _database_path or os.environ.get(DATABASE_PATH_ENV) or DEFAULT_DATABASE_PATH


#: 连接级 busy_timeout（毫秒）。并发写时让 SQLite 等待而不是立刻抛
#: "database is locked"；与 connect_args["timeout"]（秒）等价，显式 PRAGMA 便于阅读。
SQLITE_BUSY_TIMEOUT_MS = 30_000


def _configure_sqlite_connection(dbapi_connection, _connection_record) -> None:
    """每条新连接生效的 SQLite PRAGMA。

    - ``journal_mode=WAL``：读写不再互相阻塞（原 rollback journal 下写会阻塞读），
      且该设置持久化在数据库文件头，重复执行是幂等的 no-op；
    - ``busy_timeout``：并发写时按毫秒等待锁，而不是立即报 database is locked。
    """
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
    finally:
        cursor.close()


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            f"sqlite:///{get_database_path()}",
            connect_args={
                # 会话可能在不同线程间交接使用（GUI 服务实例 + 工作线程），
                # 故不启用 sqlite3 的线程归属检查；线程安全由「每个会话一条
                # 独立连接（NullPool）」保证，而不是靠共享同一条连接。
                "check_same_thread": False,
                "timeout": 30,
            },
            # NullPool：每个 Session 各自 checkout 一条连接。原实现让全进程共用
            # 一条连接，多线程写库会在同一条连接上交错事务，实测出现
            # cannot commit transaction - SQL statements in progress /
            # bad parameter or other API misuse / INSERT 拿不到主键等错误。
            # 连接不再复用，故 pool_pre_ping 无意义。
            poolclass=NullPool,
        )
        event.listen(_engine, "connect", _configure_sqlite_connection)
    return _engine


def _get_session_factory():
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(
            autocommit=False, autoflush=False, bind=_get_engine()
        )
    return _SessionFactory


def recreate_engine():
    """丢弃并重建引擎与会话工厂（数据库文件被替换后调用）。"""
    global _engine, _SessionFactory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionFactory = None
    _get_engine()
    _get_session_factory()


def get_db() -> Session:
    """创建一个新的数据库会话，生命周期由调用方负责。

    用法：``db = get_db()`` 之后必须显式 ``db.close()``（``Session`` 自带上下文
    管理，也可以写成 ``with get_db() as db:``）。

    不要再用「生成器取一次 next」的写法：那种形态下 ``finally: db.close()``
    的执行时机取决于引用计数与 GC，事务边界不确定（在 CPython 上实测会在
    取 next 之后立刻关闭会话）。
    """
    return _get_session_factory()()
