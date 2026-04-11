#!/usr/bin/env python3
# 测试编码生成器

import sys
import os

# 添加 vm-tool 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vm-tool'))

# 现在可以导入模块
from app.services.code_generator import CodeGenerator

# 创建编码生成器实例
cg = CodeGenerator()

# 测试基本功能
print("测试基本编码生成:")
code = cg.generate_code('测试')
print(f"'测试' 的编码: {code}")

# 测试自定义规则
print("\n测试自定义规则:")
from app.core.config_manager import config_manager
config_manager.set("custom_rules", {
    "测试规则": "v[2] = s[1][1] + s[1][2] + s[2][1] + s[2][2]"
})
config_manager.set("code_rule", "测试规则")
# 由于generate_code方法内部会从数据库获取字的编码，我们需要先确保数据库中有这些字
# 这里我们直接测试_execute_custom_rule方法，因为它接受char_codes参数
from app.services.code_generator import CodeGenerator
cg = CodeGenerator()
# 直接测试_execute_custom_rule方法
char_codes = ['ce', 'shi']
code = cg._execute_custom_rule('测试', char_codes)
print(f"'测试' 的编码 (使用自定义规则): {code}")

# 测试v[4+]语法
print("\n测试v[4+]语法:")
config_manager.set("custom_rules", {
    "测试规则": "v[4+] = s[1][1] + s[2][1] + s[3][1] + s[4][1]"
})
char_codes = ['ce', 'shi', 'ce', 'shi']
code = cg._execute_custom_rule('测试测试', char_codes)
print(f"'测试测试' 的编码 (使用v[4+]规则): {code}")

print("\n测试完成!")
