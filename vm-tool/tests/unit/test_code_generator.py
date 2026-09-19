"""CodeGenerator 编码生成的单元测试（纯桩）

隔离约定：
- `app.services.code_generator.get_db` 与 `app.services.code_generator.WordRepository`
  均被替换为桩：`CodeGenerator.__init__` 会 `get_db()` 建会话并构造
  `WordRepository`（T5 起为显式会话，不再有 `next(get_db())`），不打桩就会真连用户库；
- 自定义规则用例替换 `app.core.config_manager.config_manager`，不读用户真实配置；
- 真实数据库与全局缓存由 `tests/unit/conftest.py` 的 autouse 装置统一隔离
  （T24 从本模块上移；此前内联的理由是 tests/ 被 .gitignore 忽略，T13 已解除）。
  任何漏打的 patch 都会显式失败，而不是静默落到 `~/.config/vm-tool/vm_tool.db`。

断言以 app/services/code_generator.py 的真实实现为准。
"""
from unittest.mock import Mock, patch

import pytest

from app.services.code_generator import (
    ALLOWED_RULE_METHODS,
    CodeGenerator,
    CustomRuleSecurityError,
    PythonModeConfirmationRequired,
    audit_python_mode_rules,
    confirm_python_mode_rules,
    validate_python_rule,
)


@patch("app.services.code_generator.WordRepository")
@patch("app.services.code_generator.get_db")
def test_generate_code_first_letter(mock_get_db, mock_repo_cls):
    """first_letter 规则：取每个字编码的首字符拼接（separator 为空串）。"""
    # CodeGenerator.__init__ 使用 next(get_db())，桩必须返回值上的迭代器
    mock_get_db.side_effect = lambda: iter([Mock()])
    generator = CodeGenerator()
    generator.config = {"rule": "first_letter", "separator": ""}
    generator.repo.get_by_word.side_effect = [
        Mock(code="zh"),  # 中
        Mock(code="gw"),  # 国
    ]

    assert generator.generate_code("中国") == "zg"
    # 逐个字符查字表，且查的是字本身
    assert [c.args[0] for c in generator.repo.get_by_word.call_args_list] == [
        "中",
        "国",
    ]


@patch("app.services.code_generator.WordRepository")
@patch("app.services.code_generator.get_db")
@patch("app.core.config_manager.config_manager")
def test_generate_code_custom_rule(mock_cm, mock_get_db, mock_repo_cls):
    """custom 规则：按 v[N] = s[i][j] 模板取字符编码位拼接。

    真实实现（_execute_custom_rule）从 config_manager 读取 code_rule 与 custom_rules，
    再把 s[第i个字][该字编码的第j位] 逐位替换成实际编码字符。
    """
    mock_get_db.side_effect = lambda: iter([Mock()])
    mock_cm.get.side_effect = lambda key, default=None: {
        "code_rule": "测试双拼",
        "custom_rules": {"测试双拼": "v[2] = s[1][1] + s[1][2] + s[2][1] + s[2][2]"},
    }.get(key, default)

    generator = CodeGenerator()
    generator.config = {"rule": "custom"}
    generator.repo.get_by_word.side_effect = [
        Mock(code="zh"),  # 中 -> 取 z、h
        Mock(code="guo"),  # 国 -> 取 g、u
    ]

    assert generator.generate_code("中国") == "zhgu"
    mock_cm.get.assert_any_call("code_rule", "默认规则")
    mock_cm.get.assert_any_call("custom_rules", {})


# ---------------------------------------------------------------------------
# T6 沙箱加固（P0-3）：python_mode 规则不得执行任意代码
# ---------------------------------------------------------------------------

# 键 = 用例名，值 = 必须被 AST 白名单拒绝的规则源码
FORBIDDEN_RULE_SOURCES = {
    "import_os": "import os\nresult = os.system('id')",
    "from_import": "from os import system\nresult = system('id')",
    "dunder_import": "result = __import__('os').system('id')",
    "open_file": "result = open('/etc/passwd').read()",
    "bare_open": "result = open('/etc/passwd')",
    "eval_name": "result = eval('1+1')",
    "dunder_attribute": "result = vac.__class__.__mro__",
    "underscore_globals": "result = len.__globals__",
    "format_bypass": "result = '{0.__class__}'.format(vac)",
    "while_loop": "while True:\n    result = 'x'",
    "helper_escape": "def f():\n    return 1\nimport os\nresult = os.name",
    # --- T27（T11-F3）：把方法/属性取到绑定名后按名调用，绕过调用点白名单 ---
    "bind_format_then_call": "f = str.format\nresult = f('{0.__class__}', 1)",
    "bind_format_read_builtins": (
        "f = str.format\n"
        "result = f('{0.__globals__[__builtins__][__import__]}', join)"
    ),
    "bind_literal_format_then_call": "f = ''.format\nresult = f('{0.__class__}', 1)",
    "for_loop_bind_format_then_call": (
        "for f in [str.format]:\n    result = f('{0.__class__}', 1)"
    ),
    # 属性读取本身即拦（白名单在读取处生效），format_map / translate 同理
    "read_str_format": "result = str.format",
    "read_literal_format": "result = ''.format",
    "read_format_map": "result = '{}'.format_map",
    "read_str_translate": "result = str.translate",
    "read_dict_update": "result = code.update",
    # 即便取到的是白名单方法，绑定后按名调用也拒绝（可调用性来源追溯）
    "bind_whitelisted_method_then_call": "f = code.get\nresult = f('中', '')",
    # 属性赋值（可能给可达对象装上恶意属性/覆盖方法）同样拒绝
    "attribute_store": "str.join = len\nresult = 'x'",
}


