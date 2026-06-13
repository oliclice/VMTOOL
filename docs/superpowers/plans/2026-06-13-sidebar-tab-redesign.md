# 左侧 Tab 栏重设计 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 VMtool GUI 左侧 tab 栏从硬编码 paintEvent 手动绘制重写为 QSS 驱动、主题感知的 SidebarTabBar

**Architecture:** 新建 SidebarTabBar(QTabBar) 通过 QSS + paintEvent 分组标题实现主题感知侧边栏；pyqt_app 不再销毁重建 QTabWidget；ThemeSync 新增 tab bar 主题同步；theme_constants 新增图标和分组元数据

**Tech Stack:** PyQt6, QSS (Qt Style Sheets), Python 3.x

---

## 文件结构

```
vm-tool/
├── ui/gui/
│   ├── sidebar_tab_bar.py      # NEW - SidebarTabBar 类
│   ├── pyqt_app.py              # MODIFY - create_tab_widget, _apply_tab_position
│   ├── theme_sync.py            # MODIFY - sync_tab_bar()
│   └── styles/
│       └── linear_theme.qss     # MODIFY - 新增 QTabBar West 样式
├── app/core/
│   └── theme_constants.py       # MODIFY - TAB_ICONS, TAB_GROUPS
```

### 职责划分

| 文件 | 职责 |
|------|------|
| `sidebar_tab_bar.py` | SidebarTabBar: QSS 样式管理、分组标题 paintEvent 绘制、tabSizeHint |
| `pyqt_app.py` | 创建/替换 TabBar、位置切换、调用 ThemeSync |
| `theme_sync.py` | 根据 ThemeConfig 构建 CSS props 并注入到 tab bar |
| `linear_theme.qss` | 静态 QTabBar West 基础样式（变量占位符由 ThemeSync 动态替换） |
| `theme_constants.py` | TAB_ICONS 图标字典、TAB_GROUPS 分组定义 |

---

### Task 1: 添加 TAB_ICONS 和 TAB_GROUPS 常量

**Files:**
- Modify: `vm-tool/app/core/theme_constants.py`

- [ ] **Step 1: 在 theme_constants.py 末尾添加常量**

在文件末尾追加以下代码：

```python
# Tab 图标映射 (Unicode 字符)
TAB_ICONS: dict[str, str] = {
    "chars": "字",       # 字表管理
    "special": "◆",       # 特殊表管理
    "words": "词",        # 词表管理
    "stats": "📊",        # 统计分析
    "import_export": "⇄", # 导入导出
    "code_rules": "{}",   # 编码规则
    "settings": "⚙",     # 设置
}

# Tab 分组定义: {tab_index: group_label}
# tab_index 对应 addTab 的顺序:
#   0: chars, 1: special, 2: words, 3: stats, 4: import_export, 5: code_rules, 6: settings
TAB_GROUPS: dict[int, str] = {
    0: "数据管理",   # tabs 0-2
    3: "工具",       # tabs 3-5
}
# tab 6 (设置) 不属于任何分组，用视觉分隔线隔离
```

- [ ] **Step 2: 提交**

```bash
git add vm-tool/app/core/theme_constants.py
git commit -m "feat: 添加 TAB_ICONS 和 TAB_GROUPS 常量"
```

---

### Task 2: 新建 SidebarTabBar 类

**Files:**
- Create: `vm-tool/ui/gui/sidebar_tab_bar.py`

- [ ] **Step 1: 创建 SidebarTabBar 类文件**

