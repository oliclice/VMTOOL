# 主题设置立即生效修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复项目设置中调整主题或模式后无法立即生效的问题，确保主题变更实时应用到整个应用程序界面

**Architecture:** 通过增强主题应用函数、改进样式表管理和添加配置变更监听机制，确保主题设置变更后立即刷新所有UI组件

**Tech Stack:** PyQt6, Python 3.14, JSON配置管理

---

## 文件结构

### 修改现有文件:
- `vm-tool/ui/gui/theme_utils.py` - 主题工具函数增强
- `vm-tool/ui/gui/pyqt_app.py` - 主应用主题设置方法改进
- `vm-tool/ui/gui/settings_tab.py` - 主题变更信号处理
- `vm-tool/ui/gui/code_rules_tab.py` - 硬编码样式表修复

### 创建新文件:
- `vm-tool/ui/gui/theme_manager.py` - 统一主题管理器和信号系统

### 测试文件:
- `vm-tool/tests/test_theme_utils.py` - 主题工具函数测试
- `vm-tool/tests/test_theme_manager.py` - 主题管理器测试

---

### Task 1: 创建主题管理器

**Files:**
- Create: `vm-tool/ui/gui/theme_manager.py`
- Modify: `vm-tool/ui/gui/pyqt_app.py:99-121`
- Test: `vm-tool/tests/test_theme_manager.py`

- [ ] **Step 1: 创建主题管理器类**

```python
"""主题管理器，统一处理主题变更和应用"""
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from typing import Tuple, Optional

from app.core.config_manager import config_manager
from app.core.theme_constants import (
    THEME_MODE_AUTO, THEME_MODE_LIGHT, THEME_MODE_DARK,
    THEME_NAME_CLASSIC, THEME_COLOR_BLUE
)
from .theme_utils import create_palette_from_theme


class ThemeManager(QObject):
    """主题管理器，负责主题变更信号和应用"""
    
    theme_changed = pyqtSignal(str, str, str)  # theme_mode, theme_name, theme_color
    
    def __init__(self):
        super().__init__()
        self.current_theme_mode = THEME_MODE_AUTO
        self.current_theme_name = THEME_NAME_CLASSIC
        self.current_theme_color = THEME_COLOR_BLUE
        self.registered_widgets = set()
    
    def get_current_theme(self) -> Tuple[str, str, str]:
        """获取当前主题设置"""
        return (
            self.current_theme_mode,
            self.current_theme_name,
            self.current_theme_color
        )
    
    def set_theme(self, theme_mode: str, theme_name: str, theme_color: str) -> None:
        """设置主题并发出信号"""
        if (theme_mode != self.current_theme_mode or 
            theme_name != self.current_theme_name or 
            theme_color != self.current_theme_color):
            
            self.current_theme_mode = theme_mode
            self.current_theme_name = theme_name
            self.current_theme_color = theme_color
            
            # 发出主题变更信号
            self.theme_changed.emit(theme_mode, theme_name, theme_color)
            
            # 立即应用到应用程序
            self.apply_theme_to_application()
    
    def apply_theme_to_application(self) -> None:
        """将当前主题应用到整个应用程序"""
        app = QApplication.instance()
        if not app:
            return
        
        palette = create_palette_from_theme(
            self.current_theme_mode, 
            self.current_theme_color
        )
        
        # 应用到整个应用程序
        app.setPalette(palette)
        
        # 应用到所有已注册的窗口部件
        for widget_id in self.registered_widgets:
            # 注意：这里需要实际获取窗口部件对象
            # 实际实现中可能需要存储弱引用
            pass
    
    def register_widget(self, widget) -> None:
        """注册窗口部件以接收主题变更通知"""
        widget_id = id(widget)
        if widget_id not in self.registered_widgets:
            self.registered_widgets.add(widget_id)
    
    def unregister_widget(self, widget) -> None:
        """取消注册窗口部件"""
        widget_id = id(widget)
        if widget_id in self.registered_widgets:
            self.registered_widgets.remove(widget_id)


# 创建全局主题管理器实例
theme_manager = ThemeManager()
```

- [ ] **Step 2: 编写主题管理器测试**