@pytest.mark.parametrize("case", sorted(FORBIDDEN_RULE_SOURCES))
def test_validate_python_rule_rejects_forbidden_source(case):
    """非法规则在 AST 校验阶段被拒绝，错误信息包含规则名与被拒位置。"""
    with pytest.raises(CustomRuleSecurityError) as excinfo:
        validate_python_rule(FORBIDDEN_RULE_SOURCES[case], case)
    message = str(excinfo.value)
    assert f"'{case}'" in message, message
    assert "被沙箱拒绝" in message, message


def test_validate_python_rule_rejects_syntax_error():
    """语法错误也走同一条显式报错路径，不静默放行。"""
    with pytest.raises(CustomRuleSecurityError) as excinfo:
        validate_python_rule("result = = 1", "语法错误规则")
    assert "语法错误" in str(excinfo.value)


@pytest.mark.parametrize(
    "source",
    [
        "result = ''\n"
        "if len(vac) <= 3:\n"
        "\tfor char in vac:\n"
        "\t\tif char in code:\n"
        "\t\t\tresult += code[char][0]+code[char][1]",
        "result = join('', [code[c][0] for c in vac])",
        "result = ''.join(code[c][0] for c in vac)",
        "result = code.get(vac[0], '')",
        "out = []\n"
        "for i, ch in enumerate(vac):\n"
        "    out.append(code[ch][0])\n"
        "result = ''.join(out)",
    ],
)
def test_validate_python_rule_accepts_legal_source(source):
    """合法 Python 规则（含现有 flypy 模板）继续通过校验。"""
    assert validate_python_rule(source, "合法规则") is not None


# ---------------------------------------------------------------------------
# T27（T11-F3）：属性白名单必须在「读取」处生效，且绑定名调用要被追溯
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source",
    [
        "result = str.format",
        "result = ''.format",
        "result = '{}'.format_map",
        "result = str.translate",
        "result = code.update",
        "f = str.format\nresult = f('{0.__class__}', 1)",
    ],
)
def test_attribute_read_is_checked_by_whitelist_not_only_calls(source):
    """属性「读取」即过白名单：不得只在调用点检查（T11-F3 根因）。"""
    with pytest.raises(CustomRuleSecurityError) as excinfo:
        validate_python_rule(source, "属性读取规则")
    assert "禁止读取非白名单属性" in str(excinfo.value)


def test_binding_attribute_then_calling_by_name_is_rejected():
    """把属性表达式绑定到名字后再按名调用 → 拒绝（可调用性来源追溯）。

    对照组：绑定的是白名单内建函数（`f = len`）时仍允许调用，避免误伤合法写法。
    """
    with pytest.raises(CustomRuleSecurityError) as excinfo:
        validate_python_rule("f = code.get\nresult = f('中', '')", "绑定名规则")
    assert "禁止把属性取到名字 'f' 后再按名调用" in str(excinfo.value)

    assert validate_python_rule("f = len\nresult = str(f(vac))", "绑定内建规则")


def test_attribute_whitelist_excludes_c_level_format_mini_language():
    """白名单里不得存在会在 C 层解释格式串/做属性遍历的方法（守门用例）。"""
    for forbidden in ("format", "format_map", "translate", "maketrans", "__mod__"):
        assert forbidden not in ALLOWED_RULE_METHODS, forbidden


def test_percent_formatting_cannot_traverse_attributes():
    """`%` 格式化（str.__mod__ 路径）只按字面 key 做 mapping 取值，无属性遍历。

    `%` 运算符在 C 层实现，沙箱看不到格式串内容，因此必须证明它无法被用来做
    属性访问：`%(key)s` 里的 key 是**字面量**，只在右操作数上做一次 __getitem__。
    """
    # 格式串里的 "x.__class__" 被当作普通字典 key，不会去解析属性
    # （动态拼接格式串，避免 ruff 对源码里的 % 占位符做静态检查）
    literal_key_format = "%(" + "x.__class__" + ")s"
    assert literal_key_format % {"x.__class__": "LITERAL"} == "LITERAL"
    with pytest.raises(KeyError):
        _ = literal_key_format % {}
    # 右操作数不是 mapping 时直接 TypeError，同样不会做属性访问
    with pytest.raises(TypeError):
        _ = literal_key_format % "x"
    # 合法用途（元组/字典取值）仍被沙箱放行
    percent_rule = "result = '%s%s' % (vac, code.get('中', ''))"
    assert validate_python_rule(percent_rule, "百分号规则")