```python
"""侧边栏 TabBar — QSS 驱动、主题感知、分组标题"""
from PyQt6.QtWidgets import QTabBar, QStylePainter, QStyleOptionTab, QStyle
from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QPainter, QFont, QColor, QPen

from app.core.theme_constants import TAB_GROUPS


class SidebarTabBar(QTabBar):
    """左侧垂直 TabBar
    - 通过 dynamicStylesheet 属性注入主题色 CSS 变量
    - paintEvent 中额外绘制分组标题
    - tabSizeHint 为分组第一个 tab 预留标题高度
    """

    GROUP_HEADER_HEIGHT = 22
    GROUP_HEADER_MARGIN_TOP = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setExpanding(False)
        self.setDrawBase(False)
        self._dynamic_stylesheet = ""
        self.setObjectName("sidebarTabBar")

    # ---- dynamic stylesheet property ----

    @property
    def dynamicStylesheet(self) -> str:
        return self._dynamic_stylesheet

    @dynamicStylesheet.setter
    def dynamicStylesheet(self, css: str):
        self._dynamic_stylesheet = css
        self.setStyleSheet(css)

    # ---- sizing ----

    def tabSizeHint(self, index: int) -> QSize:
        base = super().tabSizeHint(index)
        height = base.height()
        # 分组第一个 tab 预留标题高度
        if index in TAB_GROUPS:
            height += self.GROUP_HEADER_HEIGHT + self.GROUP_HEADER_MARGIN_TOP
        return QSize(base.width(), height)

    def minimumTabSizeHint(self, index: int) -> QSize:
        return self.tabSizeHint(index)

    # ---- paint ----

    def paintEvent(self, event):
        """绘制 tab + 分组标题"""
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        tab_count = self.count()
        if tab_count == 0:
            return

        # 绘制每个 tab
        for i in range(tab_count):
            self._paint_group_header(painter, i)
            self._paint_tab(painter, i)

    def _paint_group_header(self, painter: QStylePainter, index: int):
        """在分组第一个 tab 上方绘制标题"""
        if index not in TAB_GROUPS:
            return

        label = TAB_GROUPS[index]
        # 计算标题位置：当前 tab 的顶部减去标题高度
        opt = QStyleOptionTab()
        self.initStyleOption(opt, index)
        tab_rect = self.tabRect(index)

        header_rect = QRect(
            tab_rect.x() + 14,
            tab_rect.y() + self.GROUP_HEADER_MARGIN_TOP,
            tab_rect.width() - 28,
            self.GROUP_HEADER_HEIGHT,
        )

        font = QFont(self.font())
        font.setPointSizeF(font.pointSizeF() * 0.75)
        font.setBold(True)
        font.setCapitalization(QFont.CapitalizeAllUppercase)
        painter.save()
        painter.setFont(font)
        # 使用与未选中文字一致的颜色 (从 palette 的 placeholder 色近似)
        c = self.palette().color(self.palette().ColorRole.PlaceholderText)
        painter.setPen(QPen(c))
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
        painter.restore()

    def _paint_tab(self, painter: QStylePainter, index: int):
        """绘制单个 tab（利用 QStyle 标准绘制 + 手动调整 rect 抵消标题偏移）"""
        opt = QStyleOptionTab()
        self.initStyleOption(opt, index)
        tab_rect = self.tabRect(index)

        # 如果有分组标题，调整 tab 绘制区域向下偏移，标题绘制在偏移上方
        if index in TAB_GROUPS:
            offset = self.GROUP_HEADER_HEIGHT + self.GROUP_HEADER_MARGIN_TOP
            adjusted_rect = QRect(
                tab_rect.x(), tab_rect.y() + offset,
                tab_rect.width(), tab_rect.height() - offset,
            )
            opt.rect = adjusted_rect

        painter.drawControl(QStyle.ControlElement.CE_TabBarTab, opt)
```

- [ ] **Step 2: 提交**

```bash
git add vm-tool/ui/gui/sidebar_tab_bar.py
git commit -m "feat: 新建 SidebarTabBar 类 — QSS 驱动、分组标题、主题感知"
```

---

### Task 3: 重写 pyqt_app.py 中的 tab 创建逻辑

**Files:**
- Modify: `vm-tool/ui/gui/pyqt_app.py`

- [ ] **Step 1: 读取当前 create_tab_widget 和 _apply_tab_position 代码**

确认改动前后的行范围。基于之前读取的内容 (303-434 行)。

- [ ] **Step 2: 替换 create_tab_widget 方法**

将第 303-340 行的 `create_tab_widget` 替换为：

