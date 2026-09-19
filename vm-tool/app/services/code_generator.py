"""编码生成服务"""
import ast
import logging
from collections.abc import Callable
from typing import Any

from ..dal.database import get_db
from ..dal.repositories import WordRepository

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 自定义规则沙箱（P0-3：消除 python_mode 规则的任意代码执行）
#
# 规则内容来自可导入导出的 config.json（custom_rules[*].content + python_mode=true），
# 因此「导入一份他人配置」等价于「以本机权限执行任意代码」。这里用 **AST 结构白名单**
# 判定取代字符串黑名单（不存在 `import` 关键字检测这类可绕过的做法）：解析后的语法树
# 中出现任何未列出的节点类型、以 `_` 开头/`__` 结尾的名字或属性、非白名单的属性读取与
# 方法调用、非白名单函数调用，一律拒绝执行并抛出 CustomRuleSecurityError。
# 属性白名单必须在「读取」处生效（T11-F3：只在调用点检查会被
# `f = str.format; f('{0.__class__}', 1)` 这类「取到绑定名再按名调用」绕过）；
# 执行时 __builtins__ 置空，只注入白名单内建函数。
# ---------------------------------------------------------------------------


class CustomRuleSecurityError(ValueError):
    """自定义规则未通过沙箱校验（AST 白名单）。"""


class PythonModeConfirmationRequired(CustomRuleSecurityError):
    """配置中存在 python_mode=true 的规则，需用户显式确认后才允许执行。"""


def _sandbox_join(separator, items=None):
    """沙箱版 join：join(iterable) 或 join(separator, iterable)。"""
    if items is None:
        items, separator = separator, ""
    return str(separator).join(str(item) for item in items)


# exec 时注入的内建函数白名单：其余内建一律不可见（__builtins__ 置空）
ALLOWED_RULE_BUILTINS: dict[str, Any] = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "tuple": tuple,
    "dict": dict,
    "set": set,
    "frozenset": frozenset,
    "enumerate": enumerate,
    "range": range,
    "zip": zip,
    "sorted": sorted,
    "reversed": reversed,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
    "any": any,
    "all": all,
    "chr": chr,
    "ord": ord,
    "divmod": divmod,
    "pow": pow,
    "join": _sandbox_join,
}

# 规则运行时预先注入的变量名
RULE_RUNTIME_NAMES = frozenset({"vac", "code", "result"})

# 允许读取与调用的属性白名单：对「属性读取」与「方法调用」**同时**生效。
# T11-F3 教训：只在调用点检查不够——`f = str.format` 先把方法取到名字上，再
# `f('{0.__class__}', 1)` 按名调用即可绕开调用点检查；而 format 的迷你语言是在 C 层
# 做属性/索引访问，验证器看不到格式串里的名字，所以「取不到」远比「拦调用」可靠。
# 集合内只保留纯值级方法；`str.format` / `str.format_map` / `str.translate`
# 这类会解释格式串做属性访问的方法不在集合内（连读取都不允许）。
ALLOWED_RULE_METHODS = frozenset(
    {
        "get",
        "keys",
        "values",
        "items",
        "join",
        "split",
        "strip",
        "lstrip",
        "rstrip",
        "replace",
        "append",
        "extend",
        "add",
        "upper",
        "lower",
        "startswith",
        "endswith",
        "index",
        "count",
        "sort",
        "reverse",
        "pop",
    }
)

# 允许出现的 AST 节点类型（白名单；未列出的节点一律拒绝）
_ALLOWED_RULE_NODES = (
    ast.Module,
    ast.Expr,
    ast.Assign,
    ast.AugAssign,
    ast.For,
    ast.If,
    ast.Break,
    ast.Continue,
    ast.Pass,
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    ast.IfExp,
    ast.Call,
    ast.Name,
    ast.Constant,
    ast.Attribute,
    ast.Subscript,
    ast.Slice,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Set,
    ast.Starred,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
    ast.comprehension,
    ast.JoinedStr,
    ast.FormattedValue,
    ast.FunctionDef,
    ast.Return,
    ast.arguments,
    ast.arg,
    ast.keyword,
)

