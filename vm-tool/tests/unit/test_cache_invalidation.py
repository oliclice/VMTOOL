"""缓存失效回归用例：写后读必须一致（P0-2）

隔离约定（T24 起统一由 tests/unit/conftest.py 的 autouse 装置提供）：
- ``app.services.dict.WordRepository``、``app.services.code_generator.WordRepository``、
  ``app.services.code_generator.get_db`` 全部替换为桩，不读写真实数据库；
- 公共装置清空全局 ``app.core.cache.cache``，并用路径感知的哨兵守住
  ``app.dal.database`` 的 ``_get_engine``/``_get_session_factory``/``create_engine``：
  任何漏打的 patch 都会显式失败，而不是静默落到 ``~/.config/vm-tool/vm_tool.db``。

断言以 app/services/dict.py 的真实实现为准：失效动作集中在
``DictService._notify_data_changed()``（全部写路径都调用它）。

T17 追加：服务层其余写路径（``WeightCalculator``）同样是缓存读取源，
因此下文的 ``test_weight_*`` 用例用**真实临时库**验证「同一实例读→写→再读」一致。
"""
from unittest.mock import MagicMock, patch

import pytest

from app.core.cache import cache
from app.dal import database as _database
from app.dal.models import Word
from app.services.dict import DictService
from app.services.weight import WeightCalculator


def _word(code: str, word: str = "测试") -> Word:
    """构造一个游离的 Word 对象（不落库，仅用于桩返回值）。"""
    return Word(
        word=word,
        code=code,
        weight=1.0,
        is_active=True,
        is_character=False,
        is_special=False,
        manual=False,
    )


def _build_service(
    repo_stub: MagicMock, mock_cg_get_db: MagicMock, mock_dict_repo_cls
) -> DictService:
    """构造被测服务：仓库与内部 CodeGenerator 的数据库访问全部是桩。"""
    mock_dict_repo_cls.return_value = repo_stub
    mock_cg_get_db.return_value = MagicMock()
    service = DictService(MagicMock())
    assert service.repo is repo_stub  # 确认注入的是桩仓库
    return service


@patch("app.services.code_generator.get_db")
@patch("app.services.code_generator.WordRepository")
@patch("app.services.dict.WordRepository")
def test_update_word_invalidates_get_word_cache(
    mock_dict_repo_cls, _cg_repo_cls, mock_cg_get_db
):
    """更新词条后，get_word 必须立即读到新值（不能命中写前的缓存）。"""
    repo = MagicMock()
    service = _build_service(repo, mock_cg_get_db, mock_dict_repo_cls)

    repo.get_by_word.return_value = _word("cs")
    assert service.get_word("测试")["code"] == "cs"  # 第一次读：结果进入缓存

    # 模拟 update_word 之后的库内真实状态
    repo.get_by_word.return_value = _word("cs2")
    repo.update.return_value = _word("cs2")

    service.update_word("测试", code="cs2")  # 写路径 → 必须让读缓存失效

    assert service.get_word("测试")["code"] == "cs2", "写后读不一致：命中了写前的脏缓存"


@patch("app.services.code_generator.get_db")
@patch("app.services.code_generator.WordRepository")
@patch("app.services.dict.WordRepository")
def test_delete_word_invalidates_get_word_cache(
    mock_dict_repo_cls, _cg_repo_cls, mock_cg_get_db
):
    """删除词条后，get_word 必须立即读到「不存在」，而不是旧缓存里的词条。"""
    repo = MagicMock()
    service = _build_service(repo, mock_cg_get_db, mock_dict_repo_cls)

    repo.get_by_word.return_value = _word("cs", word="被删词")
    assert service.get_word("被删词") is not None

    repo.delete.return_value = True
    service.delete_word("被删词")  # 写路径

    repo.get_by_word.return_value = None  # 删除后库内已无该词
    assert service.get_word("被删词") is None, "写后读不一致：命中了写前的脏缓存"