@patch("app.services.code_generator.WordRepository")
@patch("app.services.code_generator.get_db")
@patch("app.core.config_manager.config_manager")
def test_forbidden_python_rule_rejected_before_exec(
    mock_cm, mock_get_db, mock_repo_cls, tmp_path
):
    """恶意规则经 generate_code 全链路被拒，且校验发生在 exec 之前
    （落盘探针不存在）。"""
    canary = tmp_path / "pwned"
    content = f"import os\nopen({str(canary)!r}, 'w').close()\nresult = os.name"
    mock_get_db.side_effect = lambda: iter([Mock()])
    mock_cm.get.side_effect = lambda key, default=None: {
        "code_rule": "恶意规则",
        "custom_rules": {"恶意规则": {"content": content, "python_mode": True}},
    }.get(key, default)

    generator = CodeGenerator()
    generator.config = {"rule": "custom"}
    generator.repo.get_by_word.side_effect = [Mock(code="zh"), Mock(code="guo")]

    with pytest.raises(CustomRuleSecurityError) as excinfo:
        generator.generate_code("中国")

    message = str(excinfo.value)
    assert "恶意规则" in message and "import" in message, message
    assert not canary.exists(), "沙箱在 AST 校验前就执行了规则代码"


@patch("app.services.code_generator.WordRepository")
@patch("app.services.code_generator.get_db")
@patch("app.core.config_manager.config_manager")
def test_legal_python_rule_still_generates_code(mock_cm, mock_get_db, mock_repo_cls):
    """合法 Python 模式规则（与线上 flypy 同构）仍能生成编码（兼容性）。"""
    content = (
        "result = ''\n"
        "if len(vac) <= 3:\n"
        "    for char in vac:\n"
        "        if char in code:\n"
        "            result += code[char][0] + code[char][1]\n"
    )
    mock_get_db.side_effect = lambda: iter([Mock()])
    mock_cm.get.side_effect = lambda key, default=None: {
        "code_rule": "双拼",
        "custom_rules": {"双拼": {"content": content, "python_mode": True}},
    }.get(key, default)

    generator = CodeGenerator()
    generator.config = {"rule": "custom"}
    generator.repo.get_by_word.side_effect = [Mock(code="zh"), Mock(code="guo")]

    assert generator.generate_code("中国") == "zhgu"


@patch("app.services.code_generator.WordRepository")
@patch("app.services.code_generator.get_db")
@patch("app.core.config_manager.config_manager")
def test_sandbox_exposes_only_whitelisted_builtins(mock_cm, mock_get_db, mock_repo_cls):
    """沙箱命名空间内 __builtins__ 为空，白名单函数（join）可用、非白名单内建不可见。"""
    content = "result = join('', [code[c][0] for c in vac])"
    mock_get_db.side_effect = lambda: iter([Mock()])
    mock_cm.get.side_effect = lambda key, default=None: {
        "code_rule": "白名单",
        "custom_rules": {"白名单": {"content": content, "python_mode": True}},
    }.get(key, default)

    generator = CodeGenerator()
    generator.config = {"rule": "custom"}
    generator.repo.get_by_word.side_effect = [Mock(code="zh"), Mock(code="guo")]

    assert generator.generate_code("中国") == "zg"


def test_audit_python_mode_rules_reports_violations():
    """配置审计只做 AST 校验，返回非法规则说明、放过合法规则。"""
    problems = audit_python_mode_rules(
        {
            "坏规则": {"content": "import os", "python_mode": True},
            "好规则": {"content": "result = vac", "python_mode": True},
            "模板规则": {"content": "v[2] = s[1][1]", "python_mode": False},
        }
    )
    assert len(problems) == 1
    assert "坏规则" in problems[0]
    assert audit_python_mode_rules({}) == []


def test_confirm_python_mode_rules_requires_explicit_confirmation():
    """配置导入路径：存在 python_mode=true 时提示并必须由用户确认，不静默放行。"""
    rules = {"双拼": {"content": "result = vac", "python_mode": True}}

    with pytest.raises(PythonModeConfirmationRequired) as excinfo:
        confirm_python_mode_rules(rules, source="imported.json")
    assert "双拼" in str(excinfo.value)
    assert "确认" in str(excinfo.value)

    prompts = []
    confirmed = confirm_python_mode_rules(
        rules,
        confirm=lambda prompt: prompts.append(prompt) or True,
        source="imported.json",
    )
    assert confirmed == ["双拼"]
    assert len(prompts) == 1 and "双拼" in prompts[0]

    assert confirm_python_mode_rules(rules, confirm=lambda prompt: False) == []
    # 没有 python_mode 规则时不打扰用户
    assert (
        confirm_python_mode_rules(
            {"模板": {"content": "v[2] = s[1][1]", "python_mode": False}}
        )
        == []
    )


def test_confirm_python_mode_rules_rejects_forbidden_content():
    """导入路径上的确认闸门同样先过 AST 校验：非法内容立即抛错。"""
    rules = {"坏": {"content": "import os", "python_mode": True}}
    with pytest.raises(CustomRuleSecurityError):
        confirm_python_mode_rules(
            rules, confirm=lambda prompt: True, source="imported.json"
        )
