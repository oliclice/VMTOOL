from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
                             QComboBox, QPushButton, QLineEdit, QTextEdit, 
                             QCheckBox, QMessageBox, QGroupBox, QSplitter, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from app.core.config_manager import config_manager

class CodeRulesTab(QWidget):
    """编码规则标签页"""
    def __init__(self, parent=None, dict_service=None):
        super().__init__(parent)
        self.dict_service = dict_service
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 顶部：规则选择区域
        top_layout = QHBoxLayout()
        rule_label = QLabel("选择编码规则:")
        rule_label.setToolTip("选择要编辑的编码规则")
        self.rule_combo = QComboBox()
        self.rule_combo.setMinimumWidth(200)
        top_layout.addWidget(rule_label)
        top_layout.addWidget(self.rule_combo)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # 中部：规则编辑和预览区域
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：规则编辑区域
        edit_widget = QWidget()
        edit_layout = QVBoxLayout(edit_widget)
        
        # 自定义编码规则设置
        custom_rule_group = QGroupBox("规则编辑")
        custom_rule_layout = QVBoxLayout()
        
        # 规则名称
        rule_name_layout = QHBoxLayout()
        rule_name_label = QLabel("规则名称:")
        self.rule_name_edit = QLineEdit()
        self.rule_name_edit.setPlaceholderText("输入规则名称")
        rule_name_layout.addWidget(rule_name_label)
        rule_name_layout.addWidget(self.rule_name_edit)
        custom_rule_layout.addLayout(rule_name_layout)
        
        # Python模式勾选框
        python_mode_layout = QHBoxLayout()
        self.python_mode_checkbox = QCheckBox("开启Python模式")
        self.python_mode_checkbox.setToolTip("开启后可以使用Python代码生成编码")
        python_mode_layout.addWidget(self.python_mode_checkbox)
        custom_rule_layout.addLayout(python_mode_layout)
        
        # 规则内容
        rule_content_layout = QVBoxLayout()
        rule_content_layout.setSpacing(5)  # 减小间距，使文本框与标题更接近
        rule_content_label = QLabel("规则内容:")
        self.rule_content_edit = QTextEdit()
        # 设置 tab 缩进相关属性
        self.rule_content_edit.setTabStopDistance(20)  # 设置 tab 键宽度为 20 像素
        # 设置 QTextEdit 的高度，确保有足够的空间编写规则
        self.rule_content_edit.setMinimumHeight(300)
        # 设置 QTextEdit 的最小宽度，确保有足够的空间编写规则
        self.rule_content_edit.setMinimumWidth(400)
        # 设置 QTextEdit 的字体，确保代码显示清晰
        self.rule_content_edit.setFont(QFont("Monospace", 10))
        # 确保 QTextEdit 能够滚动
        self.rule_content_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # 确保文本框可以输入
        self.rule_content_edit.setReadOnly(False)
        rule_content_layout.addWidget(rule_content_label)
        rule_content_layout.addWidget(self.rule_content_edit)
        custom_rule_layout.addLayout(rule_content_layout)
        
        # 规则模板
        template_layout = QHBoxLayout()
        template_label = QLabel("规则模板:")
        self.template_combo = QComboBox()
        self.template_combo.addItems(["选择模板", "双拼规则", "全拼规则", "五笔规则", "自定义规则"])
        self.template_combo.setToolTip("选择预设规则模板")
        template_button = QPushButton("应用模板")
        template_button.setToolTip("将选择的模板应用到当前规则")
        template_button.clicked.connect(self.apply_template)
        template_layout.addWidget(template_label)
        template_layout.addWidget(self.template_combo)
        template_layout.addWidget(template_button)
        custom_rule_layout.addLayout(template_layout)
        
        # 语法说明
        syntax_layout = QHBoxLayout()
        syntax_label = QLabel("语法说明:")
        syntax_button = QPushButton("?")
        syntax_button.setFixedSize(20, 20)
        syntax_button.setStyleSheet("QPushButton { border-radius: 10px; background-color: #4CAF50; color: white; }")
        syntax_button.setToolTip("查看编码规则语法说明")
        syntax_button.clicked.connect(self.show_syntax_help)
        syntax_layout.addWidget(syntax_label)
        syntax_layout.addWidget(syntax_button)
        custom_rule_layout.addLayout(syntax_layout)
        
        custom_rule_group.setLayout(custom_rule_layout)
        edit_layout.addWidget(custom_rule_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        add_button = QPushButton("添加规则")
        add_button.setToolTip("添加新的编码规则")
        delete_button = QPushButton("删除规则")
        delete_button.setToolTip("删除当前编码规则")
        set_default_button = QPushButton("设为默认")
        set_default_button.setToolTip("将当前规则设为默认编码规则")
        
        add_button.clicked.connect(self.add_rule)
        delete_button.clicked.connect(self.delete_rule)
        set_default_button.clicked.connect(self.set_default)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(set_default_button)
        edit_layout.addLayout(button_layout)
        
        splitter.addWidget(edit_widget)
        
        # 右侧：实时预览区域
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        preview_group = QGroupBox("实时预览")
        preview_group_layout = QVBoxLayout()
        
        # 预览输入
        preview_input_layout = QHBoxLayout()
        preview_input_label = QLabel("输入测试词:")
        self.preview_input = QLineEdit()
        self.preview_input.setPlaceholderText("输入词语进行测试")
        preview_button = QPushButton("测试")
        preview_button.setToolTip("测试当前规则对输入词的编码效果")
        preview_button.clicked.connect(self.test_rule)
        preview_input_layout.addWidget(preview_input_label)
        preview_input_layout.addWidget(self.preview_input)
        preview_input_layout.addWidget(preview_button)
        preview_group_layout.addLayout(preview_input_layout)
        
        # 预览结果
        self.preview_result = QTextEdit()
        self.preview_result.setReadOnly(True)
        self.preview_result.setMinimumHeight(200)
        self.preview_result.setFont(QFont("Monospace", 10))
        preview_group_layout.addWidget(QLabel("编码结果:"))
        preview_group_layout.addWidget(self.preview_result)
        
        # 规则验证
        self.validation_result = QLabel()
        self.validation_result.setStyleSheet("color: green")
        preview_group_layout.addWidget(QLabel("规则验证:"))
        preview_group_layout.addWidget(self.validation_result)
        
        preview_group.setLayout(preview_group_layout)
        preview_layout.addWidget(preview_group)
        
        splitter.addWidget(preview_widget)
        
        # 设置分割器比例
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
        
        # 加载规则
        self.load_rules()
        
        # 连接信号
        self.rule_combo.currentTextChanged.connect(self.on_rule_changed)
        self.rule_content_edit.textChanged.connect(self.validate_rule)
    
    def load_rules(self):
        """加载编码规则"""
        # 加载自定义规则列表
        self.rules = config_manager.get("custom_rules", {})
        # 检查规则格式是否为新格式（包含content和python_mode字段）
        # 如果是旧格式，转换为新格式
        new_rules = {}
        for rule_name, rule_value in self.rules.items():
            if isinstance(rule_value, str):
                # 旧格式，转换为新格式
                new_rules[rule_name] = {
                    "content": rule_value,
                    "python_mode": False
                }
            else:
                # 新格式，直接使用
                new_rules[rule_name] = rule_value
        self.rules = new_rules
        config_manager.set("custom_rules", self.rules)
        self.rule_names = list(self.rules.keys())
        if not self.rule_names:
            # 默认规则
            self.rules = {
                "默认规则": {
                    "content": "v[2]=s[1][1]+s[1][2]+s[2][1]+s[2][2]\nv[3]=s[1][1]+s[2][1]+s[3][1]",
                    "python_mode": False
                }
            }
            config_manager.set("custom_rules", self.rules)
            self.rule_names = list(self.rules.keys())
        
        # 为默认规则和Python模式添加标识
        default_rule = config_manager.get("default_code_rule", "")
        self.rule_combo.clear()
        for name in self.rule_names:
            display_name = name
            if self.rules[name].get("python_mode", False):
                display_name += " *python"
            if name == default_rule:
                display_name += " [默认]"
            self.rule_combo.addItem(display_name)
        
        # 设置当前规则
        current_rule = config_manager.get("code_rule", self.rule_names[0] if self.rule_names else "")
        if current_rule in self.rule_names:
            # 检查是否为默认规则和Python模式
            display_name = current_rule
            if self.rules[current_rule].get("python_mode", False):
                display_name += " *python"
            if current_rule == default_rule:
                display_name += " [默认]"
            self.rule_combo.setCurrentText(display_name)
            # 初始化显示当前规则内容和Python模式状态
            self.rule_name_edit.setText(current_rule)
            self.rule_content_edit.setPlainText(self.rules.get(current_rule, {}).get("content", ""))
            self.python_mode_checkbox.setChecked(self.rules.get(current_rule, {}).get("python_mode", False))
        
        # 验证规则
        self.validate_rule()
    
    def on_rule_changed(self, text):
        """当规则选择变化时"""
        # 移除默认标识和Python模式标识
        if " [默认]" in text:
            rule_name = text.replace(" [默认]", "")
        else:
            rule_name = text
        if " *python" in rule_name:
            rule_name = rule_name.replace(" *python", "")
        config_manager.set("code_rule", rule_name)
        # 切换规则时，自动填充规则名称、内容和Python模式状态
        self.rule_name_edit.setText(rule_name)
        self.rule_content_edit.setPlainText(self.rules.get(rule_name, {}).get("content", ""))
        self.python_mode_checkbox.setChecked(self.rules.get(rule_name, {}).get("python_mode", False))
        # 验证规则
        self.validate_rule()
    
    def add_rule(self):
        """添加新规则"""
        rule_name = self.rule_name_edit.text().strip()
        rule_content = self.rule_content_edit.toPlainText().strip()
        python_mode = self.python_mode_checkbox.isChecked()
        
        if rule_name and rule_content:
            # 保存规则内容和Python模式状态
            self.rules[rule_name] = {
                "content": rule_content,
                "python_mode": python_mode
            }
            config_manager.set("custom_rules", self.rules)
            # 更新下拉框
            self.load_rules()
            # 设置当前规则的显示名称
            current_display_name = rule_name
            if python_mode:
                current_display_name += " *python"
            self.rule_combo.setCurrentText(current_display_name)
            if hasattr(self.parent(), 'show_toast'):
                self.parent().show_toast(f"规则 '{rule_name}' 添加成功")
        else:
            if hasattr(self.parent(), 'show_toast'):
                self.parent().show_toast("请输入规则名称和内容")
    
    def delete_rule(self):
        """删除当前规则"""
        current_rule = self.rule_combo.currentText()
        # 移除默认标识和Python模式标识
        if " [默认]" in current_rule:
            current_rule = current_rule.replace(" [默认]", "")
        if " *python" in current_rule:
            current_rule = current_rule.replace(" *python", "")
        
        if current_rule:
            if current_rule in self.rules:
                # 如果删除的是默认规则，清除默认规则设置
                if current_rule == config_manager.get("default_code_rule", ""):
                    config_manager.set("default_code_rule", "")
                
                del self.rules[current_rule]
                config_manager.set("custom_rules", self.rules)
                # 更新下拉框
                self.load_rules()
                if hasattr(self.parent(), 'show_toast'):
                    self.parent().show_toast(f"规则 '{current_rule}' 删除成功")
    
    def set_default(self):
        """设置默认规则"""
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
            self.load_rules()
            # 设置当前规则的显示名称
            current_display_name = current_rule
            if self.rules.get(current_rule, {}).get("python_mode", False):
                current_display_name += " *python"
            current_display_name += " [默认]"
            self.rule_combo.setCurrentText(current_display_name)
            if hasattr(self.parent(), 'show_toast'):
                self.parent().show_toast(f"规则 '{current_rule}' 已设为默认")
    
    def show_syntax_help(self):
        """显示语法说明"""
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
"""
        dialog = QMessageBox()
        dialog.setWindowTitle("语法说明")
        dialog.setText(help_text)
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.exec()
    
    def apply_template(self):
        """应用规则模板"""
        template = self.template_combo.currentText()
        if template == "双拼规则":
            self.rule_content_edit.setPlainText("v[2] = s[1][1] + s[1][2] + s[2][1] + s[2][2]\nv[3] = s[1][1] + s[2][1] + s[3][1]\nv[4+] = s[1][1] + s[2][1] + s[3][1] + s[4][1]")
        elif template == "全拼规则":
            self.rule_content_edit.setPlainText("v[2] = s[1][1] + s[1][2] + s[2][1] + s[2][2]\nv[3] = s[1][1] + s[2][1] + s[3][1]\nv[4+] = s[1][1] + s[2][1] + s[3][1] + s[4][1]")
        elif template == "五笔规则":
            self.rule_content_edit.setPlainText("v[2] = s[1][1] + s[1][2] + s[2][1] + s[2][2]\nv[3] = s[1][1] + s[2][1] + s[3][1]\nv[4+] = s[1][1] + s[2][1] + s[3][1] + s[4][1]")
        elif template == "自定义规则":
            self.rule_content_edit.setPlainText("# 自定义编码规则\nv[2] = s[1][1] + s[1][2] + s[2][1] + s[2][2]\nv[3] = s[1][1] + s[2][1] + s[3][1]\nv[4+] = s[1][1] + s[2][1] + s[3][1] + s[4][1]")
        # 验证规则
        self.validate_rule()
    
    def validate_rule(self):
        """验证规则语法"""
        rule_content = self.rule_content_edit.toPlainText().strip()
        python_mode = self.python_mode_checkbox.isChecked()
        
        if not rule_content:
            self.validation_result.setText("规则内容为空")
            self.validation_result.setStyleSheet("color: orange")
            return
        
        if python_mode:
            # Python模式，简单检查语法
            try:
                compile(rule_content, '<string>', 'exec')
                self.validation_result.setText("Python语法正确")
                self.validation_result.setStyleSheet("color: green")
            except SyntaxError as e:
                self.validation_result.setText(f"Python语法错误: {e}")
                self.validation_result.setStyleSheet("color: red")
        else:
            # 普通模式，检查语法
            lines = rule_content.split('\n')
            valid = True
            error_message = ""
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    valid = False
                    error_message = f"规则格式错误: {line}"
                    break
                parts = line.split('=')
                if len(parts) != 2:
                    valid = False
                    error_message = f"规则格式错误: {line}"
                    break
                left_part = parts[0].strip()
                if not left_part.startswith('v['):
                    valid = False
                    error_message = f"规则格式错误: {line}"
                    break
            
            if valid:
                self.validation_result.setText("规则语法正确")
                self.validation_result.setStyleSheet("color: green")
            else:
                self.validation_result.setText(error_message)
                self.validation_result.setStyleSheet("color: red")
    
    def test_rule(self):
        """测试规则"""
        test_word = self.preview_input.text().strip()
        if not test_word:
            self.preview_result.setText("请输入测试词")
            return
        
        # 简单模拟规则应用
        result = f"测试词: {test_word}\n"
        result += f"词长度: {len(test_word)}\n"
        result += "编码结果: 模拟编码"
        
        self.preview_result.setText(result)