```python
def create_tab_widget(self):
    """创建标签页"""
    from PyQt6.QtWidgets import QTabBar
    from .sidebar_tab_bar import SidebarTabBar
    from app.core.theme_constants import TAB_ICONS

    self.tab_widget = QTabWidget()
    self.main_layout.addWidget(self.tab_widget, 1)

    # 应用 tab 栏位置配置
    tab_position = config_manager.get("tab_position", "top")
    self._apply_tab_position(tab_position)

    tabs = [
        (CharsTab(parent=self, dict_service=self.dict_service), TAB_ICONS["chars"] + " 字表管理"),
        (SpecialTab(parent=self, dict_service=self.dict_service), TAB_ICONS["special"] + " 特殊表管理"),
        (WordsTab(parent=self, dict_service=self.dict_service), TAB_ICONS["words"] + " 词表管理"),
        (StatsTab(parent=self, stats_service=self.stats_service), TAB_ICONS["stats"] + " 统计分析"),
        (ImportExportTab(parent=self, filter_service=self.filter_service, dict_service=self.dict_service), TAB_ICONS["import_export"] + " 导入导出"),
        (CodeRulesTab(parent=self, dict_service=self.dict_service), TAB_ICONS["code_rules"] + " 编码规则"),
    ]

    self.chars_tab = tabs[0][0]
    self.special_tab = tabs[1][0]
    self.words_tab = tabs[2][0]
    self.stats_tab = tabs[3][0]
    self.import_export_tab = tabs[4][0]
    self.code_rules_tab = tabs[5][0]

    for widget, label in tabs:
        self.tab_widget.addTab(widget, label)

    # 设置标签页（底部固定，通过 SidebarTabBar 分隔线呈现）
    settings_tab = QWidget()
    self.tab_widget.addTab(settings_tab, TAB_ICONS["settings"] + " 设置")
    self.create_settings_tab(settings_tab)

    # 存储 sidebar tab bar 引用
    self._sidebar_tab_bar = None

    # 连接设置变更信号
    self._connect_settings_signals()

    # 初始主题同步
    self._sync_tab_theme()
```

- [ ] **Step 3: 替换 _apply_tab_position 方法**

将第 350-434 行（整个 `_apply_tab_position` 方法）替换为：

```python
def _apply_tab_position(self, position: str):
    """应用 tab 栏位置 — 仅替换 TabBar + setTabPosition，不销毁 QTabWidget"""
    from PyQt6.QtWidgets import QTabBar
    from .sidebar_tab_bar import SidebarTabBar

    if position == "left":
        sidebar = SidebarTabBar()
        self.tab_widget.setTabBar(sidebar)
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.West)
        self._sidebar_tab_bar = sidebar
    else:
        default_bar = QTabBar()
        self.tab_widget.setTabBar(default_bar)
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self._sidebar_tab_bar = None

    # 重新同步主题样式（TabBar 实例已变更）
    self._sync_tab_theme()
```

- [ ] **Step 4: 新增 _sync_tab_theme 方法**

在 `_apply_tab_position` 之后添加：

```python
def _sync_tab_theme(self):
    """同步 tab 栏主题样式"""
    if self._sidebar_tab_bar is None:
        return
    from .theme_sync import theme_sync
    theme_sync.sync_tab_bar(self._sidebar_tab_bar)
```

- [ ] **Step 5: 更新 _on_settings_changed 方法**

确认第 446-449 行的 `_on_settings_changed` 中 `tab_position` 处理正确（当前已调用 `_apply_tab_position`，无需改动）。

- [ ] **Step 6: 注册 tab_widget 到 ThemeSync**

确保 tab_widget 的主题更新能触发 tab bar 的重新同步。修改 `_connect_settings_signals` 后的逻辑——在 `theme_manager` 的 `register_widget` 中添加回调：

```python
# 在 __init__ 末尾或 create_tab_widget 末尾
theme_manager.register_widget(self.tab_widget, callback=self._on_tab_theme_changed)
```

添加回调方法：

```python
def _on_tab_theme_changed(self, mode, name, color):
    """主题变更时重新同步 tab bar 样式"""
    self._sync_tab_theme()
```

- [ ] **Step 7: 提交**

```bash
git add vm-tool/ui/gui/pyqt_app.py
git commit -m "refactor: 重写 tab 栏创建/切换逻辑 — SidebarTabBar + 非销毁式位置切换"
```

---

### Task 4: ThemeSync 新增 sync_tab_bar 方法

**Files:**
- Modify: `vm-tool/ui/gui/theme_sync.py`

- [ ] **Step 1: 在 ThemeSync 类中添加 sync_tab_bar 方法**

在 `_on_theme_changed` 方法后添加：

