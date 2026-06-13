# 左侧 Tab 栏重设计

**日期**: 2026-06-13 | **状态**: 已确认

## 一、背景与问题

当前 VMtool GUI 左侧 tab 栏存在严重的设计和技术问题：

| 问题 | 描述 |
|------|------|
| 硬编码颜色 | `paintEvent` 中使用 `QColor(240,240,240)` 绘制背景，深色主题下刺眼 |
| 无图标 | 纯文字 tab，识别效率低 |
| 交互缺失 | 无 hover 效果，无视觉反馈 |
| 硬编码选中色 | `#3b82f6` 蓝色，不跟随用户选择的主题色 |
| 销毁重建 | 切换 top/left 时销毁整个 QTabWidget 重建，效率差且可能导致状态丢失 |
| 手动绘制 | `HorizontalTabBar.paintEvent` 完全手绘，绕过了 QSS 样式系统 |

## 二、设计目标

1. **主题感知**：侧边栏自动跟随明暗主题，选中态使用用户选择的主题色
2. **分组结构**：7 个 tab 分为 "数据管理" + "工具" 两个分组，设置固定在底部
3. **保留位置切换**：用户可在设置中切换顶部/左侧，但修复销毁重建问题
4. **现代视觉**：左侧选中指示条、hover 微交互、Unicode 图标
5. **QSS 驱动**：废弃 paintEvent 手动绘制，使用 QSS 样式表

## 三、视觉设计

### 3.1 布局结构

```
┌──────────────────────────┐
│ 数据管理 (分组标题)       │
│ ┃ Aa 字表管理  ← 选中态  │  ← 左侧 3px 主题色竖线
│   ◆  特殊表管理          │
│   ⬡ 词表管理             │
│                          │
│ 工具 (分组标题)           │
│   📊 统计分析            │
│   ⇄  导入导出            │
│   { } 编码规则           │
│ ─────────────────────── │  ← 分隔线
│   ⚙  设置               │  ← 固定在底部
└──────────────────────────┘
```

### 3.2 浅色主题颜色映射

| 元素 | 颜色 |
|------|------|
| 侧边栏背景 | `#f8f9fb`（浅灰） |
| 分组标题 | `#94a3b8`（slate-400） |
| 非选中文字 | `#64748b`（slate-500） |
| 选中背景 | `rgba(accent, 0.1)`（主题色 10% 透明） |
| 选中文字 | 主题色 |
| 选中指示条 | 主题色 3px 竖线 |
| 分隔线 | `#e8ecf1` |
| Hover 背景 | `rgba(0,0,0,0.04)` |

### 3.3 深色主题颜色映射

| 元素 | 颜色 |
|------|------|
| 侧边栏背景 | `#13141f`（深蓝黑） |
| 分组标题 | `#5c5c8a`（暗紫灰） |
| 非选中文字 | `rgba(255,255,255,0.45)` |
| 选中背景 | `rgba(accent, 0.15)` |
| 选中文字 | 主题色亮化版 |
| 选中指示条 | 主题色 3px 竖线 |
| 分隔线 | `#222236` |
| Hover 背景 | `rgba(255,255,255,0.05)` |

### 3.4 Tab 图标

使用 Unicode 字符（无需额外资源文件）：

| Tab | 图标 | Unicode |
|-----|------|---------|
| 字表管理 | Aa | - |
| 特殊表管理 | ◆ | U+25C6 |
| 词表管理 | ⬡ | U+2B21 |
| 统计分析 | 📊 | U+1F4CA |
| 导入导出 | ⇄ | U+21C4 |
| 编码规则 | { } | - |
| 设置 | ⚙ | U+2699 |

## 四、技术方案

### 4.1 架构变更

**废弃**：`HorizontalTabBar(QTabBar)` 的 `paintEvent` 手动绘制

**新建**：`SidebarTabBar(QTabBar)` — 通过 QSS 样式表驱动，继承 QTabBar，仅覆盖必要方法（`tabSizeHint` 控制宽度），样式完全由 QSS 控制。

### 4.2 核心改动文件

