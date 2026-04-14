from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QFormLayout, QLabel, QComboBox, QHBoxLayout, QPushButton, QLineEdit, QTextEdit, QWidget) 
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from app.core.config_manager import config_manager

def load_code_rules(settings_content_layout, section_widgets, parent):
    """加载编码规则设置"""
    section_widget = QGroupBox("编码规则")
    section_layout = QVBoxLayout()
    
    # 编码规则设置
    rule_layout = QFormLayout()
    
    rule_label = QLabel("编码规则:")
    rule_combo = QComboBox()
    
    # 加载自定义规则列表
    rules = config_manager.get("custom_rules", {})
    # 检查规则格式是否为新格式（包含content和python_mode字段）
    # 如果是旧格式，转换为新格式
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
    
    # 自定义编码规则设置
    custom_rule_group = QGroupBox("自定义编码规则")
    custom_rule_layout = QVBoxLayout()
    
    # 规则名称
    rule_name_layout = QHBoxLayout()
    rule_name_label = QLabel("规则名称:")
    rule_name_edit = QLineEdit()
    rule_name_layout.addWidget(rule_name_label)
    rule_name_layout.addWidget(rule_name_edit)
    custom_rule_layout.addLayout(rule_name_layout)
    
    # Python模式勾选框
    python_mode_layout = QHBoxLayout()
    python_mode_checkbox = QPushButton("开启Python模式")
    python_mode_checkbox.setCheckable(True)
    python_mode_layout.addWidget(python_mode_checkbox)
    custom_rule_layout.addLayout(python_mode_layout)
    
    # 规则内容
    rule_content_layout = QVBoxLayout()
    rule_content_label = QLabel("规则内容:")
    rule_content_edit = QTextEdit()
    # 设置 tab 缩进相关属性
    rule_content_edit.setTabStopDistance(20)  # 设置 tab 键宽度为 20 像素
    # 计算屏幕高度，动态设置 QTextEdit 的最小高度为屏幕高度的 1/2
    from PyQt6.QtWidgets import QApplication
    screen = QApplication.primaryScreen()
    screen_height = screen.size().height()
    min_height = int(screen_height * 0.5)  # 屏幕高度的 1/2
    rule_content_edit.setMinimumHeight(min_height)
    # 设置 QTextEdit 的最小宽度，确保有足够的空间编写规则
    rule_content_edit.setMinimumWidth(400)
    # 设置 QTextEdit 的字体，确保代码显示清晰
    rule_content_edit.setFont(QFont("Monospace", 10))
    # 确保 QTextEdit 能够滚动
    rule_content_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
    rule_content_layout.addWidget(rule_content_label)
    rule_content_layout.addWidget(rule_content_edit)
    custom_rule_layout.addLayout(rule_content_layout)
    
    # 为默认规则和Python模式添加标识
    default_rule = config_manager.get("default_code_rule", "")
    for name in rule_names:
        display_name = name
        if rules[name].get("python_mode", False):
            display_name += " *python"
        if name == default_rule:
            display_name += " [默认]"
        rule_combo.addItem(display_name)
    
    current_rule = config_manager.get("code_rule", rule_names[0] if rule_names else "")
    if current_rule in rule_names:
        # 检查是否为默认规则和Python模式
        display_name = current_rule
        if rules[current_rule].get("python_mode", False):
            display_name += " *python"
        if current_rule == default_rule:
            display_name += " [默认]"
        rule_combo.setCurrentText(display_name)
        # 初始化显示当前规则内容和Python模式状态
        rule_name_edit.setText(current_rule)
        rule_content_edit.setPlainText(rules.get(current_rule, {}).get("content", ""))
        python_mode_checkbox.setChecked(rules.get(current_rule, {}).get("python_mode", False))
    
    # 连接信号，自动保存
    def on_rule_changed(text):
        # 移除默认标识和Python模式标识
        if " [默认]" in text:
            rule_name = text.replace(" [默认]", "")
        else:
            rule_name = text
        if " *python" in rule_name:
            rule_name = rule_name.replace(" *python", "")
        config_manager.set("code_rule", rule_name)
        # 切换规则时，自动填充规则名称、内容和Python模式状态
        rule_name_edit.setText(rule_name)
        rule_content_edit.setPlainText(rules.get(rule_name, {}).get("content", ""))
        python_mode_checkbox.setChecked(rules.get(rule_name, {}).get("python_mode", False))
    
    rule_combo.currentTextChanged.connect(on_rule_changed)
    rule_layout.addRow(rule_label, rule_combo)
    
    # 语法说明
    syntax_layout = QHBoxLayout()
    syntax_label = QLabel("语法说明:")
    syntax_button = QPushButton("?")
    syntax_button.setFixedSize(20, 20)
    syntax_button.setStyleSheet("QPushButton { border-radius: 10px; background-color: #4CAF50; color: white; }")
    
    def show_syntax_help():
        help_text = """编码规则语法说明：

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
        # 创建自定义对话框
        dialog = QWidget(parent)
        dialog.setWindowTitle("语法说明")
        
        # 获取屏幕大小
        screen = parent.screen()
        screen_rect = screen.geometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()
        
        # 设置对话框大小为1/3屏幕高，2/5屏幕宽
        dialog_width = int(screen_width * 2/5)
        dialog_height = int(screen_height * 1/3)
        dialog.resize(dialog_width, dialog_height)
        
        # 设置对话框为可调整大小
        # dialog.setSizeGripEnabled(True)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 创建文本编辑框显示帮助信息
        text_edit = QTextEdit()
        text_edit.setPlainText(help_text)
        text_edit.setReadOnly(True)
        text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        
        # 添加滚动条
        text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 添加文本编辑框到布局
        layout.addWidget(text_edit)
        
        # 创建确定按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(dialog.close)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        
        # 添加按钮到布局
        layout.addLayout(button_layout)
        
        # 显示对话框
        dialog.show()
    
    syntax_button.clicked.connect(show_syntax_help)
    syntax_layout.addWidget(syntax_label)
    syntax_layout.addWidget(syntax_button)
    custom_rule_layout.addLayout(syntax_layout)
    
    # 添加、删除和设为默认按钮
    button_layout = QHBoxLayout()
    add_button = QPushButton("添加规则")
    delete_button = QPushButton("删除规则")
    set_default_button = QPushButton("设为默认")
    
    def add_rule():
        rule_name = rule_name_edit.text().strip()
        rule_content = rule_content_edit.toPlainText().strip()
        python_mode = python_mode_checkbox.isChecked()
        
        if rule_name and rule_content:
            nonlocal rules
            rules = config_manager.get("custom_rules", {})
            # 保存规则内容和Python模式状态
            rules[rule_name] = {
                "content": rule_content,
                "python_mode": python_mode
            }
            config_manager.set("custom_rules", rules)
            # 更新下拉框
            rule_combo.clear()
            rule_names = list(rules.keys())
            # 为默认规则和Python模式添加标识
            default_rule = config_manager.get("default_code_rule", "")
            for name in rule_names:
                display_name = name
                if rules[name].get("python_mode", False):
                    display_name += " *python"
                if name == default_rule:
                    display_name += " [默认]"
                rule_combo.addItem(display_name)
            # 设置当前规则的显示名称
            current_display_name = rule_name
            if python_mode:
                current_display_name += " *python"
            rule_combo.setCurrentText(current_display_name)
            if hasattr(parent, 'show_toast'):
                parent.show_toast(f"规则 '{rule_name}' 添加成功")
        else:
            if hasattr(parent, 'show_toast'):
                parent.show_toast("请输入规则名称和内容")
    
    def delete_rule():
        current_rule = rule_combo.currentText()
        # 移除默认标识和Python模式标识
        if " [默认]" in current_rule:
            current_rule = current_rule.replace(" [默认]", "")
        if " *python" in current_rule:
            current_rule = current_rule.replace(" *python", "")
        
        if current_rule:
            nonlocal rules
            rules = config_manager.get("custom_rules", {})
            if current_rule in rules:
                # 如果删除的是默认规则，清除默认规则设置
                if current_rule == config_manager.get("default_code_rule", ""):
                    config_manager.set("default_code_rule", "")
                
                del rules[current_rule]
                config_manager.set("custom_rules", rules)
                # 更新下拉框
                rule_combo.clear()
                rule_names = list(rules.keys())
                # 为默认规则和Python模式添加标识
                default_rule = config_manager.get("default_code_rule", "")
                for name in rule_names:
                    display_name = name
                    if rules[name].get("python_mode", False):
                        display_name += " *python"
                    if name == default_rule:
                        display_name += " [默认]"
                    rule_combo.addItem(display_name)
                if rule_names:
                    rule_combo.setCurrentIndex(0)
                    config_manager.set("code_rule", rule_names[0])
                    # 更新规则编辑框
                    rule_name_edit.setText(rule_names[0])
                    rule_content_edit.setPlainText(rules.get(rule_names[0], {}).get("content", ""))
                    # 更新Python模式勾选框
                    python_mode_checkbox.setChecked(rules.get(rule_names[0], {}).get("python_mode", False))
                else:
                    config_manager.set("code_rule", "")
                    # 清空规则编辑框
                    rule_name_edit.setText("")
                    rule_content_edit.setPlainText("")
                    python_mode_checkbox.setChecked(False)
                if hasattr(parent, 'show_toast'):
                    parent.show_toast(f"规则 '{current_rule}' 删除成功")
    
    def set_default():
        current_rule = rule_combo.currentText()
        # 移除默认标识和Python模式标识
        if " [默认]" in current_rule:
            current_rule = current_rule.replace(" [默认]", "")
        if " *python" in current_rule:
            current_rule = current_rule.replace(" *python", "")
        
        if current_rule:
            # 设置默认规则
            config_manager.set("default_code_rule", current_rule)
            # 更新下拉框，为默认规则和Python模式添加标识
            nonlocal rules
            rules = config_manager.get("custom_rules", {})
            rule_names = list(rules.keys())
            rule_combo.clear()
            for name in rule_names:
                display_name = name
                if rules[name].get("python_mode", False):
                    display_name += " *python"
                if name == current_rule:
                    display_name += " [默认]"
                rule_combo.addItem(display_name)
            # 设置当前规则的显示名称
            current_display_name = current_rule
            if rules.get(current_rule, {}).get("python_mode", False):
                current_display_name += " *python"
            current_display_name += " [默认]"
            rule_combo.setCurrentText(current_display_name)
            if hasattr(parent, 'show_toast'):
                parent.show_toast(f"规则 '{current_rule}' 已设为默认")
    
    add_button.clicked.connect(add_rule)
    delete_button.clicked.connect(delete_rule)
    set_default_button.clicked.connect(set_default)
    
    button_layout.addWidget(add_button)
    button_layout.addWidget(delete_button)
    button_layout.addWidget(set_default_button)
    custom_rule_layout.addLayout(button_layout)
    
    section_layout.addLayout(rule_layout)
    section_layout.addWidget(custom_rule_group)
    section_widget.setLayout(section_layout)
    
    settings_content_layout.addWidget(section_widget)
    section_widgets["编码规则"] = section_widget