```python
def sync_tab_bar(self, tab_bar) -> None:
    """为 SidebarTabBar 构建并注入主题 QSS

    Args:
        tab_bar: SidebarTabBar 实例
    """
    from app.core.theme_config import ThemeConfig
    from app.core.theme_constants import THEME_MODE_DARK
    from .theme_manager import theme_manager

    mode, name, color = theme_manager.get_current_theme()
    palette = ThemeConfig.get_palette(name, mode, color)
    is_dark = (mode == THEME_MODE_DARK)

    # 将 hex 强调色转为 RGB 三元组用于 QSS rgba()
    hex_accent = palette.accent.lstrip("#")
    r, g, b = int(hex_accent[0:2], 16), int(hex_accent[2:4], 16), int(hex_accent[4:6], 16)

    if is_dark:
        css = f"""
            QTabBar#sidebarTabBar {{
                background: #13141f;
                border-right: 1px solid #222236;
                min-width: 148px;
            }}
            QTabBar#sidebarTabBar::tab {{
                padding: 9px 14px;
                text-align: left;
                border-left: 3px solid transparent;
                color: rgba(255,255,255,0.45);
                background: transparent;
            }}
            QTabBar#sidebarTabBar::tab:selected {{
                background: rgba({r},{g},{b},0.15);
                color: #b8c2ff;
                border-left: 3px solid {palette.accent};
                font-weight: 600;
            }}
            QTabBar#sidebarTabBar::tab:hover:!selected {{
                background: rgba(255,255,255,0.05);
            }}
        """
    else:
        css = f"""
            QTabBar#sidebarTabBar {{
                background: #f8f9fb;
                border-right: 1px solid #e8ecf1;
                min-width: 148px;
            }}
            QTabBar#sidebarTabBar::tab {{
                padding: 9px 14px;
                text-align: left;
                border-left: 3px solid transparent;
                color: #64748b;
                background: transparent;
            }}
            QTabBar#sidebarTabBar::tab:selected {{
                background: rgba({r},{g},{b},0.10);
                color: {palette.accent};
                border-left: 3px solid {palette.accent};
                font-weight: 600;
            }}
            QTabBar#sidebarTabBar::tab:hover:!selected {{
                background: rgba(0,0,0,0.04);
            }}
        """

    tab_bar.dynamicStylesheet = css
```

- [ ] **Step 2: 提交**

```bash
git add vm-tool/ui/gui/theme_sync.py
git commit -m "feat: ThemeSync 新增 sync_tab_bar — 动态注入侧边栏 QSS"
```

---

### Task 5: 清理废弃代码并验证

**Files:**
- Modify: `vm-tool/ui/gui/pyqt_app.py`

- [ ] **Step 1: 移除 HorizontalTabBar 相关导入残留**

确认 `pyqt_app.py` 的 `_apply_tab_position` 方法中不再有 `HorizontalTabBar` 内联类、`QPainter`、`QPen`、`QRect` 等只在旧 `paintEvent` 中使用的导入。新代码不再需要这些。

检查 `create_tab_widget` 顶部多余的 `from PyQt6.QtWidgets import QTabWidget as QTabWidgetClass` 等历史遗留导入。

- [ ] **Step 2: 运行应用验证**

```bash
cd vm-tool && python -c "
from PyQt6.QtWidgets import QApplication
app = QApplication([])
from ui.gui.sidebar_tab_bar import SidebarTabBar
bar = SidebarTabBar()
bar.addTab('test1')
bar.addTab('test2')
print('SidebarTabBar OK:', bar.count(), 'tabs')
"
```

- [ ] **Step 3: 提交**

```bash
git add vm-tool/ui/gui/pyqt_app.py
git commit -m "chore: 清理 HorizontalTabBar 废弃代码和多余导入"
```

---

### Task 6: 更新 linear_theme.qss 添加 Top 模式回退样式

**Files:**
- Modify: `vm-tool/ui/gui/styles/linear_theme.qss`

- [ ] **Step 1: 在文件末尾添加顶部 TabBar 样式（保留顶栏支持时使用）**

```css
/* === Top TabBar (fallback for non-sidebar mode) === */
QTabBar[position="north"] {
    background: transparent;
    border: none;
}

QTabBar[position="north"]::tab {
    padding: 8px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    color: @secondary-text;
    margin-right: 4px;
}

QTabBar[position="north"]::tab:selected {
    color: @accent;
    border-bottom: 2px solid @accent;
    font-weight: 600;
}

QTabBar[position="north"]::tab:hover:!selected {
    color: @primary-text;
    background: rgba(128,128,128,0.08);
    border-radius: 4px;
}
```

- [ ] **Step 2: 提交**

```bash
git add vm-tool/ui/gui/styles/linear_theme.qss
git commit -m "feat: linear_theme.qss 新增顶部 TabBar 样式回退"
```