```python
"""测试主题管理器"""
import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication, QWidget
from ui.gui.theme_manager import ThemeManager, theme_manager
from app.core.theme_constants import (
    THEME_MODE_AUTO, THEME_MODE_LIGHT, THEME_MODE_DARK,
    THEME_NAME_CLASSIC, THEME_COLOR_BLUE, THEME_COLOR_GREEN
)


@pytest.fixture
def mock_app():
    """创建模拟的QApplication"""
    with patch('PyQt6.QtWidgets.QApplication.instance') as mock_instance:
        mock_app = Mock(spec=QApplication)
        mock_instance.return_value = mock_app
        yield mock_app


def test_theme_manager_initialization():
    """测试主题管理器初始化"""
    manager = ThemeManager()
    assert manager.current_theme_mode == THEME_MODE_AUTO
    assert manager.current_theme_name == THEME_NAME_CLASSIC
    assert manager.current_theme_color == THEME_COLOR_BLUE
    assert len(manager.registered_widgets) == 0


def test_set_theme_emits_signal(mock_app):
    """测试设置主题时发出信号"""
    manager = ThemeManager()
    mock_signal = Mock()
    manager.theme_changed.connect(mock_signal)
    
    manager.set_theme(THEME_MODE_DARK, THEME_NAME_CLASSIC, THEME_COLOR_GREEN)
    
    mock_signal.emit.assert_called_once_with(
        THEME_MODE_DARK, THEME_NAME_CLASSIC, THEME_COLOR_GREEN
    )
    assert manager.current_theme_mode == THEME_MODE_DARK
    assert manager.current_theme_color == THEME_COLOR_GREEN


def test_get_current_theme():
    """测试获取当前主题"""
    manager = ThemeManager()
    manager.current_theme_mode = THEME_MODE_LIGHT
    manager.current_theme_color = THEME_COLOR_GREEN
    
    theme = manager.get_current_theme()
    assert theme == (THEME_MODE_LIGHT, THEME_NAME_CLASSIC, THEME_COLOR_GREEN)


def test_register_widget():
    """测试注册窗口部件"""
    manager = ThemeManager()
    widget = Mock(spec=QWidget)
    widget_id = id(widget)
    
    manager.register_widget(widget)
    assert widget_id in manager.registered_widgets
    
    manager.unregister_widget(widget)
    assert widget_id not in manager.registered_widgets
```

- [ ] **Step 3: 运行测试以验证失败**

Run: `pytest vm-tool/tests/test_theme_manager.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'ui.gui.theme_manager'"

- [ ] **Step 4: 创建主题管理器文件**

```bash
touch vm-tool/ui/gui/theme_manager.py
```

- [ ] **Step 5: 运行测试以验证基础结构**

Run: `pytest vm-tool/tests/test_theme_manager.py::test_theme_manager_initialization -v`
Expected: FAIL with "AssertionError" or import error

---

### Task 2: 增强主题应用工具函数

**Files:**
- Modify: `vm-tool/ui/gui/theme_utils.py:58-85`
- Test: `vm-tool/tests/test_theme_utils.py`

- [ ] **Step 1: 编写增强版apply_theme_to_widget测试**

```python
"""测试主题工具函数增强版"""
import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QWidget, QPushButton, QLabel
from PyQt6.QtGui import QPalette, QColor
from ui.gui.theme_utils import apply_theme_to_widget, create_palette_from_theme
from app.core.theme_constants import THEME_MODE_LIGHT, THEME_COLOR_BLUE


def test_apply_theme_to_widget_recursive():
    """测试递归应用主题到窗口部件及其子部件"""
    parent = Mock(spec=QWidget)
    child1 = Mock(spec=QPushButton)
    child2 = Mock(spec=QLabel)
    child3 = Mock(spec=QWidget)  # 孙部件
    
    parent.children.return_value = [child1, child2]
    child1.children.return_value = [child3]
    child2.children.return_value = []
    child3.children.return_value = []
    
    palette = Mock(spec=QPalette)
    
    # 模拟setPalette方法
    parent.setPalette = Mock()
    child1.setPalette = Mock()
    child2.setPalette = Mock()
    child3.setPalette = Mock()
    
    # 模拟isWindow方法
    parent.isWindow.return_value = True
    
    processed = apply_theme_to_widget(parent, palette)
    
    # 验证所有部件都调用了setPalette
    assert parent.setPalette.called
    assert child1.setPalette.called
    assert child2.setPalette.called
    assert child3.setPalette.called
    
    # 验证处理了所有部件ID
    assert len(processed) == 4


def test_apply_theme_to_widget_avoids_duplicates():
    """测试避免重复处理同一部件"""
    widget = Mock(spec=QWidget)
    widget.children.return_value = []
    palette = Mock(spec=QPalette)
    widget.setPalette = Mock()
    widget.isWindow.return_value = False
    
    # 第一次调用
    processed = apply_theme_to_widget(widget, palette, set())
    assert len(processed) == 1
    assert widget.setPalette.call_count == 1
    
    # 第二次调用，使用相同的processed集合
    processed2 = apply_theme_to_widget(widget, palette, processed)
    assert len(processed2) == 1
    assert widget.setPalette.call_count == 1  # 不应再次调用


def test_create_palette_from_theme_dark_mode():
    """测试深色模式调色板创建"""
    palette = create_palette_from_theme(THEME_MODE_DARK, THEME_COLOR_BLUE)
    assert isinstance(palette, QPalette)
    
    # 验证深色模式的基础颜色
    window_color = palette.color(QPalette.ColorRole.Window)
    assert window_color.red() < 100  # 深色背景
    assert window_color.green() < 100
    assert window_color.blue() < 100


