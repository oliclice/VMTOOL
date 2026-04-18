
from unittest.mock import patch
from app.services.dict import DictService

@patch('app.services.dict.get_db')
def test_add_word(mock_get_db):
    db_session = Mock()
    mock_get_db.return_value = db_session
    service = DictService(db_session)
    result = service.add_word(word="测试", code="cs", weight=100)
    assert result == {
        "word": "测试",
        "code": "cs",
        "weight": 100,
        "is_active": True,
        "is_character": False,
        "is_special": False,
        "created_at": None,
        "updated_at": None
    }
