
from unittest.mock import patch
from app.services.code_generator import CodeGenerator

@patch('app.services.code_generator.get_db')
def test_generate_code_first_letter(mock_get_db):
    db_session = Mock()
    mock_get_db.return_value = db_session
    generator = CodeGenerator()
    generator.config = {'rule': 'first_letter', 'separator': ''}
    generator.repo.get_by_word.side_effect = [
        Mock(code='zh'),  # 中
        Mock(code='gw'),  # 国
    ]
    result = generator.generate_code('中国')
    assert result == 'zg'

@patch('app.services.code_generator.get_db')
def test_generate_code_custom_rule(mock_get_db):
    db_session = Mock()
    mock_get_db.return_value = db_session
    generator = CodeGenerator()
    generator.config = {'rule': 'custom'}
    with patch('app.services.code_generator.config_manager') as mock_cm:
        mock_cm.get.return_value = 'custom_rule'
        # 测试自定义规则
        result = generator.generate_code('custom_test')
        assert result == 'custom_rule(custom_test)'
