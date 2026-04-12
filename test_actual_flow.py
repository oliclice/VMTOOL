#!/usr/bin/env python3
"""测试实际编码生成流程"""
from app.services.code_generator import CodeGenerator

# 创建编码生成器
code_generator = CodeGenerator()

# 设置为自定义规则模式
code_generator.set_config({'rule': 'custom'})

# 测试词
test_word = "你好"

# 测试Python模式规则
python_rule = '''
result = ''
for char in vac:
    if char in code:
        result += code[char][0]+code[char][1]
'''

# 保存临时规则
from app.core.config_manager import config_manager
original_rule = config_manager.get("code_rule")
original_rules = config_manager.get("custom_rules", {}).copy()

temp_rule_name = "__test_rule__"
temp_rules = original_rules.copy()
temp_rules[temp_rule_name] = {
    "content": python_rule,
    "python_mode": True
}

config_manager.set("code_rule", temp_rule_name)
config_manager.set("custom_rules", temp_rules)

# 生成编码
try:
    code = code_generator.generate_code(test_word)
    print(f"测试词: {test_word}")
    print(f"词长度: {len(test_word)}")
    print(f"编码结果: {code}")
    print(f"期望结果: 应该包含每个字的前两个编码字符")
except Exception as e:
    print(f"生成编码失败: {e}")
finally:
    # 恢复原来的规则
    config_manager.set("code_rule", original_rule)
    config_manager.set("custom_rules", original_rules)