# 常见危险节点的可读原因（未列出的节点回落到通用提示）
_FORBIDDEN_NODE_HINTS: dict[type, str] = {
    ast.While: "while 循环无法保证终止",
    ast.Global: "global 声明",
    ast.Nonlocal: "nonlocal 声明",
    ast.Delete: "del 语句",
    ast.Lambda: "lambda 表达式",
    ast.ClassDef: "class 定义",
    ast.Try: "try 语句",
    ast.With: "with 语句",
    ast.Raise: "raise 语句",
    ast.Assert: "assert 语句",
    ast.Import: "import 导入",
    ast.ImportFrom: "from ... import 导入",
    ast.AsyncFunctionDef: "async 函数",
    ast.Await: "await 表达式",
    ast.Yield: "yield 表达式",
    ast.YieldFrom: "yield from 表达式",
    ast.NamedExpr: "海象运算符 :=",
}
for _optional_node in ("Match", "TryStar"):
    _node_cls = getattr(ast, _optional_node, None)
    if _node_cls is not None:
        _FORBIDDEN_NODE_HINTS[_node_cls] = f"{_optional_node} 语句"


def _rule_reject(rule_name: str, node: ast.AST, detail: str) -> CustomRuleSecurityError:
    """构造带规则名与行号的拒绝错误。"""
    lineno = getattr(node, "lineno", None)
    where = f"第 {lineno} 行" if lineno else "位置未知"
    return CustomRuleSecurityError(
        f"自定义规则 '{rule_name}' 被沙箱拒绝（{where}）：{detail}"
    )


def _collect_bound_names(tree: ast.AST) -> set:
    """收集规则内自行绑定的名字（赋值目标 / for 目标 / 推导式目标 / 函数名与参数）。"""
    bound: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bound.add(node.id)
        elif isinstance(node, ast.FunctionDef):
            bound.add(node.name)
            args = node.args
            for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
                bound.add(arg.arg)
            for arg in (args.vararg, args.kwarg):
                if arg is not None:
                    bound.add(arg.arg)
    return bound


def _collect_attribute_bound_names(tree: ast.AST) -> set:
    """收集「由属性表达式取得」的名字（`f = str.format` / `for f in [code.get]:`）。

    T11-F3：属性表达式一旦被绑定到名字，后续 `f(...)` 是按名调用，不再经过
    属性白名单。这里把这类绑定名收集起来，调用时直接拒绝（可调用性的来源追溯）。
    """
    names: set = set()

    def _store_targets(node: ast.AST) -> set:
        return {
            child.id
            for child in ast.walk(node)
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store)
        }

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(child, ast.Attribute) for child in ast.walk(node.value)
        ):
            names |= _store_targets(node)
        elif isinstance(node, ast.For) and any(
            isinstance(child, ast.Attribute) for child in ast.walk(node.iter)
        ):
            names |= _store_targets(node.target)
    return names