| 文件 | 改动 |
|------|------|
| `ui/gui/pyqt_app.py` | 重写 `create_tab_widget()` 和 `_apply_tab_position()`，使用 SidebarTabBar |
| `ui/gui/styles/linear_theme.qss` | 新增 `QTabBar[position="west"]` 样式规则 |
| `ui/gui/theme_sync.py` | 新增 `sync_tab_bar()` 方法，动态注入主题色到 tab bar |
| `app/core/theme_constants.py` | 新增 tab 图标映射常量 |

### 4.3 `_apply_tab_position` 修复

**当前问题**：销毁 QTabWidget 重建

**修复方案**：
```
def _apply_tab_position(self, position: str):
    if position == "left":
        sidebar = SidebarTabBar()
        self.tab_widget.setTabBar(sidebar)
        self.tab_widget.setTabPosition(QTabWidget.West)
    else:
        self.tab_widget.setTabBar(QTabBar())  # 恢复默认
        self.tab_widget.setTabPosition(QTabWidget.North)
    # 重新应用样式
    self._sync_tab_theme()
```

不再销毁 QTabWidget，仅替换 TabBar 实例和调用 `setTabPosition()`。

### 4.4 QSS 样式结构

```css
/* 左侧 tab 栏整体 */
QTabBar[position="west"] {
    background: var(--sidebar-bg);
    border-right: 1px solid var(--sidebar-border);
    min-width: 140px;
}

/* 单个 tab */
QTabBar[position="west"]::tab {
    padding: 9px 14px;
    text-align: left;
    border-left: 3px solid transparent;
    color: var(--sidebar-text);
    font-weight: normal;
}

/* 选中 tab */
QTabBar[position="west"]::tab:selected {
    background: var(--sidebar-selected-bg);
    color: var(--accent);
    border-left: 3px solid var(--accent);
    font-weight: 600;
}

/* hover tab */
QTabBar[position="west"]::tab:hover:!selected {
    background: var(--sidebar-hover-bg);
}
```

CSS 变量由 ThemeSync 在主题切换时动态注入。

### 4.5 主题同步

ThemeSync 新增 `sync_tab_bar()` 方法：
- 接收当前 ThemeConfig
- 构建 CSS 变量（`--sidebar-bg`, `--sidebar-text`, `--accent` 等）
- 通过 `tab_widget.setStyleSheet()` 注入

## 五、分组标题实现

QTabBar 原生不支持分组标题。采用 **paintEvent 内联绘制**：

在 `SidebarTabBar.paintEvent` 中，根据 `tabData()` 判断每个 tab 的分组归属。当绘制到分组第一个 tab 时，在其上方预留 22px 空间绘制分组标题文字。

```
Group labels defined in TAB_GROUPS:
{
    0: "数据管理",   # tabs 0-2
    3: "工具",       # tabs 3-5
}
# tab 6 (设置) is ungrouped, separated by a visual divider
```

`tabSizeHint` 对分组第一个 tab 额外增加 22px 高度以容纳标题。

这是最小侵入的方案——不改动 QTabWidget 布局结构，所有逻辑封装在 `SidebarTabBar` 内部。

## 六、文件变更清单

1. **新建** `ui/gui/sidebar_tab_bar.py` — SidebarTabBar 类
2. **修改** `ui/gui/pyqt_app.py` — `create_tab_widget()`、`_apply_tab_position()`、新增 `_sync_tab_theme()`
3. **修改** `ui/gui/theme_sync.py` — 新增 `sync_tab_bar()` 方法
4. **修改** `ui/gui/styles/linear_theme.qss` — 新增 QTabBar West 样式
5. **修改** `app/core/theme_constants.py` — 新增 `TAB_ICONS`、`TAB_GROUPS` 常量
6. **修改** `ui/gui/settings/appearance_panel.py` — 无逻辑变化（保留现有切换控件）

## 七、测试要点

- 浅色/深色主题切换后侧边栏颜色正确
- 6 种主题色切换后选中指示条颜色正确
- 顶部/左侧位置切换流畅，当前选中 tab 保持
- Hover 效果正常（非选中项有背景变化）
- 设置 tab 始终在底部
- 窗口缩放时 tab 栏宽度不变，内容区自适应

## 八、已知约束

- 分组标题无法通过纯 QSS 实现，需在 paintEvent 中额外绘制或使用布局包装
- Unicode 图标在不同平台上渲染效果可能不一致
- QTabWidget 的 West 模式下 tab 文字默认水平排列，Qt6 原生支持
