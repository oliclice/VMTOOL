#!/usr/bin/env python3
"""测试Python模式编码规则"""
from app.services.code_generator import CodeGenerator

# 创建编码生成器
code_generator = CodeGenerator()

# 设置为自定义规则模式
code_generator.set_config({'rule': 'custom'})

# 测试词
test_word = "你好"

# 模拟字编码（双字符）
char_codes = ["ni", "ha"]  # 假设"你"的编码是"ni"，"好"的编码是"ha"

# 测试Python模式规则
python_rule = '''
result = ''
for char in vac:
    if char in code:
        result += code[char][0]+code[char][1]
'''

# 准备变量
vac = test_word
code = {}
for i, char in enumerate(test_word):
    code[char] = char_codes[i] if i < len(char_codes) else ''

# 执行Python代码
local_vars = {'vac': vac, 'code': code, 'result': ''}
exec(python_rule, {}, local_vars)
result = local_vars.get('result', '')

print(f"测试词: {test_word}")
print(f"词长度: {len(test_word)}")
print(f"字符编码: {code}")
print(f"编码结果: {result}")
print(f"期望结果: niah")  # 应该是ni的前两个字符加上hao的前两个字符