def validate_python_rule(source: str, rule_name: str = "<未命名>") -> ast.Module:
    """按 AST 结构校验 python_mode 规则。

    校验通过返回语法树；不合法时抛出 CustomRuleSecurityError（说明规则名、行号与
    被拒原因）。这里只做结构判定，不做任何字符串黑名单匹配。
    """
    if not isinstance(source, str) or not source.strip():
        raise CustomRuleSecurityError(f"自定义规则 '{rule_name}' 内容为空，拒绝执行。")
    try:
        tree = ast.parse(source, filename=f"<custom_rule:{rule_name}>", mode="exec")
    except SyntaxError as exc:
        raise CustomRuleSecurityError(
            f"自定义规则 '{rule_name}' 语法错误（第 {exc.lineno} 行）：{exc.msg}"
        ) from exc

    bound = _collect_bound_names(tree)
    callable_names = set(ALLOWED_RULE_BUILTINS) | bound
    attribute_bound_names = _collect_attribute_bound_names(tree)

    for node in ast.walk(tree):
        # 1) 导入语句：AST 结构判定，直接拒绝
        if isinstance(node, ast.Import | ast.ImportFrom):
            names = ", ".join(alias.name for alias in node.names)
            kind = "import" if isinstance(node, ast.Import) else "from ... import"
            raise _rule_reject(rule_name, node, f"禁止导入模块（{kind} {names}）")
        # 2) 属性：白名单在「读取」处生效（不能只在调用点拦，见 T11-F3）；
        #    下划线/双下划线属性（__globals__ / __class__ / __subclasses__）单独给原因
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_") or node.attr.endswith("__"):
                raise _rule_reject(
                    rule_name, node, f"禁止访问下划线/双下划线属性 '.{node.attr}'"
                )
            if isinstance(node.ctx, ast.Store):
                raise _rule_reject(rule_name, node, f"禁止给属性赋值 '.{node.attr}'")
            if node.attr not in ALLOWED_RULE_METHODS:
                raise _rule_reject(
                    rule_name,
                    node,
                    f"禁止读取非白名单属性 '.{node.attr}'"
                    "（属性白名单必须在读取处生效，否则可先取到名字再按名调用）",
                )
        # 3) 调用：仅允许白名单函数与白名单方法，禁止对表达式结果直接调用
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id in attribute_bound_names:
                    raise _rule_reject(
                        rule_name,
                        node,
                        f"禁止把属性取到名字 '{func.id}' 后再按名调用"
                        "（绕过属性/方法白名单的 T11-F3 路径）",
                    )
                if func.id not in callable_names:
                    raise _rule_reject(
                        rule_name, node, f"禁止调用非白名单函数 '{func.id}()'"
                    )
            elif isinstance(func, ast.Attribute):
                if func.attr not in ALLOWED_RULE_METHODS:
                    raise _rule_reject(
                        rule_name, node, f"禁止调用非白名单方法 '.{func.attr}()'"
                    )
            else:
                raise _rule_reject(rule_name, node, "禁止对表达式结果直接调用")
        # 4) 运算符与上下文节点
        if isinstance(node, ast.operator | ast.unaryop | ast.boolop | ast.cmpop):
            continue
        if isinstance(node, ast.expr_context):
            if not isinstance(node, ast.Load | ast.Store):
                raise _rule_reject(
                    rule_name, node, f"禁止的上下文 {type(node).__name__}"
                )
            continue
        # 5) 节点类型白名单
        if not isinstance(node, _ALLOWED_RULE_NODES):
            hint = _FORBIDDEN_NODE_HINTS.get(
                type(node), f"不支持的语法节点 {type(node).__name__}"
            )
            raise _rule_reject(rule_name, node, f"禁止的语法：{hint}")

    # 6) 名字白名单：白名单内建 / 运行时注入变量 / 规则内自行绑定的名字
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Store):
            if node.id in callable_names or node.id in RULE_RUNTIME_NAMES:
                continue
            if node.id.startswith("_"):
                raise _rule_reject(
                    rule_name, node, f"禁止访问下划线/双下划线名字 '{node.id}'"
                )
            raise _rule_reject(rule_name, node, f"禁止使用未定义名字 '{node.id}'")
    return tree


def find_python_mode_rules(custom_rules: dict[str, Any] | None) -> list[str]:
    """返回配置中启用 Python 模式（python_mode=true）的规则名列表。"""
    names: list[str] = []
    if not isinstance(custom_rules, dict):
        return names
    for name, data in custom_rules.items():
        if isinstance(data, dict) and data.get("python_mode", False):
            names.append(name)
    return names


def audit_python_mode_rules(custom_rules: dict[str, Any] | None) -> list[str]:
    """审计配置中的所有 Python 模式规则：只做 AST 校验、不执行。

    Returns:
        每条被拒绝规则的错误说明（空列表表示全部合法）。
    """
    problems: list[str] = []
    if not isinstance(custom_rules, dict):
        return problems
    for name in find_python_mode_rules(custom_rules):
        try:
            validate_python_rule(custom_rules[name].get("content", ""), name)
        except CustomRuleSecurityError as exc:
            problems.append(str(exc))
    return problems