@patch("app.services.code_generator.get_db")
@patch("app.services.code_generator.WordRepository")
@patch("app.services.dict.WordRepository")
def test_add_word_invalidates_get_words_by_code_cache(
    mock_dict_repo_cls, _cg_repo_cls, mock_cg_get_db
):
    """新增词条后，get_words_by_code 的缓存（含空列表）必须失效。"""
    repo = MagicMock()
    service = _build_service(repo, mock_cg_get_db, mock_dict_repo_cls)

    repo.get_by_code.return_value = []
    assert service.get_words_by_code("cs") == []  # 空结果也会被缓存

    repo.get_by_code.return_value = [_word("cs", word="新增词")]
    repo.get_by_word_and_code.return_value = None
    repo.create.return_value = _word("cs", word="新增词")

    service.add_word(word="新增词", code="cs", weight=100)  # 写路径

    assert (
        len(service.get_words_by_code("cs")) == 1
    ), "写后读不一致：命中了写前的空列表缓存"


@patch("app.services.code_generator.get_db")
@patch("app.services.code_generator.WordRepository")
@patch("app.services.dict.WordRepository")
def test_invalidation_is_global_across_instances(
    mock_dict_repo_cls, _cg_repo_cls, mock_cg_get_db
):
    """失效作用域判断依据：cache 是全局单例，clear() 覆盖所有实例的缓存键。

    GUI 里 DictService 是长驻单实例、filter.py 还会临时 new 实例，
    因此作用域必须是全局的，不能只清"自己"那份。
    """
    repo_a, repo_b = MagicMock(), MagicMock()
    mock_dict_repo_cls.side_effect = [repo_a, repo_b]
    mock_cg_get_db.return_value = MagicMock()
    service_a = DictService(MagicMock())
    service_b = DictService(MagicMock())

    new_word = _word("cs")
    repo_a.get_by_word.return_value = new_word
    repo_b.get_by_word.return_value = new_word
    assert service_b.get_word("测试")["code"] == "cs"  # B 实例先读一次并缓存

    updated = _word("cs2")
    repo_a.get_by_word.return_value = updated
    repo_a.update.return_value = updated
    repo_b.get_by_word.return_value = updated
    service_a.update_word("测试", code="cs2")  # A 实例写入

    assert service_b.get_word("测试")["code"] == "cs2", "A 的写入没有让 B 缓存失效"


def test_default_cache_ttl_is_bounded():
    """兜底：默认 ttl 必须降到 ≤60 秒，避免遗漏的失效路径造成长时间脏读。"""
    assert 0 < cache.ttl <= 60, f"默认 ttl 仍过长: {cache.ttl}"


# ─────────────────────────────────────────────────────────────────────────────
# T17：服务层其余写路径（WeightCalculator）的写后读一致
#
# 上面全是桩用例；下面这组必须走**真实 SQLite 写路径**（权重写入经
# WordRepository.update → commit），故用 real_temp_db 夹具把模块级哨兵换回真实实现。
# 仍然不触碰 ~/.config/vm-tool/vm_tool.db（写入 pytest 的 tmp_path 临时库）。
# ─────────────────────────────────────────────────────────────────────────────

_REAL_GET_ENGINE = _database._get_engine
_REAL_SESSION_FACTORY = _database._get_session_factory


@pytest.fixture
def real_temp_db(tmp_path, monkeypatch):
    """真实临时库（在模块级哨兵之后再次 monkeypatch，覆盖之）。"""
    monkeypatch.setattr(_database, "_get_engine", _REAL_GET_ENGINE)
    monkeypatch.setattr(_database, "_get_session_factory", _REAL_SESSION_FACTORY)
    monkeypatch.setattr(_database, "_database_path", str(tmp_path / "weight_cache.db"))
    monkeypatch.setattr(_database, "_engine", None)
    monkeypatch.setattr(_database, "_SessionFactory", None)
    _database.Base.metadata.create_all(bind=_database._get_engine())
    yield
    cache.clear()


@pytest.fixture
def stub_weight_freq(monkeypatch):
    """固定词频为 0 → new_weight = base_weight，不读 data/ 词频文件。"""
    monkeypatch.setattr("app.services.weight.load_thuocl_data", lambda *_a, **_k: {})
    monkeypatch.setattr("app.services.weight.get_log_weight", lambda *_a, **_k: 0.0)


