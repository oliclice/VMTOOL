"""DictService.add_word 的单元测试（纯桩）

隔离约定：
- `app.services.dict.WordRepository`、`app.services.code_generator.WordRepository`、
  `app.services.code_generator.get_db` 全部替换为桩，不读写真实数据库；
- 桩方法的返回值显式配置（`get_by_word_and_code` 明确返回 None），
  避免未配置的 Mock 返回值被真值化而误判「组合已存在」；
- 真实数据库与全局缓存由 `tests/unit/conftest.py` 的 autouse 装置统一隔离
  （T24 从本模块上移；此前内联的理由是 tests/ 被 .gitignore 忽略，T13 已解除）。

断言以 app/services/dict.py 的真实实现为准。
"""
from unittest.mock import MagicMock, patch

import pytest

from app.core.errors import DictError
from app.dal.models import Word
from app.services.dict import DictService


def _build_service(mock_dict_repo_cls, mock_get_db):
    """构造被测服务：仓库与内部 CodeGenerator 的数据库访问全部是桩。"""
    mock_get_db.side_effect = lambda: iter([MagicMock()])
    service = DictService(MagicMock())
    assert service.repo is mock_dict_repo_cls.return_value  # 确认注入的是桩仓库
    return service


@patch("app.services.code_generator.WordRepository")
@patch("app.services.code_generator.get_db")
@patch("app.services.dict.WordRepository")
def test_add_word(mock_dict_repo_cls, mock_get_db, mock_cg_repo_cls):
    """新增词条：真实实现返回 word/code/weight/is_character/is_special/manual
    六个字段。"""
    service = _build_service(mock_dict_repo_cls, mock_get_db)

    # 显式声明桩语义：该 (word, code) 组合在库中不存在
    service.repo.get_by_word_and_code.return_value = None
    service.repo.create.return_value = Word(
        word="测试",
        code="cs",
        weight=100,
        is_character=False,
        is_special=False,
        manual=False,
    )

    result = service.add_word(word="测试", code="cs", weight=100)

    assert result == {
        "word": "测试",
        "code": "cs",
        "weight": 100,
        "is_character": False,
        "is_special": False,
        "manual": False,
    }
    service.repo.get_by_word_and_code.assert_called_once_with("测试", "cs")
    service.repo.create.assert_called_once_with("测试", "cs", 100, False, False, False)


@patch("app.services.code_generator.WordRepository")
@patch("app.services.code_generator.get_db")
@patch("app.services.dict.WordRepository")
def test_add_word_duplicate_pair_raises(
    mock_dict_repo_cls, mock_get_db, mock_cg_repo_cls
):
    """重复检查由桩的返回值驱动：桩返回已存在记录时才抛 DictError，且不写库。"""
    service = _build_service(mock_dict_repo_cls, mock_get_db)
    service.repo.get_by_word_and_code.return_value = Word(
        word="测试", code="cs", weight=100
    )

    with pytest.raises(DictError, match="已存在"):
        service.add_word(word="测试", code="cs", weight=100)

    service.repo.create.assert_not_called()