def confirm_python_mode_rules(
    custom_rules: dict[str, Any] | None,
    *,
    confirm: Callable[[str], bool] | None = None,
    source: str = "config.json",
) -> list[str]:
    """配置导入路径的 Python 模式确认闸门。

    导入/加载配置时若存在 python_mode=true 的规则：先逐条做 AST 校验（非法立即抛
    CustomRuleSecurityError，不静默放行），再显式提示并要求用户逐条确认。
    `confirm` 为 None（无交互通道）时抛 PythonModeConfirmationRequired —— 绝不静默执行。

    Returns:
        用户确认通过的规则名列表；配置中没有 Python 模式规则时返回空列表且不打扰用户。
    """
    names = find_python_mode_rules(custom_rules)
    if not names:
        return []
    if not isinstance(custom_rules, dict):
        return []
    for name in names:
        validate_python_rule(custom_rules[name].get("content", ""), name)
    logger.warning(
        "配置 %s 中发现 %d 条 Python 模式规则（将以本机权限执行代码）：%s",
        source,
        len(names),
        ", ".join(names),
    )
    if confirm is None:
        raise PythonModeConfirmationRequired(
            f"{source} 中的规则 {', '.join(names)} 启用了 Python 模式，"
            "会在本机执行任意代码；请确认来源可信后再导入。"
        )
    confirmed: list[str] = []
    for name in names:
        prompt = f"{source}: 规则 '{name}' 启用 Python 模式，将执行任意代码，是否继续？"
        if confirm(prompt):
            confirmed.append(name)
        else:
            logger.warning(
                "用户拒绝导入 Python 模式规则 '%s'（来源：%s）", name, source
            )
    return confirmed


