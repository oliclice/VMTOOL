"""编码规则设置面板"""

from PyQt6.QtWidgets import (QFormLayout, QLabel, QComboBox, QHBoxLayout,
                             QPushButton, QLineEdit, QTextEdit, QWidget,
                             QVBoxLayout, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from .base_panel import SettingsPanel
from app.core.config_manager import config_manager
from ..theme_colors import get_status_color


# 语法帮助文本
SYNTAX_HELP_TEXT = """编码规则语法说明：

普通模式：
v[n] = 表达式 表示词长度为n时的编码规则

v[n+] = 表达式 表示词长度为n及以上时的编码规则（如v[4+]表示四个字及以上的词）

s[i][j] 表示第i个字的第j个编码字符（1-based索引，从1开始）

s[-1][j] 表示词的最后一个字的第j个编码字符

+ 表示连接字符串

Python模式：
开启Python模式后，可以使用Python代码来生成编码

默认变量：
- vac：单条词条
- code['字']：表示字的编码（例如code['测']表示"测"字的编码）
- result：用于存储生成的编码

默认编码规则：
在规则名称后添加 [default] 后缀，表示该规则为默认编码规则，用于加词时自动计算编码

Python模式标识：
在规则名称后添加 *python 后缀，表示该规则启用了Python模式

普通模式示例：
v[2] = s[1][1] + s[1][2] + s[2][1] + s[2][2]
表示词长度为2时，取前两个字的前两个编码

v[3] = s[1][1] + s[2][1] + s[3][1]
表示词长度为3时，取前三个字的每个字第一个编码

v[4+] = s[1][1] + s[2][1] + s[3][1] + s[4][1]
表示词长度为4及以上时，取前四个字的每个字第一个编码

v[2] = s[1][1] + s[-1][1]
表示词长度为2时，取第一个字和最后一个字的第一个编码

Python模式示例：
# 取每个字的第一个编码
result = ''
for char in vac:
    if char in code:
        result += code[char][0]

# 取第一个字和最后一个字的编码
if len(vac) >= 2:
    result = code[vac[0]] + code[vac[-1]]
else:
    result = code.get(vac[0], '')

# 自定义复杂逻辑
if len(vac) == 2:
    result = code[vac[0]][:2] + code[vac[1]][:2]
elif len(vac) == 3:
    result = code[vac[0]][0] + code[vac[1]][0] + code[vac[2]][:2]
elif len(vac) >= 4:
    result = code[vac[0]][0] + code[vac[1]][0] + code[vac[2]][0] + code[vac[3]][0]"""


class CodeRulesPanel(SettingsPanel):
    """编码规则设置面板 - 规则管理、编辑、Python模式"""

    panel_name = "编码规则"
    panel_description = "管理编码规则，支持普通模式和Python模式"

    def _setup_ui(self):
        # 规则选择
        rule_layout = QFormLayout()
        rule_layout.setSpacing(12)

        self.rule_combo = QComboBox()
        rule_layout.addRow("编码规则:", self.rule_combo)

        self._main_layout.addLayout(rule_layout)

        # 自定义编码规则区域
        custom_rule_group = QGroupBox("自定义编码规则")
        custom_rule_layout = QVBoxLayout()

        # 规则名称
        rule_name_layout = QHBoxLayout()
        self.rule_name_edit = QLineEdit()
        rule_name_layout.addWidget(QLabel("规则名称:"))
        rule_name_layout.addWidget(self.rule_name_edit)
        custom_rule_layout.addLayout(rule_name_layout)

        # Python模式勾选框
        self.python_mode_checkbox = QPushButton("开启Python模式")
        self.python_mode_checkbox.setCheckable(True)
        custom_rule_layout.addWidget(self.python_mode_checkbox)

        # 规则内容
        self.rule_content_edit = QTextEdit()
        self.rule_content_edit.setTabStopDistance(20)

        # 动态设置最小高度为屏幕高度的1/2
        screen = QApplication.primaryScreen()
        screen_height = screen.size().height()
        min_height = int(screen_height * 0.5)
        self.rule_content_edit.setMinimumHeight(min_height)
        self.rule_content_edit.setMinimumWidth(400)
        self.rule_content_edit.setFont(QFont("Monospace", 10))
        self.rule_content_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        custom_rule_layout.addWidget(QLabel("规则内容:"))
        custom_rule_layout.addWidget(self.rule_content_edit)

        # 语法说明
        syntax_layout = QHBoxLayout()
        syntax_button = QPushButton("?")
        syntax_button.setFixedSize(20, 20)
        success_color = get_status_color("success")
        syntax_button.setStyleSheet(
            f"QPushButton {{ border-radius: 10px; background-color: {success_color}; color: white; }}"
        )
        syntax_button.clicked.connect(self._show_syntax_help)

        syntax_layout.addWidget(QLabel("语法说明:"))
        syntax_layout.addWidget(syntax_button)
        syntax_layout.addStretch()
        custom_rule_layout.addLayout(syntax_layout)

        # 操作按钮
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("添加规则")
        self.delete_button = QPushButton("删除规则")
        self.set_default_button = QPushButton("设为默认")

        self.add_button.clicked.connect(self._add_rule)
        self.delete_button.clicked.connect(self._delete_rule)
        self.set_default_button.clicked.connect(self._set_default_rule)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.set_default_button)
        custom_rule_layout.addLayout(button_layout)

        self._main_layout.addWidget(custom_rule_group)

        # 加载当前值
        self._load_current_values()

    def _connect_signals(self):
        self.rule_combo.currentTextChanged.connect(self._on_rule_changed)

    def _load_current_values(self):
        """从 config_manager 加载当前值"""
        # 加载自定义规则列表
        rules = config_manager.get("custom_rules", {})

        # 检查规则格式是否为新格式，如果是旧格式则转换
        new_rules = {}
        for rule_name, rule_value in rules.items():
            if isinstance(rule_value, str):
                # 旧格式，转换为新格式
                new_rules[rule_name] = {
                    "content": rule_value,
                    "python_mode": False
                }
            else:
                # 新格式，直接使用
                new_rules[rule_name] = rule_value
        rules = new_rules
        config_manager.set("custom_rules", rules)

        rule_names = list(rules.keys())
        if not rule_names:
            # 默认规则
            rules = {
                "默认规则": {
                    "content": "v[2]=s[1][1]+s[1][2]+s[2][1]+s[2][2]\nv[3]=s[1][1]+s[2][1]+s[3][1]",
                    "python_mode": False
                }
            }
            config_manager.set("custom_rules", rules)
            rule_names = list(rules.keys())

        # 为默认规则和Python模式添加标识
        default_rule = config_manager.get("default_code_rule", "")
        self.rule_combo.clear()
        for name in rule_names:
            display_name = name
            if rules[name].get("python_mode", False):
                display_name += " *python"
            if name == default_rule:
                display_name += " [默认]"
            self.rule_combo.addItem(display_name)

        # 设置当前规则
        current_rule = config_manager.get("code_rule", rule_names[0] if rule_names else "")
        if current_rule in rule_names:
            display_name = current_rule
            if rules[current_rule].get("python_mode", False):
                display_name += " *python"
            if current_rule == default_rule:
                display_name += " [默认]"
            self.rule_combo.setCurrentText(display_name)

            # 初始化显示当前规则内容和Python模式状态
            self.rule_name_edit.setText(current_rule)
            self.rule_content_edit.setPlainText(rules.get(current_rule, {}).get("content", ""))
            self.python_mode_checkbox.setChecked(rules.get(current_rule, {}).get("python_mode", False))

    def _on_rule_changed(self, text):
        """规则选择变更"""
        # 移除默认标识和Python模式标识
        rule_name = text
        if " [默认]" in rule_name:
            rule_name = rule_name.replace(" [默认]", "")
        if " *python" in rule_name:
            rule_name = rule_name.replace(" *python", "")

        config_manager.set("code_rule", rule_name)

        # 切换规则时，自动填充规则名称、内容和Python模式状态
        rules = config_manager.get("custom_rules", {})
        self.rule_name_edit.setText(rule_name)
        self.rule_content_edit.setPlainText(rules.get(rule_name, {}).get("content", ""))
        self.python_mode_checkbox.setChecked(rules.get(rule_name, {}).get("python_mode", False))

    def _add_rule(self):
        """添加规则"""
        rule_name = self.rule_name_edit.text().strip()
        rule_content = self.rule_content_edit.toPlainText().strip()
        python_mode = self.python_mode_checkbox.isChecked()

        if rule_name and rule_content:
            rules = config_manager.get("custom_rules", {})
            # 保存规则内容和Python模式状态
            rules[rule_name] = {
                "content": rule_content,
                "python_mode": python_mode
            }
            config_manager.set("custom_rules", rules)

            # 更新下拉框
            self._refresh_rule_combo(rule_name)

            parent = self.parent()
            while parent and not hasattr(parent, 'show_toast'):
                parent = parent.parent() if hasattr(parent, 'parent') else None
            if parent and hasattr(parent, 'show_toast'):
                parent.show_toast(f"规则 '{rule_name}' 添加成功")
        else:
            parent = self.parent()
            while parent and not hasattr(parent, 'show_toast'):
                parent = parent.parent() if hasattr(parent, 'parent') else None
            if parent and hasattr(parent, 'show_toast'):
                parent.show_toast("请输入规则名称和内容")

    def _delete_rule(self):
        """删除规则"""
        current_rule = self.rule_combo.currentText()
        # 移除默认标识和Python模式标识
        if " [默认]" in current_rule:
            current_rule = current_rule.replace(" [默认]", "")
        if " *python" in current_rule:
            current_rule = current_rule.replace(" *python", "")

        if current_rule:
            rules = config_manager.get("custom_rules", {})
            if current_rule in rules:
                # 如果删除的是默认规则，清除默认规则设置
                if current_rule == config_manager.get("default_code_rule", ""):
                    config_manager.set("default_code_rule", "")

                del rules[current_rule]
                config_manager.set("custom_rules", rules)

                # 更新下拉框
                self._refresh_rule_combo()

                parent = self.parent()
                while parent and not hasattr(parent, 'show_toast'):
                    parent = parent.parent() if hasattr(parent, 'parent') else None
                if parent and hasattr(parent, 'show_toast'):
                    parent.show_toast(f"规则 '{current_rule}' 删除成功")

    def _set_default_rule(self):
        """设为默认规则"""
        current_rule = self.rule_combo.currentText()
        # 移除默认标识和Python模式标识
        if " [默认]" in current_rule:
            current_rule = current_rule.replace(" [默认]", "")
        if " *python" in current_rule:
            current_rule = current_rule.replace(" *python", "")

        if current_rule:
            # 设置默认规则
            config_manager.set("default_code_rule", current_rule)

            # 更新下拉框
            self._refresh_rule_combo(current_rule)

            parent = self.parent()
            while parent and not hasattr(parent, 'show_toast'):
                parent = parent.parent() if hasattr(parent, 'parent') else None
            if parent and hasattr(parent, 'show_toast'):
                parent.show_toast(f"规则 '{current_rule}' 已设为默认")

    def _refresh_rule_combo(self, select_rule=None):
        """刷新规则下拉框"""
        rules = config_manager.get("custom_rules", {})
        rule_names = list(rules.keys())
        default_rule = config_manager.get("default_code_rule", "")

        self.rule_combo.clear()
        for name in rule_names:
            display_name = name
            if rules[name].get("python_mode", False):
                display_name += " *python"
            if name == default_rule:
                display_name += " [默认]"
            self.rule_combo.addItem(display_name)

        if select_rule:
            # 找到并选中指定规则
            for i in range(self.rule_combo.count()):
                item_text = self.rule_combo.itemText(i)
                if select_rule in item_text:
                    self.rule_combo.setCurrentIndex(i)
                    break
        elif rule_names:
            self.rule_combo.setCurrentIndex(0)
            config_manager.set("code_rule", rule_names[0])
            # 更新规则编辑框
            self.rule_name_edit.setText(rule_names[0])
            self.rule_content_edit.setPlainText(rules.get(rule_names[0], {}).get("content", ""))
            self.python_mode_checkbox.setChecked(rules.get(rule_names[0], {}).get("python_mode", False))
        else:
            config_manager.set("code_rule", "")
            self.rule_name_edit.setText("")
            self.rule_content_edit.setPlainText("")
            self.python_mode_checkbox.setChecked(False)

    def _show_syntax_help(self):
        """显示语法帮助"""
        dialog = QWidget(self)
        dialog.setWindowTitle("语法说明")

        # 获取屏幕大小
        screen = self.screen()
        screen_rect = screen.geometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()

        # 设置对话框大小为1/3屏幕高，2/5屏幕宽
        dialog_width = int(screen_width * 2 / 5)
        dialog_height = int(screen_height * 1 / 3)
        dialog.resize(dialog_width, dialog_height)

        # 创建布局
        layout = QVBoxLayout(dialog)

        # 创建文本编辑框显示帮助信息
        text_edit = QTextEdit()
        text_edit.setPlainText(SYNTAX_HELP_TEXT)
        text_edit.setReadOnly(True)
        text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        layout.addWidget(text_edit)

        # 创建确定按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(dialog.close)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        dialog.show()

    def reload(self):
        """重新加载设置值"""
        self._load_current_values()

    def _on_theme_changed(self, _mode, _name, _color):
        """主题变更时更新样式"""
        # 重新设置 UI 以更新颜色
        self._setup_ui()
