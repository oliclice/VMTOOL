"""会话所有权回归用例（T16）

隔离约定：**不使用真实用户数据库**。需要真实会话的用例把 DAL 的模块全局
（``_database_path`` / ``_engine`` / ``_SessionFactory``）monkeypatch 到 pytest 的
``tmp_path`` 临时库，测试结束自动还原；只关心 close() 是否被调用的用例使用桩会话。

覆盖的所有权规则（与 T5 建立的模型一致）：
- ``db=None``：服务自建会话并持有 → 调用方 ``close()`` 后必须真的关闭；
- ``db=<外部会话>``：注入方负责关闭，服务不得越权关闭；
- FilterService 的 4 条导入路径里临时构造的 DictService 必须被 close（否则其内部
  CodeGenerator 会话泄漏）。
"""
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.errors import FileError
from app.dal import database as dbmod
from app.services.filter import FilterService
from app.services.stats import StatsService
from app.services.weight import WeightCalculator


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """把 DAL 指向临时库文件（不触碰 ~/.config/vm-tool/vm_tool.db）。"""
    path = tmp_path / "ownership.db"
    monkeypatch.setattr(dbmod, "_database_path", str(path))
    monkeypatch.setattr(dbmod, "_engine", None)
    monkeypatch.setattr(dbmod, "_SessionFactory", None)
    dbmod.Base.metadata.create_all(bind=dbmod._get_engine())
    assert dbmod.get_database_path() == str(path)
    return path


@pytest.fixture
def closed_sessions(monkeypatch):
    """记录所有被 close() 的 Session（按对象 id）。"""
    closed = []
    original_close = Session.close

    def traced_close(self, *args, **kwargs):
        closed.append(id(self))
        return original_close(self, *args, **kwargs)

    monkeypatch.setattr(Session, "close", traced_close)
    return closed


@pytest.mark.parametrize("service_cls", [FilterService, WeightCalculator, StatsService])
def test_service_closes_self_created_session(service_cls, temp_db, closed_sessions):
    """自建会话：close() 必须真的关闭它，且幂等。"""
    service = service_cls()
    session = service.db
    assert session is not None
    assert service._owns_db is True

    service.close()

    assert id(session) in closed_sessions
    assert service.db is None
    service.close()  # 幂等：不抛异常、不重复关闭


@pytest.mark.parametrize("service_cls", [FilterService, WeightCalculator, StatsService])
def test_service_does_not_close_injected_session(service_cls, closed_sessions):
    """外部注入的会话：服务不得关闭，也不得清空引用。"""
    external = MagicMock()
    service = service_cls(external)
    assert service._owns_db is False
    assert service.db is external

    service.close()

    external.close.assert_not_called()
    assert service.db is external


@pytest.mark.parametrize("service_cls", [FilterService, WeightCalculator, StatsService])
def test_service_is_a_context_manager(service_cls, temp_db, closed_sessions):
    """上下文管理器：退出 with 块即释放自建会话（三个服务同构）。"""
    with service_cls() as service:
        session = service.db
        assert session is not None
    assert id(session) in closed_sessions
    assert service.db is None


def test_compatibility_layer_closes_every_service_session(temp_db, closed_sessions):
    """CompatibilityLayer 持有 4 个服务（含 DictService 的内部 CodeGenerator 会话）。"""
    from app.core.compatibility import CompatibilityLayer

    layer = CompatibilityLayer()
    sessions = [
        layer.dict_service.db,
        layer.dict_service.code_generator.db,
        layer.weight_calc.db,
        layer.filter_service.db,
        layer.stats_service.db,
    ]

    layer.close()

    assert len(set(map(id, sessions))) == len(sessions)  # 五个互不相同的会话
    for session in sessions:
        assert id(session) in closed_sessions


def test_compatibility_layer_is_a_context_manager(temp_db, closed_sessions):
    """CompatibilityLayer 退出 with 块时释放它自建的 5 个会话。"""
    from app.core.compatibility import CompatibilityLayer

    with CompatibilityLayer() as layer:
        sessions = [
            layer.dict_service.db,
            layer.dict_service.code_generator.db,
            layer.weight_calc.db,
            layer.filter_service.db,
            layer.stats_service.db,
        ]
    for session in sessions:
        assert id(session) in closed_sessions


def test_sessions_are_returned_after_close(temp_db):
    """创建→使用→释放 3 轮：连接 checkout/checkin 平衡（无累积）。"""
    engine = dbmod._get_engine()
    checkouts, checkins = [], []
    event.listen(engine, "checkout", lambda *a, **k: checkouts.append(1))
    event.listen(engine, "checkin", lambda *a, **k: checkins.append(1))

    for _ in range(3):
        service = FilterService()
        service.filter_by_length(1, None)  # 真正使用一次会话（空库返回 []）
        service.close()

    assert len(checkouts) >= 3, "未观察到连接 checkout，用例没有真正用到数据库"
    assert len(checkins) == len(checkouts), "有连接未归还"


def _patch_import_dependencies():
    """包装 import_from_txt 的外部依赖：配置、建索引、DictService。"""
    return (
        patch("app.core.config_manager.ConfigManager"),
        patch("app.dal.init_db.optimize_database"),
        patch("app.dal.init_db.create_indexes"),
        patch("app.services.dict.DictService"),
    )


def test_import_from_txt_closes_inner_dict_service(tmp_path):
    """导入路径里临时构造的 DictService 必须被 close()（内部 CodeGenerator 会话）。"""
    cm_patch, opt_patch, idx_patch, ds_patch = _patch_import_dependencies()
    with cm_patch as mock_cm, opt_patch, idx_patch, ds_patch as mock_ds_cls:
        mock_cm.return_value.get.return_value = "\t"
        mock_ds_cls.return_value.add_words.return_value = {
            "added": 1,
            "existing": 0,
            "existing_pairs": [],
            "added_words": [],
        }
        file_path = tmp_path / "in.txt"
        file_path.write_text("测试\tcs\t100\n", encoding="utf-8")

        service = FilterService(MagicMock())
        service.import_from_txt(str(file_path))

        mock_ds_cls.return_value.close.assert_called_once()


def test_import_from_txt_closes_inner_dict_service_on_error(tmp_path):
    """导入失败时也必须 close（finally 语义）。"""
    cm_patch, opt_patch, idx_patch, ds_patch = _patch_import_dependencies()
    with cm_patch as mock_cm, opt_patch, idx_patch, ds_patch as mock_ds_cls:
        mock_cm.return_value.get.return_value = "\t"
        mock_ds_cls.return_value.add_words.side_effect = RuntimeError("boom")
        file_path = tmp_path / "in.txt"
        file_path.write_text("测试\tcs\t100\n", encoding="utf-8")

        service = FilterService(MagicMock())
        with pytest.raises(FileError):
            service.import_from_txt(str(file_path))

        mock_ds_cls.return_value.close.assert_called_once()


def test_migration_defaults_match_core_settings():
    """migration.py 的 DAL 本地默认路径与被替换掉的 app.core Settings 取值等价。"""
    from app.core.config import settings
    from app.dal import migration

    assert migration.DEFAULT_MAIN_DICT == settings.MAIN_DICT
    assert migration.DEFAULT_OUTPUT_FILE == settings.OUTPUT_FILE