class CodeGenerator:
    """编码生成器"""

    def __init__(self) -> None:
        """初始化编码生成器"""
        # 显式创建会话（持有者负责 close）；不再对生成器取一次 next
        self.db = get_db()
        self.repo = WordRepository(self.db)
        self.config: dict[str, Any] = {
            "rule": "first_letter",  # first_letter, all_letters, custom
            "separator": "",  # 编码分隔符
        }

    def set_config(self, config: dict[str, Any]) -> None:
        """设置编码生成配置

        Args:
            config: 配置字典
        """
        self.config.update(config)

    def get_config(self) -> dict[str, Any]:
        """获取编码生成配置

        Returns:
            配置字典
        """
        return self.config

    def generate_code(self, word: str) -> str:
        """生成编码

        Args:
            word: 词条

        Returns:
            生成的编码
        """
        try:
            # 尝试根据字表中的字的编码计算
            code = self.generate_code_from_chars(word)
            if code:
                return code

            # 如果 generate_code_from_chars 返回空字符串，检查是否是自定义规则模式
            # 如果是自定义规则模式，尝试直接执行自定义规则
            if self.config["rule"] == "custom":
                try:
                    # 为每个字生成默认编码
                    char_codes = []
                    for char in word:
                        # 为每个字符生成2个字符的默认编码
                        char_code = "".join(
                            [chr((ord(char) + i) % 26 + 97) for i in range(2)]
                        )
                        char_codes.append(char_code)

                    # 执行自定义规则
                    code = self._execute_custom_rule(word, char_codes)
                    if code:
                        return code
                except CustomRuleSecurityError:
                    # 沙箱拒绝必须显式上抛，不得被回退逻辑吞掉
                    raise
                except Exception as e:
                    logger.error(f"自定义规则回退执行失败: {e}")
                    # 继续使用默认方法

            # 默认方法
            # 对于单个字符和词语，都生成多个字符的编码
            if len(word) == 1:
                # 为单个字符生成编码
                char = word[0]
                # 使用字符的ASCII码生成编码
                code = "".join([chr((ord(char) + i) % 26 + 97) for i in range(4)])
                return code
            else:
                # 对于词语，为每个字符生成多个字符的编码
                code = ""
                for char in word:
                    # 为每个字符生成编码
                    char_code = "".join(
                        [chr((ord(char) + i) % 26 + 97) for i in range(2)]
                    )  # 每个字生成2个字符
                    code += char_code
                return code
        except CustomRuleSecurityError:
            # 沙箱拒绝必须显式上抛（含规则名与行号），不得静默返回空字符串
            raise
        except Exception as e:
            logger.error(f"生成编码失败: {e}")
            return ""

    def generate_code_from_chars(self, word: str) -> str:
        """根据字表中的字的编码计算词的编码

        Args:
            word: 词条

        Returns:
            生成的编码
        """
        try:
            char_codes = []

            # 获取每个字的编码
            for char in word:
                char_word = self.repo.get_by_word(char)
                if char_word:
                    char_codes.append(char_word.code)
                else:
                    # 如果字表中没有这个字，使用默认方法生成编码
                    # 为每个字符生成2个字符的编码
                    char_code = "".join(
                        [chr((ord(char) + i) % 26 + 97) for i in range(2)]
                    )
                    char_codes.append(char_code)

            # 根据配置的规则生成编码
            if self.config["rule"] == "first_letter":
                # 取每个字编码的第一个字符
                code = self.config["separator"].join([c[0] for c in char_codes])
            elif self.config["rule"] == "all_letters":
                # 拼接所有字的编码
                code = self.config["separator"].join(char_codes)
            elif self.config["rule"] == "custom":
                # 自定义规则
                code = self._execute_custom_rule(word, char_codes)
            else:
                # 默认规则
                code = self.config["separator"].join([c[0] for c in char_codes])

            # 移除编码长度限制
            return code
        except CustomRuleSecurityError:
            # 沙箱拒绝必须显式上抛，不得静默返回空字符串
            raise
        except Exception as e:
            logger.error(f"根据字表生成编码失败: {e}")
            return ""

    def _execute_custom_rule(self, word: str, char_codes: list[str]) -> str:
        """执行自定义编码规则

        Args:
            word: 词条
            char_codes: 每个字的编码列表

        Returns:
            生成的编码
        """
        try:
            # 读取自定义规则配置
            from ..core.config_manager import config_manager

            current_rule = config_manager.get("code_rule", "默认规则")
            custom_rules = config_manager.get("custom_rules", {})

            # 获取当前规则的内容和Python模式状态
            rule_name = current_rule
            rule_data = custom_rules.get(current_rule, {})
            if isinstance(rule_data, str):
                # 旧格式，转换为新格式
                custom_rule_content = rule_data
                python_mode = False
            else:
                # 新格式
                custom_rule_content = rule_data.get("content", "")
                python_mode = rule_data.get("python_mode", False)

            # 如果没有指定规则或规则不存在，查找默认规则
            if not custom_rule_content:
                # 查找默认规则配置
                default_rule_name = config_manager.get("default_code_rule", "")
                if default_rule_name in custom_rules:
                    rule_name = default_rule_name
                    default_rule_data = custom_rules[default_rule_name]
                    if isinstance(default_rule_data, str):
                        custom_rule_content = default_rule_data
                        python_mode = False
                    else:
                        custom_rule_content = default_rule_data.get("content", "")
                        python_mode = default_rule_data.get("python_mode", False)
                else:
                    # 如果没有自定义规则，使用默认规则
                    return self.config["separator"].join([c[0] for c in char_codes])

            word_length = len(word)

            # 检查是否启用Python模式
            if python_mode:
                # Python模式：在受限沙箱中执行Python代码生成编码
                # 先做 AST 结构校验（拒绝 import / 下划线属性 / 非白名单
                # 名字与方法调用），再以 __builtins__ 置空的命名空间执行。
                validate_python_rule(custom_rule_content, rule_name)
                logger.warning(
                    "将以 Python 模式执行自定义规则 '%s'（来源：config.json，"
                    "内容可信度自负）；如需在导入配置时要求用户确认，"
                    "请使用 confirm_python_mode_rules()",
                    rule_name,
                )
                try:
                    # 准备变量
                    vac = word  # vac变量为单条词条
                    code: dict[str, str] = {}
                    for i, char in enumerate(word):
                        code[char] = char_codes[i] if i < len(char_codes) else ""

                    # 执行Python代码（沙箱命名空间：globals 与 locals 为同一映射，
                    # 以便推导式/函数体也能看到 vac/code/result）
                    # 结果存储在 result 变量中
                    sandbox: dict[str, Any] = {"__builtins__": {}}
                    sandbox.update(ALLOWED_RULE_BUILTINS)
                    sandbox.update({"vac": vac, "code": code, "result": ""})
                    exec(custom_rule_content, sandbox, sandbox)  # noqa: S102 - 已过 AST 白名单校验
                    result = sandbox.get("result", "")

                    # 确保结果是字符串
                    if not isinstance(result, str):
                        result = str(result)

                    return result
                except CustomRuleSecurityError:
                    # 沙箱拒绝必须显式上抛，不得回退成默认编码
                    raise
                except Exception as e:
                    logger.error(f"执行Python模式编码规则失败: {e}")
                    logger.error(f"字符编码: {code}")
                    logger.error(f"规则内容: {custom_rule_content}")
                    # 失败时使用默认规则
                    return self.config["separator"].join([c[0] for c in char_codes])
            else:
                # 普通模式：使用原有规则解析逻辑
                # 解析规则
                rules = {}
                plus_rules = {}
                for line in custom_rule_content.strip().split("\n"):
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        # 提取长度
                        if key.startswith("v[") and key.endswith("]"):
                            length_str = key[2:-1]
                            # 处理v[4+]格式的规则
                            if length_str.endswith("+"):
                                try:
                                    min_length = int(length_str[:-1])
                                    plus_rules[min_length] = value
                                except (TypeError, ValueError) as exc:
                                    logger.debug(
                                        "忽略无法解析的 v[%s+] 规则长度 '%s': %s",
                                        length_str[:-1],
                                        length_str,
                                        exc,
                                    )
                            else:
                                try:
                                    length = int(length_str)
                                    rules[length] = value
                                except (TypeError, ValueError) as exc:
                                    logger.debug(
                                        "忽略无法解析的 v[N] 规则长度 '%s': %s",
                                        length_str,
                                        exc,
                                    )

                # 找到匹配的规则
                rule = None
                if word_length in rules:
                    rule = rules[word_length]
                else:
                    # 检查是否匹配v[4+]格式的规则
                    for min_length, rule_content in plus_rules.items():
                        if word_length >= min_length:
                            rule = rule_content
                            break

                if rule:
                    # 替换s[i][j]为实际编码
                    result = rule

                    # 处理s[i][j]表示第i个字的第j个编码字符（1-based索引）
                    for i in range(word_length):
                        for j in range(len(char_codes[i])):
                            # 1-based索引（从1开始）
                            placeholder = f"s[{i+1}][{j+1}]"
                            if placeholder in result:
                                result = result.replace(placeholder, char_codes[i][j])

                    # 处理s[-1][j]表示最后一个字的编码
                    if word_length > 0:
                        last_index = word_length - 1
                        for j in range(len(char_codes[last_index])):
                            placeholder = f"s[-1][{j+1}]"
                            if placeholder in result:
                                result = result.replace(
                                    placeholder, char_codes[last_index][j]
                                )

                    # 处理连接符（移除+号）
                    result = result.replace("+", "")
                    # 移除所有空格
                    result = result.replace(" ", "")

                    # 确保所有占位符都被替换
                    import re

                    # 查找所有未被替换的s[i][j]格式的占位符
                    placeholders = re.findall(r"s\[\d+\]\[\d+\]|s\[-1\]\[\d+\]", result)
                    for placeholder in placeholders:
                        # 移除未被替换的占位符
                        result = result.replace(placeholder, "")

                    return result
                else:
                    # 如果没有匹配的规则，使用默认规则
                    return self.config["separator"].join([c[0] for c in char_codes])
        except CustomRuleSecurityError:
            # 沙箱拒绝必须显式上抛（含规则名/行号/被拒原因），不得回退成默认编码
            raise
        except Exception as e:
            logger.error(f"执行自定义规则失败: {e}")
            # 失败时使用默认规则
            return self.config["separator"].join([c[0] for c in char_codes])

    def validate_code(self, code: str) -> bool:
        """验证编码

        Args:
            code: 编码

        Returns:
            是否有效
        """
        try:
            # 简单的编码验证逻辑
            return isinstance(code, str) and len(code) > 0
        except Exception as e:
            logger.error(f"验证编码失败: {e}")
            return False


if __name__ == "__main__":
    # 测试编码生成器
    generator = CodeGenerator()
    # 测试默认规则
    logger.info("测试默认规则:")
    logger.info(generator.generate_code("测试", ["ce", "shi"]))
    # 测试自定义规则
    logger.info("\n测试自定义规则:")
    # 模拟自定义规则，使用1-based索引
    from ..core.config_manager import config_manager

    config_manager.set(
        "custom_rules", {"测试规则": "v[2] = s[1][1] + s[1][2] + s[2][1] + s[2][2]"}
    )
    config_manager.set("code_rule", "测试规则")
    logger.info(generator.generate_code("测试", ["ce", "shi"]))
    # 测试v[4+]语法
    logger.info("\n测试v[4+]语法:")
    config_manager.set(
        "custom_rules", {"测试规则": "v[4+] = s[1][1] + s[2][1] + s[3][1] + s[4][1]"}
    )
    logger.info(generator.generate_code("测试测试", ["ce", "shi", "ce", "shi"]))