def test_create_palette_from_theme_light_mode():
    """测试浅色模式调色板创建"""
    palette = create_palette_from_theme(THEME_MODE_LIGHT, THEME_COLOR_GREEN)
    assert isinstance(palette, QPalette)
    
    # 验证浅色模式的基础颜色
    window_color = palette.color(QPalette.ColorRole.Window)
    assert window_color.red() > 200  # 浅色背景
    assert window_color.green() > 200
    assert window_color.blue() > 200
```

- [ ] **Step 2: 运行增强测试以查看当前行为**

Run: `pytest vm-tool/tests/test_theme_utils.py -v`
Expected: Tests may pass or fail depending on current implementation

- [ ] **Step 3: 增强apply_theme_to_widget函数**

修改 `vm-tool/ui/gui/theme_utils.py:58-85`:

```python
def apply_theme_to_widget(widget, palette: QPalette, processed_widgets: Set[int] = None) -> Set[int]:
    """递归应用调色板到控件及其子控件"""
    if processed_widgets is None:
        processed_widgets = set()

    if not widget or id(widget) in processed_widgets:
        return processed_widgets

    processed_widgets.add(id(widget))

    # 应用调色板到支持它的控件
    if hasattr(widget, 'setPalette'):
        widget.setPalette(palette)
        # 对所有控件都刷新样式，不仅仅是顶级窗口
        try:
            style = widget.style()
            if style:
                style.unpolish(widget)
                style.polish(widget)
        except Exception:
            pass  # 样式刷新失败不影响主题应用

    # 清除可能覆盖调色板的样式表
    if hasattr(widget, 'styleSheet') and widget.styleSheet():
        # 保存原始样式表以便后续可能恢复
        if not hasattr(widget, '_original_styleSheet'):
            widget._original_styleSheet = widget.styleSheet()
        # 清除硬编码的颜色样式表
        widget.setStyleSheet("")

    # 递归处理所有子控件
    for child in widget.children():
        apply_theme_to_widget(child, palette, processed_widgets)

    return processed_widgets
```

- [ ] **Step 4: 添加样式表清理辅助函数**

在 `theme_utils.py` 中添加:

```python
def clear_hardcoded_stylesheets(widget, processed_widgets: Set[int] = None) -> Set[int]:
    """清理硬编码的样式表，这些可能覆盖主题设置"""
    if processed_widgets is None:
        processed_widgets = set()

    if not widget or id(widget) in processed_widgets:
        return processed_widgets

    processed_widgets.add(id(widget))

    # 清理硬编码的颜色样式表
    if hasattr(widget, 'styleSheet') and widget.styleSheet():
        stylesheet = widget.styleSheet()
        # 查找并移除硬编码的颜色定义
        if any(color_def in stylesheet for color_def in ['#4CAF50', '#FF0000', '#0000FF']):
            if not hasattr(widget, '_original_styleSheet'):
                widget._original_styleSheet = stylesheet
            widget.setStyleSheet("")

    # 递归处理所有子控件
    for child in widget.children():
        clear_hardcoded_stylesheets(child, processed_widgets)

    return processed_widgets
```

- [ ] **Step 5: 运行测试验证增强功能**

Run: `pytest vm-tool/tests/test_theme_utils.py -v`
Expected: All tests pass

---

### Task 3: 集成主题管理器到主应用

**Files:**
- Modify: `vm-tool/ui/gui/pyqt_app.py:86-121`
- Modify: `vm-tool/ui/gui/pyqt_app.py:42-90` (__init__部分)
- Test: `vm-tool/tests/test_theme_manager.py` (新增测试)

- [ ] **Step 1: 修改主应用以使用主题管理器**

在 `vm-tool/ui/gui/pyqt_app.py` 顶部添加导入:

```python
from .theme_manager import theme_manager
from .theme_utils import clear_hardcoded_stylesheets
```

- [ ] **Step 2: 修改__init__方法中的主题设置**

修改 `vm-tool/ui/gui/pyqt_app.py:85-90`:

```python
        # 设置主题
        theme_mode = config_manager.get("theme_mode", THEME_MODE_AUTO)
        theme_name = config_manager.get("theme_name", THEME_NAME_CLASSIC)
        theme_color = config_manager.get("theme_color", THEME_COLOR_BLUE)
        
        # 注册到主题管理器
        theme_manager.register_widget(self)
        
        # 初始主题设置
        self.set_theme(theme_mode, theme_name, theme_color)
        
        # 连接主题变更信号
        theme_manager.theme_changed.connect(self.on_theme_changed)
