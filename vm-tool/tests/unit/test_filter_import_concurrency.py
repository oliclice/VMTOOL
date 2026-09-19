"""batch_import 并发写库回归（T28 / T11-F2）

缺陷：``batch_import`` 用 ``ThreadPoolExecutor(max_workers=4)`` 并行调用
``import_from_*``，各任务共用同一个 ``self.db`` —— 多线程在同一个 Session 上交错
事务。T11-F2 在临时库实测（6 文件 × 40 条）：6/6 文件失败、``total_imported=0``、
实际落库 39/240（异常 ``This transaction is closed`` /
``sqlite3.InterfaceError: bad parameter or other API misuse``）。

修复：每个任务在自己线程内自建 FilterService 与会话（
``FilterService._import_file_in_own_session``），用完在 finally 里 ``close()``。
本文件用**真实临时 SQLite** 精确计数落库条数（不是"没报错"）来固定该结论。

隔离：``tests/unit/conftest.py`` 的 autouse 装置（T24）只允许访问重定向到
``tmp_path`` 的库；本文件的 ``temp_db`` 夹具正是这样做的，不触碰
``~/.config/vm-tool/vm_tool.db``。
"""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.dal import database as dbmod
from app.dal.models import Word
from app.services import filter as filter_module
from app.services.filter import FilterService

FILE_COUNT = 6
WORDS_PER_FILE = 40


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """把 DAL 指向临时库（满足 conftest 的路径感知守卫）。"""
    path = tmp_path / "batch_import.db"
    monkeypatch.setattr(dbmod, "_database_path", str(path))
    monkeypatch.setattr(dbmod, "_engine", None)
    monkeypatch.setattr(dbmod, "_SessionFactory", None)
    dbmod.Base.metadata.create_all(bind=dbmod._get_engine())
    assert dbmod.get_database_path() == str(path)
    yield path


def _make_dir(tmp_path):
    directory = tmp_path / "import_files"
    directory.mkdir()
    return directory


def _write_txt(directory, index: int):
    path = directory / f"f{index}.txt"
    path.write_text(
        "\n".join(f"词{index}-{i}\tcode{index}{i}\t1.0" for i in range(WORDS_PER_FILE))
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_csv(directory, index: int):
    path = directory / f"f{index}.csv"
    rows = ["word,code,weight"]
    rows += [f"csv{index}-{i},cc{index}{i},1.0" for i in range(WORDS_PER_FILE)]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def _write_json(directory, index: int):
    path = directory / f"f{index}.json"
    payload = [
        {"word": f"json{index}-{i}", "code": f"jc{index}{i}", "weight": 1.0}
        for i in range(WORDS_PER_FILE)
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _count_words() -> int:
    """用独立会话统计落库行数（调用方负责关闭）。"""
    db = dbmod.get_db()
    try:
        return db.query(Word).count()
    finally:
        db.close()


def test_batch_import_concurrent_sessions_persist_every_row(
    temp_db, tmp_path, monkeypatch
):
    """核心闭合证据：6 文件 × 40 条并发导入 → 精确落库 240 条、0 失败文件。"""
    directory = _make_dir(tmp_path)
    files = [_write_txt(directory, i) for i in range(FILE_COUNT)]

    # 观察：外层调用方服务 1 个 + 每个并发任务各 1 个 = 7 个会话，且都被关闭
    created: list[Session] = []
    closed: list[int] = []
    real_get_db = filter_module.get_db
    real_close = Session.close

    def tracking_get_db():
        session = real_get_db()
        created.append(session)
        return session

    def tracking_close(self, *args, **kwargs):
        closed.append(id(self))
        return real_close(self, *args, **kwargs)

    monkeypatch.setattr(filter_module, "get_db", tracking_get_db)
    with patch.object(Session, "close", tracking_close):
        service = FilterService()
        try:
            result = service.batch_import(str(directory))
        finally:
            service.close()

    expected = FILE_COUNT * WORDS_PER_FILE
    assert len(files) == FILE_COUNT
    assert result == {
        "total_imported": expected,
        "failed_files": [],
    }, f"并发导入未全部成功（T11-F2 回归）: {result}"
    assert _count_words() == expected, "落库条数不等于期望条数（T11-F2 回归）"
    assert len(created) == FILE_COUNT + 1, (
        f"应为「调用方服务 1 个 + 每个文件各 1 个」共 {FILE_COUNT + 1} 个会话，"
        f"实际 {len(created)} 个"
    )
    assert all(id(s) in closed for s in created), "并发任务自建的会话未全部关闭"


def test_batch_import_handles_mixed_formats(temp_db, tmp_path):
    """txt / csv / json 三种格式混排：条数精确相加。"""
    directory = _make_dir(tmp_path)
    _write_txt(directory, 0)
    _write_csv(directory, 1)
    _write_json(directory, 2)

    service = FilterService()
    try:
        result = service.batch_import(str(directory))
    finally:
        service.close()

    expected = 3 * WORDS_PER_FILE
    assert result == {"total_imported": expected, "failed_files": []}
    assert _count_words() == expected


def test_batch_import_skips_unsupported_files(temp_db, tmp_path):
    """不支持的后缀不参与导入，也不计入失败文件。"""
    directory = _make_dir(tmp_path)
    _write_txt(directory, 0)
    (directory / "notes.md").write_text("不是导入格式\n", encoding="utf-8")

    service = FilterService()
    try:
        result = service.batch_import(str(directory))
    finally:
        service.close()

    assert result == {
        "total_imported": WORDS_PER_FILE,
        "failed_files": [],
    }, "不支持的后缀应在提交任务前被过滤掉，既不导入也不计入失败"
    assert _count_words() == WORDS_PER_FILE


def test_batch_import_empty_directory(temp_db, tmp_path):
    """空目录：不建会话、不报错。"""
    directory = _make_dir(tmp_path)
    service = FilterService()
    try:
        assert service.batch_import(str(directory)) == {
            "total_imported": 0,
            "failed_files": [],
        }
    finally:
        service.close()
    assert _count_words() == 0


def test_single_file_import_path_unchanged(temp_db, tmp_path):
    """不得回归既有能力：单文件（非批处理）导入路径行为不变。"""
    path = _write_txt(_make_dir(tmp_path), 0)

    service = FilterService()
    try:
        result = service.import_from_txt(str(path))
    finally:
        service.close()

    assert result["added"] == WORDS_PER_FILE
    assert result["total_count"] == WORDS_PER_FILE
    assert _count_words() == WORDS_PER_FILE
