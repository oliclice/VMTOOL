# GUI 诊断日志说明

## 日志位置

已在以下关键位置添加了详细的 print 日志（所有日志都使用 `flush=True` 确保立即输出）：

### 1. CLI 启动入口 (`ui/cli/__main__.py`)
日志标签：`[CLI-GUI]`

**关键步骤：**
- `[CLI-GUI] ===== 开始启动 GUI =====` - 启动入口
- `[CLI-GUI] [1/5] 导入 PyQt6 模块...` - 导入阶段
- `[CLI-GUI] [2/5] 检查 QApplication 实例...` - 应用实例检查
- `[CLI-GUI] [3/5] 导入 VMTOOLPyQtApp...` - 导入主窗口类
- `[CLI-GUI] [4/5] 创建主窗口...` - **关键：创建窗口实例**
  - 显示窗口所有属性（title, size, centralWidget, layout, isVisible 等）
- `[CLI-GUI] [5/5] 显示窗口...` - **关键：调用 window.show()**
  - 显示调用前后的窗口状态
- `[CLI-GUI] 调用 app.exec()...` - **关键：进入事件循环**
- `[CLI-GUI] Qt 事件循环结束，退出码: X` - 事件循环退出

### 2. 主窗口初始化 (`ui/gui/pyqt_app.py`)
日志标签：`[GUI]`, `[GUI-Menu]`, `[GUI-Tabs]`, `[GUI-Theme]`

**主窗口流程：**
- `[GUI] ===== 开始初始化主窗口 =====`
- `[GUI] [1/8] 调用 super().__init__() 完成`
- `[GUI] [2/8] 设置窗口标题和大小`
- `[GUI] [3/8] 加载配置完成`
- `[GUI] [4/8] 创建中央组件完成`
- `[GUI] [5/8] 创建主布局完成`
- `[GUI] [6/8] 创建菜单栏完成`
- `[GUI] [7/8] 创建状态栏完成`
- `[GUI] [8/8] 开始初始化数据库...`
- `[GUI] ✓ 数据库初始化成功`
- `[GUI] 开始初始化服务...` - 4个服务
- `[GUI] 开始创建标签页...` - 7个标签页
- `[GUI] 开始设置主题...` - 主题应用
- `[GUI] 执行 show() 前的最后检查...` - **关键：最终状态检查**
- `[GUI] ===== 主窗口初始化完成 =====`

### 3. 菜单栏创建 (`ui/gui/pyqt_app.py`)
日志标签：`[GUI-Menu]`

**详细步骤：**
- 文件菜单（导入、导出、退出）
- 工具菜单（计算权重、检测冲突、数据迁移）
- 帮助菜单（关于）

### 4. 标签页创建 (`ui/gui/pyqt_app.py`)
日志标签：`[GUI-Tabs]`

**7个标签页：**
- 字表管理 (索引 0)
- 特殊表管理 (索引 1)
- 词表管理 (索引 2)
- 统计分析 (索引 3)
- 导入导出 (索引 4)
- 编码规则 (索引 5)
- 设置 (索引 6)

### 5. 表格标签页基类 (`ui/gui/tabs/base_table_tab.py`)
日志标签：`[BaseTableTab]`, `[BaseTableTab-UI]`

**初始化流程：**
- `[BaseTableTab] ===== 开始初始化 XXXTab =====`
- `[BaseTableTab] [1/4] 调用 super().__init__() 完成`
- `[BaseTableTab] [2/4] dict_service 设置`
- `[BaseTableTab] [3/4] 开始初始化 UI...`
- `[BaseTableTab-UI]` - 所有UI组件创建（搜索框、表格、按钮等）
- `[BaseTableTab] [4/4] UI 初始化完成，开始刷新数据...`
- `[BaseTableTab] 数据刷新完成`
- `[BaseTableTab] ===== XXXTab 初始化完成 =====`

### 6. 主题设置 (`ui/gui/pyqt_app.py`)
日志标签：`[GUI-Theme]`

**主题流程：**
- 清除硬编码样式表
- 创建调色板
- 应用到 QApplication
- 应用到所有窗口
- 应用到主窗口
- 主题管理器设置

## 使用方法

### 方法1：直接运行
```bash
python vmtool.py gui
```

### 方法2：使用详细测试脚本
```bash
python test_gui_verbose.py
```

### 方法3：输出到文件查看
```bash
python vmtool.py gui > /tmp/gui_debug.log 2>&1
cat /tmp/gui_debug.log
```

### 方法4：实时监控日志
```bash
python vmtool.py gui 2>&1 | grep --line-buffered "^\["
```

## 关键诊断点

如果 GUI 无法显示，检查日志在哪个位置停止：

1. **如果在 `[CLI-GUI] [4/5] 创建主窗口...` 后停止**
   - 问题在 `VMTOOLPyQtApp.__init__()` 中
   - 查看 `[GUI]` 系列日志，找到最后一条成功的日志

2. **如果在 `[CLI-GUI] [5/5] 显示窗口...` 后停止**
   - 问题在 `window.show()` 调用
   - 检查窗口状态日志（isVisible, isHidden 等）

3. **如果在 `[CLI-GUI] 调用 app.exec()...` 后立即退出**
   - 问题在 Qt 事件循环启动
   - 可能是 QApplication 配置问题

4. **如果所有日志都正常但窗口不可见**
   - 检查窗口位置和大小
   - 检查是否被其他窗口遮挡
   - 检查 `isVisible` 和 `isMinimized` 状态

## 常见错误模式

### 错误1：进程立即退出
```
[CLI-GUI] ===== GUI 启动完成，进入事件循环 =====
[1] terminated
```
**可能原因：** 
- `window.show()` 后被立即关闭
- Qt 事件循环启动失败
- 存在未捕获的异常

### 错误2：标签页创建失败
```
[GUI-Tabs] 创建词表管理标签页...
[BaseTableTab] ===== 开始初始化 WordsTab =====
...（无后续日志）
```
**可能原因：**
- 服务未正确初始化
- 数据库访问失败
- UI 组件创建异常

### 错误3：主题设置失败
```
[GUI-Theme] 开始设置主题...
[GUI-Theme] ✓ 清除硬编码样式表完成
...（无后续日志）
```
**可能原因：**
- 调色板创建失败
- 主题文件缺失
- 样式表语法错误

## 下一步

运行 GUI 并查看日志输出，找出最后一条成功的日志，然后根据上述诊断点定位问题。