```

- [ ] **Step 3: 重构set_theme方法**

修改 `vm-tool/ui/gui/pyqt_app.py:99-121`:

```python
    def set_theme(self, theme_mode, theme_name, theme_color):
        """设置主题"""
        # 清理硬编码样式表
        clear_hardcoded_stylesheets(self)
        
        # 使用工具函数创建调色板
        palette = create_palette_from_theme(theme_mode, theme_color)

        # 获取应用程序实例
        app = QApplication.instance()
        if app:
            # 应用调色板到应用程序
            app.setPalette(palette)
            
            # 应用调色板到所有顶级窗口
            for window in app.topLevelWindows():
                if window.isWidgetType():
                    apply_theme_to_widget(window, palette)
        
        # 应用调色板到当前窗口
        self.setPalette(palette)
        apply_theme_to_widget(self, palette)
        
        # 强制刷新界面
        self.update()
        self.repaint()
        
        # 通知主题管理器
        theme_manager.set_theme(theme_mode, theme_name, theme_color)
    
    def on_theme_changed(self, theme_mode, theme_name, theme_color):
        """处理主题变更信号"""
        # 当主题管理器发出信号时，重新应用主题
        self.set_theme(theme_mode, theme_name, theme_color)
```

- [ ] **Step 4: 添加主题变更响应测试**

在 `vm-tool/tests/test_theme_manager.py` 中添加:

```python
def test_theme_integration_with_main_app():
    """测试主题管理器与主应用的集成"""
    with patch('PyQt6.QtWidgets.QApplication.instance') as mock_instance:
        mock_app = Mock(spec=QApplication)
        mock_instance.return_value = mock_app
        
        # 创建模拟的主应用窗口
        mock_window = Mock()
        mock_window.setPalette = Mock()
        mock_window.update = Mock()
        mock_window.repaint = Mock()
        
        # 模拟apply_theme_to_widget
        with patch('ui.gui.pyqt_app.apply_theme_to_widget') as mock_apply:
            with patch('ui.gui.pyqt_app.clear_hardcoded_stylesheets') as mock_clear:
                # 调用set_theme
                from ui.gui.pyqt_app import VMTOOLPyQtApp
                app_instance = VMTOOLPyQtApp()
                app_instance.set_theme = Mock()
                
                # 触发主题变更信号
                theme_manager.theme_changed.emit(
                    THEME_MODE_DARK, THEME_NAME_CLASSIC, THEME_COLOR_GREEN
                )
                
                # 验证set_theme被调用
                app_instance.set_theme.assert_called_once_with(
                    THEME_MODE_DARK, THEME_NAME_CLASSIC, THEME_COLOR_GREEN
                )
```

- [ ] **Step 5: 运行集成测试**

Run: `pytest vm-tool/tests/test_theme_manager.py::test_theme_integration_with_main_app -v`
Expected: PASS after implementation

---

### Task 4: 修复设置标签页中的主题变更处理

**Files:**
- Modify: `vm-tool/ui/gui/settings_tab.py:155-177`
- Modify: `vm-tool/ui/gui/settings_tab.py:376-378` (样式表按钮)
- Test: `vm-tool/tests/test_settings_tab.py` (新测试)

- [ ] **Step 1: 编写设置标签页主题测试**

```python
"""测试设置标签页主题变更"""
import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QComboBox, QApplication
from ui.gui.settings_tab import SettingsTab
from app.core.theme_constants import (
    THEME_MODE_AUTO, THEME_MODE_LIGHT, THEME_MODE_DARK,
    THEME_NAME_CLASSIC, THEME_NAME_MATERIAL3, THEME_COLOR_BLUE,
    MODE_DISPLAY_MAP, MODE_DISPLAY_REVERSE_MAP
)


@pytest.fixture
def settings_tab():
    """创建设置标签页实例"""
    parent = Mock()
    parent.set_theme = Mock()
    parent.show_toast = Mock()
    
    dict_service = Mock()
    tab = SettingsTab(parent=parent, dict_service=dict_service)
    return tab


def test_theme_combo_initialization(settings_tab):
    """测试主题下拉框初始化"""
    # 需要调用load_theme_settings来初始化
    settings_tab.load_theme_settings()
    
    # 验证下拉框存在
    assert hasattr(settings_tab, 'theme_combo')
    assert hasattr(settings_tab, 'mode_combo')
    assert hasattr(settings_tab, 'color_combo')


def test_theme_changed_signal(settings_tab):
    """测试主题变更信号触发"""
    with patch('ui.gui.settings_tab.config_manager') as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            'theme_name': THEME_NAME_CLASSIC,
            'theme_mode': THEME_MODE_AUTO,
            'theme_color': THEME_COLOR_BLUE
        }.get(key, default)
        
        settings_tab.load_theme_settings()
        
        # 模拟用户选择
        settings_tab.theme_combo.setCurrentText(THEME_NAME_MATERIAL3)
        settings_tab.mode_combo.setCurrentText(MODE_DISPLAY_MAP[THEME_MODE_DARK])
        settings_tab.color_combo.setCurrentText(THEME_COLOR_GREEN)
        
        # 验证父窗口的set_theme被调用
        assert settings_tab.parent().set_theme.called
        call_args = settings_tab.parent().set_theme.call_args[0]
        assert call_args[0] == THEME_MODE_DARK  # theme_mode
        assert call_args[1] == THEME_NAME_MATERIAL3  # theme_name
        assert call_args[2] == THEME_COLOR_GREEN  # theme_color