@pytest.fixture
def stub_weight_config(monkeypatch):
    """固定 recalculate_all_weights 的范围配置，不读用户 config.json。"""
    from app.core import config_manager as config_manager_module

    fake = MagicMock()
    fake.get.side_effect = lambda key, default=None: {
        "weight_calc_words": True,
        "weight_calc_chars": False,
        "weight_calc_special": False,
    }.get(key, default)
    monkeypatch.setattr(config_manager_module, "config_manager", fake)


def _release(service) -> None:
    """释放服务会话：优先用 T16 的 close()，未合入时退回直接关自身会话。"""
    close = getattr(service, "close", None)
    if callable(close):
        close()
    elif getattr(service, "db", None) is not None:
        service.db.close()


def _assert_read_write_read(reader: DictService, word: str, expected: float) -> None:
    """同一实例读到新值，且全新实例读数一致。"""
    assert (
        reader.get_word(word)["weight"] == expected
    ), "权重写入后同一实例读到了旧缓存（脏读）"
    fresh = DictService()
    try:
        assert (
            fresh.get_word(word)["weight"] == expected
        ), "全新实例与同一实例的读数必须一致"
    finally:
        _release(fresh)


def test_set_weight_directly_invalidates_cached_read(real_temp_db):
    """T7 实测的脏读复现：读 1.0 → set_weight_directly(5.0) → 同实例必须读到 5.0。"""
    reader = DictService()
    writer = WeightCalculator()
    try:
        reader.add_word("测试", "cs", 1.0)
        assert reader.get_word("测试")["weight"] == 1.0  # 进入缓存

        writer.set_weight_directly("测试", 5.0)

        _assert_read_write_read(reader, "测试", 5.0)
    finally:
        _release(reader)
        _release(writer)


def test_update_word_weight_invalidates_cached_read(real_temp_db, stub_weight_freq):
    """update_word_weight 写后读一致。"""
    reader = DictService()
    writer = WeightCalculator()
    try:
        reader.add_word("测试", "cs", 1.0)
        assert reader.get_word("测试")["weight"] == 1.0

        writer.update_word_weight("测试", 0.1)  # new_weight = 1.0 + 0.1 = 1.1

        _assert_read_write_read(reader, "测试", 1.1)
    finally:
        _release(reader)
        _release(writer)


def test_recalculate_all_weights_invalidates_cached_read(
    real_temp_db, stub_weight_freq, stub_weight_config
):
    """批量重算（循环内 commit）写后读一致。"""
    reader = DictService()
    writer = WeightCalculator()
    try:
        reader.add_word("测试", "cs", 100.0)
        assert reader.get_word("测试")["weight"] == 100.0

        result = writer.recalculate_all_weights()
        assert result["updated"] == 1

        _assert_read_write_read(reader, "测试", 1.0)
    finally:
        _release(reader)
        _release(writer)


def test_calculate_weights_for_words_invalidates_cached_read(
    real_temp_db, stub_weight_freq
):
    """按词表批量重算（循环内 commit）写后读一致。"""
    reader = DictService()
    writer = WeightCalculator()
    try:
        reader.add_word("测试", "cs", 100.0)
        assert reader.get_word("测试")["weight"] == 100.0

        result = writer.calculate_weights_for_words([{"word": "测试"}])
        assert result["updated"] == 1

        _assert_read_write_read(reader, "测试", 1.0)
    finally:
        _release(reader)
        _release(writer)


def test_adjust_same_code_weights_invalidates_cached_read(real_temp_db):
    """同码词权重调整（循环内 repo.update）写后读一致。"""
    reader = DictService()
    writer = WeightCalculator()
    try:
        for word, weight in (("甲", 10.0), ("乙", 5.0), ("丙", 1.0)):
            reader.add_word(word, "cs", weight)
        assert reader.get_word("乙")["weight"] == 5.0

        writer.adjust_same_code_weights("cs")  # base=10 → 乙 8.0、丙 6.4

        _assert_read_write_read(reader, "乙", 8.0)
    finally:
        _release(reader)
        _release(writer)
