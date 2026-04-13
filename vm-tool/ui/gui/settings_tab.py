from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
                             QComboBox, QPushButton, QTreeWidget, QTreeWidgetItem, 
                             QSplitter, QScrollArea, QGroupBox, QLineEdit, QTextEdit, 
                             QCheckBox, QFontDialog, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase
import os
from app.core.config_manager import config_manager
from app.core.theme_constants import (
    THEME_MODE_AUTO, THEME_MODE_LIGHT, THEME_MODE_DARK,
    THEME_NAME_CLASSIC, THEME_NAME_MATERIAL3, THEME_COLOR_BLUE, THEME_COLOR_GREEN,
    THEME_COLOR_RED, THEME_COLOR_PURPLE, THEME_COLOR_ORANGE,
    MODE_DISPLAY_MAP, MODE_DISPLAY_REVERSE_MAP
)
from app.services.dict import DictService

class SettingsTab(QWidget):
    """设置标签页"""
    def __init__(self, parent=None, dict_service=None):
        super().__init__(parent)
        self.dict_service = dict_service
        self.section_widgets = {}
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QHBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Horizontal)
        
        # 左侧设置类型列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        settings_types = QTreeWidget()
        settings_types.setHeaderLabel("设置类型")
        # 允许拖动排序
        settings_types.setDragEnabled(True)
        settings_types.setDropIndicatorShown(True)
        settings_types.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        
        # 从配置中加载设置类型顺序，如果没有则使用默认顺序
        default_sections = ["主题设置", "字体设置", "语言设置", 
                          "配置目录", "数据库路径", "缓存设置", "统计设置", "删除表", "文件配置"]
        sections = config_manager.get("settings_order", default_sections)
        
        # 添加设置类型
        for section in sections:
            QTreeWidgetItem(settings_types, [section])
        
        # 连接拖动结束信号
        settings_types.model().rowsInserted.connect(self.on_settings_order_changed)
        
        left_layout.addWidget(settings_types)
        splitter.addWidget(left_widget)
        
        # 右侧设置内容
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 设置标题
        self.settings_title = QLabel("设置")
        self.settings_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        right_layout.addWidget(self.settings_title)
        
        # 设置内容区域 - 使用滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.settings_content = QWidget()
        self.settings_content_layout = QVBoxLayout(self.settings_content)
        # 调整布局间距
        self.settings_content_layout.setSpacing(10)
        self.settings_content_layout.setContentsMargins(10, 10, 10, 10)
        
        # 加载所有设置项
        self.load_all_settings()
        
        scroll_area.setWidget(self.settings_content)
        right_layout.addWidget(scroll_area)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器大小
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter)
        
        # 连接信号
        settings_types.itemClicked.connect(self.on_settings_type_clicked)
    
    def load_all_settings(self):
        """加载所有设置项"""
        # 主题设置
        self.load_theme_settings()
        
        # 语言设置（包含字体设置）
        self.load_language_settings()
        
        # 配置目录
        self.load_config_dir_settings()
        
        # 数据库路径
        self.load_database_path_settings()
        
        # 缓存设置
        self.load_cache_settings()
        
        # 删除表
        self.load_delete_table_settings()
        
        # 文件配置
        self.load_file_config_settings()
        
        # 统计设置
        self.load_stats_settings()
    
    def load_theme_settings(self):
        """加载主题设置"""
        section_widget = QGroupBox("主题设置")
        section_layout = QVBoxLayout()
        
        # 主题设置
        theme_layout = QFormLayout()
        
        theme_label = QLabel("主题:")
        theme_combo = QComboBox()
        theme_combo.addItems([THEME_NAME_CLASSIC, THEME_NAME_MATERIAL3])

        # 模式设置
        mode_label = QLabel("模式:")
        mode_combo = QComboBox()
        # 按顺序添加模式显示名称
        mode_display_names = [
            MODE_DISPLAY_MAP[THEME_MODE_AUTO],
            MODE_DISPLAY_MAP[THEME_MODE_LIGHT],
            MODE_DISPLAY_MAP[THEME_MODE_DARK]
        ]
        mode_combo.addItems(mode_display_names)

        # 主题颜色设置（仅对Material3有效）
        color_label = QLabel("主题颜色:")
        color_combo = QComboBox()
        color_combo.addItems([
            THEME_COLOR_BLUE, THEME_COLOR_GREEN, THEME_COLOR_RED,
            THEME_COLOR_PURPLE, THEME_COLOR_ORANGE
        ])
        
        # 加载当前设置
        current_theme = config_manager.get("theme_name", THEME_NAME_CLASSIC)
        current_mode = config_manager.get("theme_mode", THEME_MODE_AUTO)
        current_color = config_manager.get("theme_color", THEME_COLOR_BLUE)
        
        theme_combo.setCurrentText(current_theme)
        
        # 映射内部模式值到显示名称（使用常量映射）
        display_mode = MODE_DISPLAY_MAP.get(current_mode, MODE_DISPLAY_MAP[THEME_MODE_AUTO])
        mode_combo.setCurrentText(display_mode)
        
        color_combo.setCurrentText(current_color)
        
        # 连接信号
        def on_theme_changed():
            theme = theme_combo.currentText()
            mode = mode_combo.currentText()
            color = color_combo.currentText()
            
            # 映射模式显示名称到内部值（使用常量映射）
            internal_mode = MODE_DISPLAY_REVERSE_MAP.get(mode, THEME_MODE_AUTO)
            
            # 保存设置
            config_manager.set("theme_name", theme)
            config_manager.set("theme_mode", internal_mode)
            config_manager.set("theme_color", color)
            
            # 使用主题管理器应用主题
            from .theme_manager import theme_manager
            theme_manager.set_theme(internal_mode, theme, color)
            
            # 显示提示
            if hasattr(self.parent(), 'show_toast'):
                self.parent().show_toast(f"主题已更改为：{theme} - {mode} - {color}")
        
        theme_combo.currentTextChanged.connect(on_theme_changed)
        mode_combo.currentTextChanged.connect(on_theme_changed)
        color_combo.currentTextChanged.connect(on_theme_changed)
        
        theme_layout.addRow(theme_label, theme_combo)
        theme_layout.addRow(mode_label, mode_combo)
        theme_layout.addRow(color_label, color_combo)
        
        section_layout.addLayout(theme_layout)
        section_widget.setLayout(section_layout)
        
        self.settings_content_layout.addWidget(section_widget)
        self.section_widgets["主题设置"] = section_widget
    

    
    def load_language_settings(self):
        """加载语言设置"""
        section_widget = QGroupBox("语言设置")
        section_layout = QVBoxLayout()
        
        # 语言设置
        language_layout = QFormLayout()
        
        language_label = QLabel("语言:")
        language_combo = QComboBox()
        language_combo.addItems(["中文", "English"])
        language_combo.setCurrentText(config_manager.get("language", "中文"))
        
        # 连接信号，自动保存
        language_combo.currentTextChanged.connect(lambda text: config_manager.set("language", text))
        
        language_layout.addRow(language_label, language_combo)
        
        # 字体设置
        font_label = QLabel("字体:")
        font_combo = QComboBox()
        
        # 获取系统字体列表
        from PyQt6.QtGui import QFontDatabase
        font_families = QFontDatabase.families()
        font_combo.addItems(font_families)
        
        # 加载当前字体设置
        current_font = config_manager.get("font_family", "")
        if current_font and current_font in font_families:
            font_combo.setCurrentText(current_font)
        
        # 连接信号，自动保存并应用
        def on_font_changed(font_family):
            config_manager.set("font_family", font_family)
            # 应用字体到整个应用
            from PyQt6.QtGui import QFont
            from PyQt6.QtWidgets import QApplication
            font = QFont(font_family)
            QApplication.instance().setFont(font)
            if hasattr(self.parent(), 'show_toast'):
                self.parent().show_toast(f"字体已更改为: {font_family}")
        
        font_combo.currentTextChanged.connect(on_font_changed)
        
        language_layout.addRow(font_label, font_combo)
        
        section_layout.addLayout(language_layout)
        section_widget.setLayout(section_layout)
        
        self.settings_content_layout.addWidget(section_widget)
        self.section_widgets["语言设置"] = section_widget
    
    def load_code_rules(self):
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
        python_mode_checkbox = QCheckBox("开启Python模式")
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
            dialog = QWidget(self)
            dialog.setWindowTitle("语法说明")
            
            # 获取屏幕大小
            screen = self.screen()
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
                if hasattr(self.parent(), 'show_toast'):
                    self.parent().show_toast(f"规则 '{rule_name}' 添加成功")
            else:
                if hasattr(self.parent(), 'show_toast'):
                    self.parent().show_toast("请输入规则名称和内容")
        
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
                    if hasattr(self.parent(), 'show_toast'):
                        self.parent().show_toast(f"规则 '{current_rule}' 删除成功")
        
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
                if hasattr(self.parent(), 'show_toast'):
                    self.parent().show_toast(f"规则 '{current_rule}' 已设为默认")
        
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
        
        self.settings_content_layout.addWidget(section_widget)
        self.section_widgets["编码规则"] = section_widget
    

    
    def load_config_dir_settings(self):
        """加载配置目录设置"""
        section_widget = QGroupBox("配置目录")
        section_layout = QVBoxLayout()
        
        # 配置目录设置
        config_dir_layout = QFormLayout()
        
        dir_label = QLabel("配置目录:")
        dir_edit = QLineEdit()
        dir_edit.setText(config_manager.get("config_dir", "~/.config/vm-tool"))
        # 连接信号，自动保存
        dir_edit.textChanged.connect(lambda text: config_manager.set("config_dir", text))
        
        # 连接浏览按钮点击事件
        def browse_config_dir():
            # 尝试使用 zenity 打开目录选择对话框
            try:
                import subprocess
                
                # 使用 zenity 打开目录选择对话框
                result = subprocess.run(
                    ["zenity", "--file-selection", "--directory", "--title=选择配置目录", "--filename=~/.config/"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # 如果 zenity 成功执行（无论是否选择了目录），都不再使用Qt内置对话框
                if result.returncode == 0:
                    directory = result.stdout.strip()
                    if directory:
                        dir_edit.setText(directory)
                        config_manager.set("config_dir", directory)
                    return
            except Exception:
                pass
            
            # 如果 zenity 失败，使用Qt内置对话框
            from PyQt6.QtWidgets import QFileDialog
            directory = QFileDialog.getExistingDirectory(
                self, "选择配置目录", "~/.config"
            )
            if directory:
                dir_edit.setText(directory)
                config_manager.set("config_dir", directory)
        
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(browse_config_dir)
        
        browse_layout = QHBoxLayout()
        browse_layout.addWidget(dir_edit)
        browse_layout.addWidget(browse_button)
        
        config_dir_layout.addRow(dir_label, browse_layout)
        section_layout.addLayout(config_dir_layout)
        section_widget.setLayout(section_layout)
        
        self.settings_content_layout.addWidget(section_widget)
        self.section_widgets["配置目录"] = section_widget
    
    def load_database_path_settings(self):
        """加载数据库路径设置"""
        section_widget = QGroupBox("数据库路径")
        section_layout = QVBoxLayout()
        
        # 数据库路径设置
        database_path_layout = QFormLayout()
        
        path_label = QLabel("数据库路径:")
        path_edit = QLineEdit()
        
        # 计算默认数据库路径
        config_dir = config_manager.get("config_dir", "~/.config/vm-tool")
        # 展开波浪号
        config_dir = os.path.expanduser(config_dir)
        default_db_path = os.path.join(config_dir, "vm_tool.db")
        
        path_edit.setText(config_manager.get("database_path", default_db_path))
        # 连接信号，自动保存
        path_edit.textChanged.connect(lambda text: config_manager.set("database_path", text))
        
        # 连接浏览按钮点击事件
        def browse_database_path():
            # 尝试使用 zenity 打开保存文件对话框
            try:
                import subprocess
                
                # 使用 zenity 打开保存文件对话框
                result = subprocess.run(
                    ["zenity", "--file-selection", "--save", "--title=选择数据库文件", "--file-filter=SQLite数据库文件 (*.db)|*.db"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # 如果 zenity 成功执行（无论是否选择了文件），都不再使用Qt内置对话框
                if result.returncode == 0:
                    file_path = result.stdout.strip()
                    if file_path:
                        path_edit.setText(file_path)
                        config_manager.set("database_path", file_path)
                    return
            except Exception:
                pass
            
            # 如果 zenity 失败，使用Qt内置对话框
            from PyQt6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "选择数据库文件", "", "SQLite数据库文件 (*.db)"
            )
            if file_path:
                path_edit.setText(file_path)
                config_manager.set("database_path", file_path)
        
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(browse_database_path)
        
        browse_layout = QHBoxLayout()
        browse_layout.addWidget(path_edit)
        browse_layout.addWidget(browse_button)
        
        database_path_layout.addRow(path_label, browse_layout)
        section_layout.addLayout(database_path_layout)
        section_widget.setLayout(section_layout)
        
        self.settings_content_layout.addWidget(section_widget)
        self.section_widgets["数据库路径"] = section_widget
    
    def load_cache_settings(self):
        """加载缓存设置"""
        section_widget = QGroupBox("缓存设置")
        section_layout = QVBoxLayout()
        
        # 缓存设置
        cache_layout = QFormLayout()
        
        # 启用缓存
        cache_enabled_label = QLabel("启用缓存:")
        cache_enabled_checkbox = QCheckBox()
        cache_enabled_checkbox.setChecked(config_manager.get("cache_enabled", True))
        # 连接信号，自动保存
        cache_enabled_checkbox.stateChanged.connect(lambda state: config_manager.set("cache_enabled", state == 2))
        
        # 缓存大小
        cache_size_label = QLabel("缓存大小 (MB):")
        cache_size_combo = QComboBox()
        cache_size_combo.addItems(["10", "50", "100", "200", "500"])
        cache_size_combo.setCurrentText(str(config_manager.get("cache_size", 100)))
        # 连接信号，自动保存
        cache_size_combo.currentTextChanged.connect(lambda text: config_manager.set("cache_size", int(text)))
        
        # 缓存过期时间
        cache_expiry_label = QLabel("缓存过期时间:")
        cache_expiry_combo = QComboBox()
        cache_expiry_combo.addItems(["1h", "6h", "12h", "24h", "48h", "7d", "30d"])
        
        # 转换当前值为对应选项
        current_expiry = config_manager.get("cache_expiry", 24)
        if current_expiry == 168:  # 7天
            current_option = "7d"
        elif current_expiry == 720:  # 30天
            current_option = "30d"
        else:
            current_option = f"{current_expiry}h"
        
        # 找到对应的选项，如果不存在则使用默认值
        if current_option not in ["1h", "6h", "12h", "24h", "48h", "7d", "30d"]:
            current_option = "24h"
        
        cache_expiry_combo.setCurrentText(current_option)
        
        # 连接信号，自动保存
        def on_cache_expiry_changed(text):
            if text.endswith("d"):
                # 天数转换为小时
                hours = int(text[:-1]) * 24
            else:
                # 直接使用小时
                hours = int(text[:-1])
            config_manager.set("cache_expiry", hours)
        
        cache_expiry_combo.currentTextChanged.connect(on_cache_expiry_changed)
        
        cache_layout.addRow(cache_enabled_label, cache_enabled_checkbox)
        cache_layout.addRow(cache_size_label, cache_size_combo)
        cache_layout.addRow(cache_expiry_label, cache_expiry_combo)
        
        section_layout.addLayout(cache_layout)
        section_widget.setLayout(section_layout)
        
        self.settings_content_layout.addWidget(section_widget)
        self.section_widgets["缓存设置"] = section_widget
    
    def load_delete_table_settings(self):
        """加载删除表设置"""
        section_widget = QGroupBox("删除表")
        section_layout = QVBoxLayout()
        
        # 删除表设置
        delete_table_layout = QVBoxLayout()
        
        # 删除字表按钮
        delete_chars_button = QPushButton("删除字表")
        delete_chars_button.clicked.connect(self.delete_chars_table)
        
        # 删除词表按钮
        delete_words_button = QPushButton("删除词表")
        delete_words_button.clicked.connect(self.delete_words_table)
        
        # 删除特殊字符表按钮
        delete_special_button = QPushButton("删除特殊字符表")
        delete_special_button.clicked.connect(self.delete_special_table)
        
        delete_table_layout.addWidget(delete_chars_button)
        delete_table_layout.addWidget(delete_words_button)
        delete_table_layout.addWidget(delete_special_button)
        
        section_layout.addLayout(delete_table_layout)
        section_widget.setLayout(section_layout)
        
        self.settings_content_layout.addWidget(section_widget)
        self.section_widgets["删除表"] = section_widget
    
    def load_file_config_settings(self):
        """加载文件配置设置"""
        section_widget = QGroupBox("文件配置")
        section_layout = QVBoxLayout()
        
        # 导出路径设置
        export_path_layout = QFormLayout()
        
        export_path_label = QLabel("默认导出路径:")
        export_path_edit = QLineEdit()
        export_path_edit.setText(config_manager.get("default_export_path", "./"))
        
        # 连接信号，自动保存
        def on_export_path_changed(text):
            config_manager.set("default_export_path", text)
            # 更新导入导出标签页中的路径
            if hasattr(self.parent(), 'export_path_edit'):
                self.parent().export_path_edit.setText(text)
                # 更新导出界面中的完整路径
                if hasattr(self.parent(), 'update_export_full_path'):
                    self.parent().update_export_full_path()
        
        export_path_edit.textChanged.connect(on_export_path_changed)
        
        # 连接浏览按钮点击事件
        def browse_export_path():
            # 尝试使用 zenity 打开目录选择对话框
            try:
                import subprocess
                
                # 使用 zenity 打开目录选择对话框
                result = subprocess.run(
                    ["zenity", "--file-selection", "--directory", "--title=选择导出目录", "--filename=./"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # 如果 zenity 成功执行（无论是否选择了目录），都不再使用Qt内置对话框
                if result.returncode == 0:
                    directory = result.stdout.strip()
                    if directory:
                        export_path_edit.setText(directory)
                        config_manager.set("default_export_path", directory)
                    return
            except Exception:
                pass
            
            # 如果 zenity 失败，使用Qt内置对话框
            from PyQt6.QtWidgets import QFileDialog
            directory = QFileDialog.getExistingDirectory(
                self, "选择导出目录", "./"
            )
            if directory:
                export_path_edit.setText(directory)
                config_manager.set("default_export_path", directory)
        
        export_browse_button = QPushButton("浏览")
        export_browse_button.clicked.connect(browse_export_path)
        
        export_browse_layout = QHBoxLayout()
        export_browse_layout.addWidget(export_path_edit)
        export_browse_layout.addWidget(export_browse_button)
        
        export_path_layout.addRow(export_path_label, export_browse_layout)
        
        # 默认导出名称设置
        export_name_label = QLabel("默认导出名称:")
        export_name_edit = QLineEdit()
        export_name_edit.setText(config_manager.get("default_export_name", "vmtool_export"))
        
        # 连接信号，自动保存
        def on_export_name_changed(text):
            config_manager.set("default_export_name", text)
            # 更新导出界面中的完整路径
            if hasattr(self.parent(), 'update_export_full_path'):
                self.parent().update_export_full_path()
        
        export_name_edit.textChanged.connect(on_export_name_changed)
        export_path_layout.addRow(export_name_label, export_name_edit)
        
        # 分隔符设置
        delimiter_layout = QFormLayout()
        
        # 词条和编码分隔符
        word_code_delimiter_label = QLabel("词条和编码分隔符:")
        word_code_delimiter_combo = QComboBox()
        word_code_delimiter_combo.addItems(["Tab", ",", "|", "空格"])
        current_delimiter = config_manager.get("word_code_delimiter", "\t")
        if current_delimiter == "\t":
            word_code_delimiter_combo.setCurrentText("Tab")
        elif current_delimiter == ",":
            word_code_delimiter_combo.setCurrentText(",")
        elif current_delimiter == "|":
            word_code_delimiter_combo.setCurrentText("|")
        elif current_delimiter == " ":
            word_code_delimiter_combo.setCurrentText("空格")
        
        # 连接信号，自动保存
        def on_word_code_delimiter_changed(text):
            if text == "Tab":
                delimiter = "\t"
            elif text == ",":
                delimiter = ","
            elif text == "|":
                delimiter = "|"
            elif text == "空格":
                delimiter = " "
            config_manager.set("word_code_delimiter", delimiter)
        
        word_code_delimiter_combo.currentTextChanged.connect(on_word_code_delimiter_changed)
        
        # 编码和权重分隔符
        code_weight_delimiter_label = QLabel("编码和权重分隔符:")
        code_weight_delimiter_combo = QComboBox()
        code_weight_delimiter_combo.addItems(["Tab", ",", "|", "空格"])
        current_delimiter = config_manager.get("code_weight_delimiter", "\t")
        if current_delimiter == "\t":
            code_weight_delimiter_combo.setCurrentText("Tab")
        elif current_delimiter == ",":
            code_weight_delimiter_combo.setCurrentText(",")
        elif current_delimiter == "|":
            code_weight_delimiter_combo.setCurrentText("|")
        elif current_delimiter == " ":
            code_weight_delimiter_combo.setCurrentText("空格")
        
        # 连接信号，自动保存
        def on_code_weight_delimiter_changed(text):
            if text == "Tab":
                delimiter = "\t"
            elif text == ",":
                delimiter = ","
            elif text == "|":
                delimiter = "|"
            elif text == "空格":
                delimiter = " "
            config_manager.set("code_weight_delimiter", delimiter)
        
        code_weight_delimiter_combo.currentTextChanged.connect(on_code_weight_delimiter_changed)
        
        delimiter_layout.addRow(word_code_delimiter_label, word_code_delimiter_combo)
        delimiter_layout.addRow(code_weight_delimiter_label, code_weight_delimiter_combo)
        
        # 导入路径设置
        import_path_layout = QFormLayout()
        
        import_path_label = QLabel("默认导入路径:")
        import_path_edit = QLineEdit()
        import_path_edit.setText(config_manager.get("import_path", "./"))
        
        # 连接信号，自动保存
        def on_import_path_changed(text):
            config_manager.set("import_path", text)
            # 更新导入导出标签页中的路径
            if hasattr(self.parent(), 'import_path_edit'):
                self.parent().import_path_edit.setText(text)
        
        import_path_edit.textChanged.connect(on_import_path_changed)
        
        # 连接浏览按钮点击事件
        def browse_import_path():
            # 尝试使用 zenity 打开文件选择对话框
            try:
                import subprocess
                
                # 使用 zenity 打开文件选择对话框
                result = subprocess.run(
                    ["zenity", "--file-selection", "--title=选择导入文件", "--file-filter=文本文件 (*.txt)|*.txt|CSV文件 (*.csv)|*.csv|JSON文件 (*.json)|*.json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # 如果 zenity 成功执行（无论是否选择了文件），都不再使用Qt内置对话框
                if result.returncode == 0:
                    file_path = result.stdout.strip()
                    if file_path:
                        import_path_edit.setText(file_path)
                        config_manager.set("import_path", file_path)
                    return
            except Exception:
                pass
            
            # 如果 zenity 失败，使用Qt内置对话框
            from PyQt6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择导入文件", "./", "文本文件 (*.txt);;CSV文件 (*.csv);;JSON文件 (*.json)"
            )
            if file_path:
                import_path_edit.setText(file_path)
                config_manager.set("import_path", file_path)
        
        import_browse_button = QPushButton("浏览")
        import_browse_button.clicked.connect(browse_import_path)
        
        import_browse_layout = QHBoxLayout()
        import_browse_layout.addWidget(import_path_edit)
        import_browse_layout.addWidget(import_browse_button)
        
        import_path_layout.addRow(import_path_label, import_browse_layout)
        
        # 默认导出路径开关
        export_path_enabled_checkbox = QCheckBox("启用默认导出路径")
        export_path_enabled_checkbox.setChecked(config_manager.get("export_path_enabled", True))
        
        def on_export_path_enabled_changed(state):
            config_manager.set("export_path_enabled", state == 2)
            # 更新导出界面中的完整路径
            if hasattr(self.parent(), 'update_export_full_path'):
                self.parent().update_export_full_path()
        
        export_path_enabled_checkbox.stateChanged.connect(on_export_path_enabled_changed)
        
        # Rime 配置自动导出
        rime_layout = QVBoxLayout()
        rime_layout.addWidget(QLabel("Rime 配置自动导出:"))
        
        # 检查 ibus/rime 目录是否存在
        ibus_rime_path = os.path.expanduser("~/.config/ibus/rime")
        if os.path.exists(ibus_rime_path):
            ibus_rime_checkbox = QCheckBox(f"自动导出到 ibus/rime 目录 ({ibus_rime_path})")
            ibus_rime_checkbox.setChecked(config_manager.get("auto_export_ibus_rime", False))
            
            def on_ibus_rime_changed(state):
                config_manager.set("auto_export_ibus_rime", state == 2)
                # 更新导出界面中的完整路径
                if hasattr(self.parent(), 'update_export_full_path'):
                    self.parent().update_export_full_path()
            
            ibus_rime_checkbox.stateChanged.connect(on_ibus_rime_changed)
            rime_layout.addWidget(ibus_rime_checkbox)
        
        # 检查 fcitx5/rime 目录是否存在
        fcitx5_rime_path = os.path.expanduser("~/.local/share/fcitx5/rime")
        if os.path.exists(fcitx5_rime_path):
            fcitx5_rime_checkbox = QCheckBox(f"自动导出到 fcitx5/rime 目录 ({fcitx5_rime_path})")
            fcitx5_rime_checkbox.setChecked(config_manager.get("auto_export_fcitx5_rime", False))
            
            def on_fcitx5_rime_changed(state):
                config_manager.set("auto_export_fcitx5_rime", state == 2)
                # 更新导出界面中的完整路径
                if hasattr(self.parent(), 'update_export_full_path'):
                    self.parent().update_export_full_path()
            
            fcitx5_rime_checkbox.stateChanged.connect(on_fcitx5_rime_changed)
            rime_layout.addWidget(fcitx5_rime_checkbox)
        
        # 只导出词表选项
        only_export_words_checkbox = QCheckBox("只导出词表")
        only_export_words_checkbox.setChecked(config_manager.get("only_export_words", False))
        
        def on_only_export_words_changed(state):
            config_manager.set("only_export_words", state == 2)
            # 更新导出界面中的完整路径
            if hasattr(self.parent(), 'update_export_full_path'):
                self.parent().update_export_full_path()
        
        only_export_words_checkbox.stateChanged.connect(on_only_export_words_changed)
        rime_layout.addWidget(only_export_words_checkbox)
        
        section_layout.addLayout(export_path_layout)
        section_layout.addLayout(delimiter_layout)
        section_layout.addLayout(import_path_layout)
        section_layout.addWidget(export_path_enabled_checkbox)
        
        # 分表导出设置
        split_export_layout = QVBoxLayout()
        split_export_layout.addWidget(QLabel("分表导出设置:"))
        
        # 分表导出勾选框
        split_export_checkbox = QCheckBox("启用分表导出")
        split_export_checkbox.setChecked(config_manager.get("split_export_enabled", False))
        
        def on_split_export_changed(state):
            config_manager.set("split_export_enabled", state == 2)
            # 更新导出界面中的完整路径
            if hasattr(self.parent(), 'update_export_full_path'):
                self.parent().update_export_full_path()
        
        split_export_checkbox.stateChanged.connect(on_split_export_changed)
        split_export_layout.addWidget(split_export_checkbox)
        
        # 不同表的导出名称设置
        table_names_layout = QFormLayout()
        
        # 词表导出名称
        words_export_name_label = QLabel("词表导出名称:")
        words_export_name_edit = QLineEdit()
        words_export_name_edit.setText(config_manager.get("words_export_name", "vmtool_words"))
        
        def on_words_export_name_changed(text):
            config_manager.set("words_export_name", text)
            # 更新导出界面中的完整路径
            if hasattr(self.parent(), 'update_export_full_path'):
                self.parent().update_export_full_path()
        
        words_export_name_edit.textChanged.connect(on_words_export_name_changed)
        table_names_layout.addRow(words_export_name_label, words_export_name_edit)
        
        # 字表导出名称
        chars_export_name_label = QLabel("字表导出名称:")
        chars_export_name_edit = QLineEdit()
        chars_export_name_edit.setText(config_manager.get("chars_export_name", "vmtool_chars"))
        
        def on_chars_export_name_changed(text):
            config_manager.set("chars_export_name", text)
            # 更新导出界面中的完整路径
            if hasattr(self.parent(), 'update_export_full_path'):
                self.parent().update_export_full_path()
        
        chars_export_name_edit.textChanged.connect(on_chars_export_name_changed)
        table_names_layout.addRow(chars_export_name_label, chars_export_name_edit)
        
        # 特殊字符表导出名称
        special_export_name_label = QLabel("特殊字符表导出名称:")
        special_export_name_edit = QLineEdit()
        special_export_name_edit.setText(config_manager.get("special_export_name", "vmtool_special"))
        
        def on_special_export_name_changed(text):
            config_manager.set("special_export_name", text)
            # 更新导出界面中的完整路径
            if hasattr(self.parent(), 'update_export_full_path'):
                self.parent().update_export_full_path()
        
        special_export_name_edit.textChanged.connect(on_special_export_name_changed)
        table_names_layout.addRow(special_export_name_label, special_export_name_edit)
        
        split_export_layout.addLayout(table_names_layout)
        section_layout.addLayout(split_export_layout)
        
        section_layout.addLayout(rime_layout)
        
        section_widget.setLayout(section_layout)
        self.settings_content_layout.addWidget(section_widget)
        self.section_widgets["文件配置"] = section_widget
    
    def delete_chars_table(self):
        """删除字表"""
        reply = QMessageBox.question(
            self, "确认", "确定要删除字表吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.dict_service:
                    self.dict_service.delete_table("chars")
                    QMessageBox.information(self, "成功", "字表删除成功")
                    if hasattr(self.parent(), 'refresh_chars'):
                        self.parent().refresh_chars()
                else:
                    QMessageBox.warning(self, "警告", "词典服务未初始化")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
    
    def delete_words_table(self):
        """删除词表"""
        reply = QMessageBox.question(
            self, "确认", "确定要删除词表吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.dict_service:
                    self.dict_service.delete_table("words")
                    QMessageBox.information(self, "成功", "词表删除成功")
                    if hasattr(self.parent(), 'refresh_words'):
                        self.parent().refresh_words()
                else:
                    QMessageBox.warning(self, "警告", "词典服务未初始化")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
    
    def delete_special_table(self):
        """删除特殊字符表"""
        reply = QMessageBox.question(
            self, "确认", "确定要删除特殊字符表吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.dict_service:
                    self.dict_service.delete_table("special")
                    QMessageBox.information(self, "成功", "特殊字符表删除成功")
                    if hasattr(self.parent(), 'refresh_special'):
                        self.parent().refresh_special()
                else:
                    QMessageBox.warning(self, "警告", "词典服务未初始化")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
    
    def on_settings_order_changed(self):
        """设置类型顺序改变事件"""
        # 获取当前的设置类型顺序
        settings_types = self.findChild(QTreeWidget)
        if settings_types:
            sections = []
            for i in range(settings_types.topLevelItemCount()):
                item = settings_types.topLevelItem(i)
                sections.append(item.text(0))
            
            # 保存到配置文件
            config_manager.set("settings_order", sections)
            
            # 重新加载设置内容，按照新的顺序
            self.reload_settings_content()
    
    def reload_settings_content(self):
        """重新加载设置内容"""
        # 清除当前的设置内容
        for widget in self.section_widgets.values():
            widget.deleteLater()
        self.section_widgets.clear()
        
        # 从配置中加载设置类型顺序
        default_sections = ["主题设置", "语言设置", 
                          "配置目录", "数据库路径", "缓存设置", "统计设置", "删除表", "文件配置"]
        sections = config_manager.get("settings_order", default_sections)
        
        # 按照新的顺序加载设置
        for section in sections:
            if section == "主题设置":
                self.load_theme_settings()
            elif section == "语言设置":
                self.load_language_settings()
            elif section == "配置目录":
                self.load_config_dir_settings()
            elif section == "数据库路径":
                self.load_database_path_settings()
            elif section == "缓存设置":
                self.load_cache_settings()
            elif section == "统计设置":
                self.load_stats_settings()
            elif section == "删除表":
                self.load_delete_table_settings()
            elif section == "文件配置":
                self.load_file_config_settings()
    
    def on_settings_type_clicked(self, tree_item, column):
        """设置类型点击事件"""
        # 获取选中的设置类型
        settings_type = tree_item.text(column)
        
        # 滚动到对应的设置部分
        if settings_type in self.section_widgets:
            widget = self.section_widgets[settings_type]
            # 滚动到该控件
            scroll_area = self.parent().findChild(QScrollArea)
            if scroll_area:
                scroll_area.ensureWidgetVisible(widget)
    
    def save_settings(self):
        """保存设置"""
        # 配置会在修改时自动保存，这里只是显示一个提示
        if hasattr(self.parent(), 'show_toast'):
            self.parent().show_toast("设置已保存")
    
    def load_stats_settings(self):
        """加载统计设置"""
        section_widget = QGroupBox("统计设置")
        section_layout = QVBoxLayout()
        
        # 统计设置
        stats_layout = QFormLayout()
        
        # 词条示例上限
        example_limit_label = QLabel("词条示例上限:")
        example_limit_edit = QLineEdit()
        example_limit_edit.setText(str(config_manager.get("stats_example_limit", 20)))
        
        # 输入验证函数
        def validate_example_limit(text):
            if not text.isdigit():
                # 不是纯数字，显示toast提醒并恢复到20
                if hasattr(self.parent(), 'show_toast'):
                    self.parent().show_toast("词条示例上限必须是纯数字")
                example_limit_edit.setText("20")
                config_manager.set("stats_example_limit", 20)
            else:
                # 是纯数字，保存设置
                config_manager.set("stats_example_limit", int(text))
        
        # 连接信号，自动保存
        example_limit_edit.textChanged.connect(validate_example_limit)
        
        stats_layout.addRow(example_limit_label, example_limit_edit)
        section_layout.addLayout(stats_layout)
        section_widget.setLayout(section_layout)
        
        self.settings_content_layout.addWidget(section_widget)
        self.section_widgets["统计设置"] = section_widget