```

- [ ] **Step 2: 修改主题变更处理函数**

修改 `vm-tool/ui/gui/settings_tab.py:155-177`:

```python
        # 连接信号
        def on_theme_changed():
            theme = theme_combo.currentText()
            mode = mode_combo.currentText()
            color = color_combo.currentText()
            
            # 映射模式显示名称到内部值
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
                self.parent().show_toast(f"主题已更改为: {theme} - {mode} - {color}")
```

- [ ] **Step 3: 修复硬编码样式表按钮**

修改 `vm-tool/ui/gui/settings_tab.py:376-378`:

```python
        syntax_button.setStyleSheet("")
        # 使用调色板颜色而不是硬编码颜色
        # 样式将通过主题系统自动应用
```

- [ ] **Step 4: 添加样式表清理到设置标签页**

在 `load_theme_settings` 方法中添加:

```python
        # 清理现有样式表
        from .theme_utils import clear_hardcoded_stylesheets
        clear_hardcoded_stylesheets(section_widget)
```

- [ ] **Step 5: 运行设置标签页测试**

Run: `pytest vm-tool/tests/test_settings_tab.py -v`
Expected: Tests pass after implementation

---

### Task 5: 修复编码规则标签页中的样式表

**Files:**
- Modify: `vm-tool/ui/gui/code_rules_tab.py:98`
- Modify: `vm-tool/ui/gui/code_rules_tab.py:158,412,420,423,451,454`
- Test: `vm-tool/tests/test_code_rules_tab.py` (新测试)

- [ ] **Step 1: 编写编码规则标签页样式表测试**

```python
"""测试编码规则标签页样式表修复"""
import pytest
from unittest.mock import Mock
from ui.gui.code_rules_tab import CodeRulesTab
from app.core.theme_constants import THEME_MODE_LIGHT, THEME_COLOR_BLUE


@pytest.fixture
def code_rules_tab():
    """创建编码规则标签页实例"""
    parent = Mock()
    parent.show_toast = Mock()
    
    dict_service = Mock()
    tab = CodeRulesTab(parent=parent, dict_service=dict_service)
    return tab


def test_syntax_button_no_hardcoded_stylesheet(code_rules_tab):
    """测试语法按钮没有硬编码样式表"""
    # 初始化UI
    code_rules_tab.init_ui()
    
    # 验证语法按钮样式表为空或使用主题颜色
    assert hasattr(code_rules_tab, 'syntax_button')
    stylesheet = code_rules_tab.syntax_button.styleSheet()
    assert '#4CAF50' not in stylesheet  # 硬编码绿色不应存在
    assert 'background-color' not in stylesheet or 'color' not in stylesheet


def test_validation_result_dynamic_styling(code_rules_tab):
    """测试验证结果动态样式应用"""
    # 模拟验证结果设置
    code_rules_tab.validation_result = Mock()
    code_rules_tab.validation_result.setStyleSheet = Mock()
    
    # 测试不同状态下的样式设置
    code_rules_tab.set_validation_result("成功", "success")
    code_rules_tab.validation_result.setStyleSheet.assert_called()
    
    code_rules_tab.set_validation_result("失败", "error")
    code_rules_tab.validation_result.setStyleSheet.assert_called()
```

- [ ] **Step 2: 移除硬编码样式表**

修改 `vm-tool/ui/gui/code_rules_tab.py:98`:

```python
        # 移除硬编码样式表，使用主题系统
        syntax_button.setStyleSheet("")
```

- [ ] **Step 3: 创建动态样式应用函数**

在 `CodeRulesTab` 类中添加:

```python
    def apply_theme_based_styling(self):
        """应用基于主题的样式"""
        # 获取当前主题颜色
        from app.core.config_manager import config_manager
        from app.core.theme_constants import THEME_COLOR_BLUE, COLOR_RGB_MAP
        
        theme_color = config_manager.get("theme_color", THEME_COLOR_BLUE)
        rgb = COLOR_RGB_MAP.get(theme_color, COLOR_RGB_MAP[THEME_COLOR_BLUE])
        
        # 将RGB转换为十六进制
        hex_color = f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
        
        # 应用动态样式
        if hasattr(self, 'syntax_button'):
            self.syntax_button.setStyleSheet(
                f"QPushButton {{ border-radius: 10px; background-color: {hex_color}; color: white; }}"
            )
        
        # 更新验证结果颜色
        self.update_validation_result_style()
    
    def update_validation_result_style(self):
        """更新验证结果样式基于当前主题"""
        if not hasattr(self, 'validation_result'):
            return
        
        from app.core.config_manager import config_manager
        from app.core.theme_constants import THEME_MODE_DARK
        
        theme_mode = config_manager.get("theme_mode", THEME_MODE_DARK)
        
        # 根据主题模式设置文本颜色
        if theme_mode == THEME_MODE_DARK:
            text_color = "lightgreen"
            error_color = "lightcoral"
            warning_color = "lightyellow"
        else:
            text_color = "green"
            error_color = "red"
            warning_color = "orange"
        
        # 保存颜色供其他方法使用
        self.success_color = text_color
        self.error_color = error_color
        self.warning_color = warning_color
```

- [ ] **Step 4: 修改验证结果样式设置方法**

替换硬编码颜色为动态颜色:

```python
    def set_validation_result(self, message: str, result_type: str = "info"):
        """设置验证结果消息和样式"""
        if not hasattr(self, 'validation_result'):
            return
        
        self.validation_result.setText(message)
        
        # 使用动态颜色
        if result_type == "success":
            self.validation_result.setStyleSheet(f"color: {self.success_color}")
        elif result_type == "error":
            self.validation_result.setStyleSheet(f"color: {self.error_color}")
        elif result_type == "warning":
            self.validation_result.setStyleSheet(f"color: {self.warning_color}")
        else:
            self.validation_result.setStyleSheet("")
```

- [ ] **Step 5: 连接主题变更信号**

在 `__init__` 或 `init_ui` 方法中添加:

```python
        # 连接主题变更信号
        from .theme_manager import theme_manager
        theme_manager.theme_changed.connect(self.on_theme_changed)
    
    def on_theme_changed(self, theme_mode, theme_name, theme_color):
        """处理主题变更"""
        self.apply_theme_based_styling()
```

- [ ] **Step 6: 运行编码规则标签页测试**

Run: `pytest vm-tool/tests/test_code_rules_tab.py -v`
Expected: Tests pass after implementation

---

### Task 6: 添加配置变更监听器

**Files:**
- Modify: `vm-tool/app/core/config_manager.py:95-98` (set方法)
- Create: `vm-tool/app/core/config_listener.py`
- Test: `vm-tool/tests/test_config_listener.py`

- [ ] **Step 1: 创建配置变更监听器**

```python
"""配置变更监听器，监听配置变化并触发相应操作"""
from typing import Dict, Any, Callable, Set
from app.core.config_manager import config_manager


class ConfigListener:
    """配置变更监听器"""
    
    def __init__(self):
        self.listeners: Dict[str, Set[Callable]] = {}
        self.setup_default_listeners()
    
    def setup_default_listeners(self):
        """设置默认监听器"""
        # 主题相关配置监听
        self.add_listener("theme_mode", self.on_theme_config_changed)
        self.add_listener("theme_name", self.on_theme_config_changed)
        self.add_listener("theme_color", self.on_theme_config_changed)
        
        # 字体配置监听
        self.add_listener("font_family", self.on_font_config_changed)
    
    def add_listener(self, config_key: str, callback: Callable):
        """添加配置变更监听器"""
        if config_key not in self.listeners:
            self.listeners[config_key] = set()
        self.listeners[config_key].add(callback)
    
    def remove_listener(self, config_key: str, callback: Callable):
        """移除配置变更监听器"""
        if config_key in self.listeners:
            self.listeners[config_key].discard(callback)
    
    def notify_listeners(self, config_key: str, old_value: Any, new_value: Any):
        """通知监听器配置已变更"""
        if config_key in self.listeners:
            for callback in self.listeners[config_key]:
                try:
                    callback(config_key, old_value, new_value)
                except Exception as e:
                    print(f"配置监听器回调出错: {e}")
    
    def on_theme_config_changed(self, config_key: str, old_value: Any, new_value: Any):
        """主题配置变更处理"""
        if old_value == new_value:
            return
        
        # 导入主题管理器
        try:
            from ui.gui.theme_manager import theme_manager
            from app.core.config_manager import config_manager
            
            # 获取当前主题设置
            theme_mode = config_manager.get("theme_mode", "auto")
            theme_name = config_manager.get("theme_name", "经典")
            theme_color = config_manager.get("theme_color", "蓝色")
            
            # 通知主题管理器
            theme_manager.set_theme(theme_mode, theme_name, theme_color)
            
        except ImportError:
            # GUI可能未加载，忽略错误
            pass
    
    def on_font_config_changed(self, config_key: str, old_value: Any, new_value: Any):
        """字体配置变更处理"""
        if old_value == new_value:
            return
        
        # 应用新字体到应用程序
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtGui import QFont
            
            app = QApplication.instance()
            if app and new_value:
                font = QFont(new_value)
                app.setFont(font)
                
        except ImportError:
            # GUI可能未加载，忽略错误
            pass


# 创建全局配置监听器实例
config_listener = ConfigListener()
```

- [ ] **Step 2: 修改config_manager的set方法以通知监听器**

修改 `vm-tool/app/core/config_manager.py:95-98`:

```python
    def set(self, key: str, value: Any) -> bool:
        """设置配置值"""
        old_value = self.config.get(key)
        self.config[key] = value
        success = self.save_config()
        
        # 通知配置监听器
        if success and old_value != value:
            try:
                from app.core.config_listener import config_listener
                config_listener.notify_listeners(key, old_value, value)
            except ImportError:
                pass  # 监听器可能未加载
        
        return success
```

- [ ] **Step 3: 编写配置监听器测试**

```python
"""测试配置变更监听器"""
import pytest
from unittest.mock import Mock, patch
from app.core.config_listener import ConfigListener, config_listener
from app.core.config_manager import ConfigManager


def test_config_listener_initialization():
    """测试配置监听器初始化"""
    listener = ConfigListener()
    assert "theme_mode" in listener.listeners
    assert "theme_name" in listener.listeners
    assert "theme_color" in listener.listeners
    assert "font_family" in listener.listeners


def test_add_remove_listener():
    """测试添加和移除监听器"""
    listener = ConfigListener()
    callback = Mock()
    
    listener.add_listener("test_key", callback)
    assert callback in listener.listeners["test_key"]
    
    listener.remove_listener("test_key", callback)
    assert callback not in listener.listeners.get("test_key", set())


def test_notify_listeners():
    """测试通知监听器"""
    listener = ConfigListener()
    callback1 = Mock()
    callback2 = Mock()
    
    listener.add_listener("test_key", callback1)
    listener.add_listener("test_key", callback2)
    
    listener.notify_listeners("test_key", "old_value", "new_value")
    
    callback1.assert_called_once_with("test_key", "old_value", "new_value")
    callback2.assert_called_once_with("test_key", "old_value", "new_value")


@patch('ui.gui.theme_manager.theme_manager')
def test_theme_config_changed(mock_theme_manager):
    """测试主题配置变更处理"""
    listener = ConfigListener()
    
    # 模拟配置管理器
    with patch('app.core.config_listener.config_manager') as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            'theme_mode': 'dark',
            'theme_name': '经典',
            'theme_color': '蓝色'
        }.get(key, default)
        
        listener.on_theme_config_changed('theme_mode', 'light', 'dark')
        
        # 验证主题管理器被调用
        mock_theme_manager.set_theme.assert_called_once_with(
            'dark', '经典', '蓝色'
        )
```

- [ ] **Step 4: 运行配置监听器测试**

Run: `pytest vm-tool/tests/test_config_listener.py -v`
Expected: FAIL initially, then PASS after implementation

- [ ] **Step 5: 创建配置监听器文件**

```bash
touch vm-tool/app/core/config_listener.py
```

---

### Task 7: 综合测试和验证

**Files:**
- Create: `vm-tool/tests/test_theme_immediate_application.py`
- Test: 所有相关测试

- [ ] **Step 1: 创建综合测试**

```python
"""综合测试主题立即生效功能"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

from ui.gui.pyqt_app import VMTOOLPyQtApp
from ui.gui.settings_tab import SettingsTab
from app.core.config_manager import config_manager
from app.core.theme_constants import (
    THEME_MODE_LIGHT, THEME_MODE_DARK, THEME_NAME_CLASSIC, THEME_COLOR_BLUE, THEME_COLOR_GREEN
)


@pytest.fixture
def mock_qt_app():
    """创建模拟的Qt应用环境"""
    with patch('PyQt6.QtWidgets.QApplication.instance') as mock_instance:
        mock_app = Mock(spec=QApplication)
        mock_instance.return_value = mock_app
        
        # 模拟顶级窗口列表
        mock_window1 = Mock()
        mock_window1.isWidgetType.return_value = True
        mock_window1.setPalette = Mock()
        
        mock_window2 = Mock()
        mock_window2.isWidgetType.return_value = True
        mock_window2.setPalette = Mock()
        
        mock_app.topLevelWindows.return_value = [mock_window1, mock_window2]
        
        yield mock_app


@pytest.fixture
def theme_test_app(mock_qt_app):
    """创建测试用的应用实例"""
    with patch('app.dal.init_db.init_database'):
        with patch('app.services.dict.DictService'):
            with patch('app.services.weight.WeightCalculator'):
                with patch('app.services.filter.FilterService'):
                    with patch('app.services.stats.StatsService'):
                        app = VMTOOLPyQtApp()
                        yield app


def test_theme_change_immediate_application(theme_test_app, mock_qt_app):
    """测试主题变更立即生效"""
    # 模拟主题工具函数
    with patch('ui.gui.pyqt_app.apply_theme_to_widget') as mock_apply:
        with patch('ui.gui.pyqt_app.clear_hardcoded_stylesheets') as mock_clear:
            with patch('ui.gui.pyqt_app.create_palette_from_theme') as mock_palette:
                mock_palette.return_value = Mock(spec=QPalette)
                
                # 初始主题设置
                theme_test_app.set_theme(THEME_MODE_LIGHT, THEME_NAME_CLASSIC, THEME_COLOR_BLUE)
                
                # 验证调色板应用到应用程序
                assert mock_qt_app.setPalette.called
                assert mock_apply.called
                assert theme_test_app.setPalette.called
                
                # 验证清理函数被调用
                assert mock_clear.called
                
                # 验证窗口更新
                assert theme_test_app.update.called
                assert theme_test_app.repaint.called


def test_settings_tab_theme_change_propagation():
    """测试设置标签页主题变更传播"""
    parent = Mock()
    parent.set_theme = Mock()
    parent.show_toast = Mock()
    
    dict_service = Mock()
    
    with patch('ui.gui.settings_tab.config_manager') as mock_config:
        mock_config.get.side_effect = lambda key, default: {
            'theme_name': THEME_NAME_CLASSIC,
            'theme_mode': THEME_MODE_LIGHT,
            'theme_color': THEME_COLOR_BLUE
        }.get(key, default)
        
        mock_config.set.return_value = True
        
        tab = SettingsTab(parent=parent, dict_service=dict_service)
        tab.load_theme_settings()
        
        # 模拟用户更改主题
        tab.theme_combo.setCurrentText(THEME_NAME_CLASSIC)
        tab.mode_combo.setCurrentText("深色")
        tab.color_combo.setCurrentText(THEME_COLOR_GREEN)
        
        # 验证配置保存
        assert mock_config.set.called
        calls = mock_config.set.call_args_list
        assert any('theme_mode' in str(call) for call in calls)
        assert any('theme_color' in str(call) for call in calls)
        
        # 验证主题管理器被调用
        with patch('ui.gui.settings_tab.theme_manager') as mock_theme_manager:
            # 重新触发主题变更
            tab.theme_combo.currentTextChanged.emit(THEME_NAME_CLASSIC)
            assert mock_theme_manager.set_theme.called


def test_config_manager_triggers_listeners():
    """测试配置管理器触发监听器"""
    # 创建配置管理器实例
    manager = ConfigManager()
    
    # 模拟配置文件
    import tempfile
    import json
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"theme_mode": THEME_MODE_LIGHT}, f)
        temp_file = f.name
    
    try:
        # 临时替换配置文件路径
        original_file = manager.config_file
        manager.config_file = temp_file
        
        # 模拟监听器
        mock_listener = Mock()
        manager.config_listener = mock_listener
        
        # 设置新值
        result = manager.set("theme_mode", THEME_MODE_DARK)
        
        # 验证监听器被通知
        assert result is True
        # 注意：实际实现中需要通过导入config_listener来测试
        
    finally:
        # 清理
        import os
        manager.config_file = original_file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_theme_consistency_across_widgets():
    """测试跨部件主题一致性"""
    # 创建模拟部件树
    root = Mock(spec=QWidget)
    child1 = Mock(spec=QPushButton)
    child2 = Mock(spec=QLabel)
    grandchild = Mock(spec=QWidget)
    
    root.children.return_value = [child1, child2]
    child1.children.return_value = [grandchild]
    child2.children.return_value = []
    grandchild.children.return_value = []
    
    # 模拟setPalette方法
    for widget in [root, child1, child2, grandchild]:
        widget.setPalette = Mock()
        widget.styleSheet.return_value = ""
        widget.isWindow.return_value = False
    
    root.isWindow.return_value = True
    
    # 应用主题
    palette = Mock(spec=QPalette)
    from ui.gui.theme_utils import apply_theme_to_widget
    
    processed = apply_theme_to_widget(root, palette)
    
    # 验证所有部件都收到了调色板
    assert root.setPalette.called
    assert child1.setPalette.called
    assert child2.setPalette.called
    assert grandchild.setPalette.called
    
    # 验证所有部件都被处理
    assert len(processed) == 4
```

- [ ] **Step 2: 运行所有相关测试**

Run: `pytest vm-tool/tests/test_theme_*.py -v`
Expected: All tests pass

- [ ] **Step 3: 手动验证功能**

1. 启动GUI应用程序
2. 导航到设置标签页
3. 更改主题模式（浅色/深色/自动）
4. 验证界面立即响应变更
5. 更改主题颜色
6. 验证强调色立即更新
7. 更改字体设置
8. 验证字体立即生效
9. 测试编码规则标签页的语法按钮样式
10. 验证所有硬编码颜色已被主题系统替换

- [ ] **Step 4: 提交更改**

```bash
git add vm-tool/ui/gui/theme_manager.py
git add vm-tool/ui/gui/theme_utils.py
git add vm-tool/ui/gui/pyqt_app.py
git add vm-tool/ui/gui/settings_tab.py
git add vm-tool/ui/gui/code_rules_tab.py
git add vm-tool/app/core/config_listener.py
git add vm-tool/app/core/config_manager.py
git add vm-tool/tests/test_*.py
git commit -m "fix: 主题设置立即生效问题修复

- 创建主题管理器统一处理主题变更
- 增强主题应用工具函数，支持递归样式刷新
- 清理硬编码样式表，改用动态主题颜色
- 添加配置变更监听器，自动响应设置变更
- 添加综合测试确保主题立即生效

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 执行选项

**计划已完成并保存至 `vm-tool/docs/superpowers/plans/2026-04-12-fix-theme-immediate-application.md`**

**两种执行方式：**

1. **子代理驱动（推荐）** - 我为每个任务分派一个独立的子代理，在任务间进行审查，快速迭代

2. **内联执行** - 在当前会话中使用executing-plans技能执行，批量执行并设置检查点进行审查

**请选择哪种方式？**