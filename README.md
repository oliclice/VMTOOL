# VM-TOOL 码表处理工具

中文输入法码表管理工具，支持 CLI 和 GUI 界面，提供高效的码表增删改查、权重计算、过滤去重、导入导出等功能。

## 功能特性

### 核心功能
- **码表管理**：词条/字/特殊符号的增删改查，支持批量操作
- **权重计算**：基于词频数据，使用 log₁₀(词频) 自动计算权重
- **过滤去重**：批量过滤不需要的词条，智能去重
- **编码生成**：基于自定义编码规则自动生成编码（模板语法 + Python 模式，Python 模式在 AST 白名单沙箱中执行）
- **导入导出**：支持 TXT/CSV/JSON 格式导入导出，支持分表导出
- **统计功能**：高频编码统计、词条分布分析
- **自动导出**：支持自动导出到 ibus/rime 和 fcitx5/rime 目录

引用了
- [清华大学开放中文词库](https://github.com/thunlp/THUOCL)（韩世依, 张钰晖, 马云山, 涂存超, 郭志芃, 刘知远, 孙茂松. THUOCL：清华大学开放中文词库. 2016.）
- [chinese-frequency-word-list](https://github.com/liangqi/chinese-frequency-word-list) 

### 数据库支持
- SQLite + SQLAlchemy ORM
- 连接层使用 `NullPool` 并开启 WAL（`journal_mode=WAL`）+ `busy_timeout`，支持多线程并发写
- 会话所有权显式化：`get_db()` 返回新 Session，由调用方负责 `close()`
- 迁移：内置脚本 `app/dal/migration.py`（**不再依赖 Alembic**）
- 词条模型：word、code、weight、is_active、is_character、is_special、manual

## 界面

| 界面 | 说明 |
|------|------|
| **CLI** | Typer 构建，支持命令模式和交互式模式，带自动补全 |
| **GUI (PyQt6)** | 多标签页桌面应用，含词/字/特殊/统计/导入导出/设置/编码规则等功能页 |

## 快速开始

### 安装（推荐：一条命令）

```bash
cd vm-tool
python3 vmtool.py --install
```

它会自动完成三件事：

1. 在项目目录下创建 `.venv`（已存在则复用）；
2. 用**该 venv 的解释器**安装项目与依赖——只有这样 `pyproject.toml` 里
   PyQt6/Qt6 的版本上界才会真正生效；
3. 在 `~/.local/bin/vmtool` 写入启动器，其解释器**固定指向该 venv**。

完成后，**任何终端、任何目录**直接使用：

```bash
vmtool --help
vmtool gui
```

不需要 `activate`，也不需要关心当前用的是哪个 python。

> **为什么必须这样**：PyQt6 与 Qt 运行库必须同属 6.6.x，而系统 `python3` 会加载
> `~/.local` 或系统级里的其他版本 PyQt6，并与系统 Qt 混用而崩溃
> （`ImportError: ... version Qt_6_PRIVATE_API not found`）。
> 启动器把解释器钉在 venv 上，从根上避免这类问题；
> 详见「开发 → PyQt6/Qt6 版本约束」。

### 手工安装（等价做法，适合开发调试）

```bash
cd vm-tool
python3 -m venv .venv
.venv/bin/python -m pip install -e .
# 之后需自行使用 .venv/bin/vmtool，或 .venv/bin/python -m ui.cli
```

### CLI 使用

```bash
# 交互式模式
.venv/bin/python -m ui.cli

# 直接命令（子命令共 12 个，可用 --help 查看）
.venv/bin/python -m ui.cli add --word 测试 --code ceshi --weight 100
.venv/bin/python -m ui.cli query --keyword 测试
.venv/bin/python -m ui.cli delete --word 测试
.venv/bin/python -m ui.cli delete-batch word1 word2 word3
.venv/bin/python -m ui.cli set-weight 测试 100
.venv/bin/python -m ui.cli replace-code 测试 newcode
.venv/bin/python -m ui.cli calculate-all-codes --rule first_letter
.venv/bin/python -m ui.cli calculate-weight
.venv/bin/python -m ui.cli import --file path/to/file.txt
.venv/bin/python -m ui.cli export --format csv --path output.csv
.venv/bin/python -m ui.cli stats
```

安装后也可以直接用入口脚本（等价于上面的 `-m ui.cli`）：

```bash
.venv/bin/vmtool stats
.venv/bin/vmtool --help
```

### GUI 使用

```bash
cd vm-tool
.venv/bin/python -m ui.cli gui
```

> `ui/gui/pyqt_app.py` **没有 `__main__` 入口**，不能通过 `python pyqt_app.py` 启动，
> 请统一走 `ui.cli` 的 `gui` 子命令。同样必须使用项目 venv 的解释器。

## 项目结构

```
VMtool/
├── vm-tool/                    # 主项目目录
│   ├── app/                    # 核心应用代码
│   │   ├── core/               # 核心模块
│   │   │   ├── config.py       # 配置管理（Pydantic Settings）
│   │   │   ├── config_manager.py # 运行时配置管理器（~/.config/vm-tool/config.json）
│   │   │   ├── cache.py        # 缓存系统（写路径显式失效，ttl 60s 兜底）
│   │   │   ├── errors.py       # 错误定义
│   │   │   ├── logging_config.py # 日志配置
│   │   │   ├── run_mode.py     # 运行模式管理
│   │   │   ├── compatibility.py # 兼容性层（持有会话，已提供 close()）
│   │   │   ├── theme_config.py # 主题配置
│   │   │   └── theme_constants.py # 主题常量
│   │   ├── dal/                # 数据访问层
│   │   │   ├── database.py     # 连接与会话工厂（NullPool + WAL）
│   │   │   ├── models.py       # 数据模型
│   │   │   ├── repositories.py # 数据仓库
│   │   │   ├── init_db.py      # 数据库初始化
│   │   │   └── migration.py    # 数据迁移（不依赖 app.core）
│   │   ├── services/           # 业务逻辑层
│   │   │   ├── dict.py         # 词条服务
│   │   │   ├── weight.py       # 权重计算
│   │   │   ├── filter.py       # 过滤/导入导出服务
│   │   │   ├── stats.py        # 统计服务
│   │   │   ├── code_generator.py # 编码生成器（Python 模式含 AST 沙箱）
│   │   │   └── thuocl.py       # 词频数据加载
│   │   └── plugins/            # 插件系统
│   │       ├── base.py         # 插件基类
│   │       └── manager.py      # 插件管理器
│   ├── ui/                     # 用户界面
│   │   ├── cli/                # 命令行界面
│   │   │   └── __main__.py     # CLI 入口（Typer app）
│   │   └── gui/                # 图形界面
│   │       ├── pyqt_app.py     # PyQt6 主应用（无 __main__，经 ui.cli gui 启动）
│   │       ├── tabs/           # 功能标签页
│   │       │   ├── words_tab.py          # 词表标签页
│   │       │   ├── chars_tab.py          # 字表标签页
│   │       │   ├── special_tab.py        # 特殊字符标签页
│   │       │   ├── stats_tab.py          # 统计标签页
│   │       │   ├── import_export_tab.py  # 导入导出标签页
│   │       │   ├── general_table_tab.py  # 通用表格标签页
│   │       │   ├── refreshable_tab.py    # 可刷新标签页基类
│   │       │   └── base_table_tab.py     # 基础表格标签页
│   │       ├── settings/       # 设置页面
│   │       │   ├── appearance_panel.py     # 外观设置
│   │       │   ├── cache_panel.py          # 缓存设置
│   │       │   ├── code_rules_panel.py     # 编码规则设置
│   │       │   ├── data_panel.py           # 数据设置
│   │       │   ├── danger_zone_panel.py    # 危险操作
│   │       │   ├── export_panel.py         # 导出设置
│   │       │   ├── stats_panel.py          # 统计设置
│   │       │   └── base_panel.py           # 设置面板基类
│   │       ├── threads/        # 后台线程（每个线程在 run() 内自建服务并释放）
│   │       │   ├── service_factory.py      # 线程私有服务 scope 工厂
│   │       │   ├── import_thread.py        # 导入线程
│   │       │   ├── add_batch_thread.py     # 批量添加线程
│   │       │   ├── calculate_thread.py     # 计算编码线程
│   │       │   ├── calculate_weight_thread.py # 计算权重线程
│   │       │   ├── auto_dedupe_thread.py   # 自动去重线程
│   │       │   ├── delete_table_thread.py  # 删表线程
│   │       │   └── refresh_data_thread.py  # 刷新数据线程
│   │       ├── widgets/        # 自定义控件（仪表盘、图表、统计卡片、侧边栏等）
│   │       ├── styles/         # 样式与主题变量
│   │       ├── theme_manager.py # 主题管理器
│   │       ├── theme_utils.py  # 主题工具
│   │       ├── progress_bar.py # 进度条组件
│   │       ├── settings_tab.py # 设置标签页
│   │       └── code_rules_tab.py # 编码规则标签页
│   ├── plugins/                # 插件目录
│   │   └── example_plugin.py   # 示例插件
│   ├── scripts/                # 脚本目录
│   │   └── build.py            # 构建脚本（PyInstaller）
│   ├── tests/                  # 测试目录
│   │   └── unit/               # 单元测试（conftest.py 提供全局隔离装置）
│   │       ├── conftest.py                       # 自动隔离真实数据库与全局缓存
│   │       ├── test_dict_service.py
│   │       ├── test_code_generator.py            # 含沙箱逃逸载荷
│   │       ├── test_cache_invalidation.py
│   │       ├── test_concurrent_writes.py
│   │       ├── test_dependency_declarations.py   # 依赖声明一致性门禁
│   │       ├── test_filter_import_concurrency.py
│   │       ├── test_gui_thread_conventions.py    # 线程约定 AST 门禁
│   │       ├── test_isolation_guard.py
│   │       ├── test_session_ownership.py
│   │       └── test_thread_service_ownership.py
│   ├── vmtool.py               # 安装器（--install 建 venv + 写全局启动器）与命令行入口
│   ├── pyproject.toml          # 项目配置
│   ├── requirements.txt        # 依赖列表
│   ├── data/                   # 词频数据（THUOCL）
│   └── vm_tool.db              # SQLite 数据库文件（示例）
├── .github/workflows/ci.yml    # CI：ruff / mypy / pytest
├── .pre-commit-config.yaml     # pre-commit 钩子
├── ARCHITECTURE_REVIEW.md      # 架构评审（过程文档，可不入库）
├── EXECUTION_REPORT.md         # 修复执行报告（过程文档，可不入库）
├── AGENTS.md                   # AI 代理指南
└── 项目规范                   # 开发规范
```

## 编码规则

自定义编码规则语法：

```
v[n] = 表达式      # 词长度为 n 的编码规则
s[i][j]            # 第 i+1 个字的第 j 个编码字符（0 索引）
s[-1][j]           # 最后一个字的第 j 个编码字符
+                  # 字符串连接
```

示例：

```
v[2] = s[0][1] + s[0][2] + s[1][1] + s[1][2]  # 取前两字的前两码
v[3] = s[0][1] + s[1][1] + s[2][1]              # 取前三字的第一码
```

支持自定义 Python 函数编码规则，详情参考 GUI 界面。

> **安全说明**：Python 模式的自定义规则在 AST 白名单沙箱中执行——
> 禁用 `import`、禁止访问下划线/双下划线属性（含**属性读取**）、
> 禁止把属性绑定到名字后再调用；`str.format` / `format_map` / `translate` / `maketrans`
> 连读取都被拒绝（因为它们的迷你语言会在 C 层做属性访问，绕过 AST 校验）。
> 白名单外的一律抛 `CustomRuleSecurityError`，不再静默降级。

## 技术栈

- **Python** >= 3.10（开发/CI 使用 3.10，本机开发环境为 3.14）
- **CLI**: Typer + Rich
- **GUI**: PyQt6（Qt 运行库需与绑定同属 6.6.x）
- **数据库**: SQLite + SQLAlchemy ORM（NullPool + WAL）
- **配置**: Pydantic + Pydantic Settings
- **迁移**: 内置脚本 `app/dal/migration.py`
- **构建**: PyInstaller
- **测试**: pytest + pytest-cov
- **代码质量**: ruff（lint + format）、mypy

## 开发

### 环境准备

```bash
cd vm-tool

# 创建虚拟环境
python3 -m venv .venv
.venv/bin/python -m pip install -U pip

# 安装运行时 + 测试 + 代码质量依赖
.venv/bin/python -m pip install -e ".[test,quality]"
```

### 测试

```bash
cd vm-tool

# 全量测试（当前基线：107 passed / 0 failed）
.venv/bin/python -m pytest -q

# 带覆盖率（当前 TOTAL 约 19%）
.venv/bin/python -m pytest --cov=app

# 单个测试文件
.venv/bin/python -m pytest -q tests/unit/test_code_generator.py
```

> `tests/unit/conftest.py` 会自动隔离真实数据库与全局缓存：
> **任何用例若不把 DAL 重定向到临时库就直接连库，会立刻抛 `AssertionError`。**
> 需要真实会话请沿用 `temp_db` 夹具模式（monkeypatch 路径/引擎/会话工厂到 `tmp_path`）。

### 代码检查与格式化

```bash
cd vm-tool

# lint（当前应为零输出、exit 0）
.venv/bin/python -m ruff check .

# 格式检查（当前应为 N files already formatted）
.venv/bin/python -m ruff format --check .

# 类型检查（当前基线 119 个错误；CI 中暂为 continue-on-error）
.venv/bin/python -m mypy app/
```

### 提交前门禁

```bash
cd vm-tool
.venv/bin/python -m pip install pre-commit   # 注意：未声明在 extras 中，需手动安装
pre-commit install
pre-commit run --all-files
```

CI 配置见 `.github/workflows/ci.yml`（`push` / `pull_request` 触发）：

| 步骤 | 是否阻断 |
|------|----------|
| `python -m ruff check .` | **硬失败** |
| `python -m pytest --cov=app` | **硬失败** |
| `python -m mypy app/` | 暂为 `continue-on-error`（基线较大，待阶段 3 收紧） |

仓库内还有两条纯 Python 实现的“门禁测试”，随 pytest 一起生效：

- `tests/unit/test_dependency_declarations.py`：核对 `pyproject.toml` 声明的依赖集合与代码实际 import 的第三方包集合（**无豁免名单**，传递依赖不算）
- `tests/unit/test_gui_thread_conventions.py`：用 AST 检查 GUI 线程类不得接收/保存服务实例、必须在 `run()` 内用 scope 工厂自建服务、且 `self.<name>.emit` 的信号必须已声明

### 构建可执行文件

```bash
cd vm-tool

# PyInstaller 未声明在 extras 中，需手动安装
.venv/bin/python -m pip install pyinstaller

# 构建（产物输出到 dist/linux/）
.venv/bin/python scripts/build.py --linux

# 其他平台参数：--windows / --macos / --all
```

构建脚本会调用 PyInstaller；仓库内的 spec 文件可作参考/手动使用：

- `vm-tool/vmtool.spec`：CLI 版本
- `vm-tool/vmtool-gui.spec`：GUI 版本

### PyQt6/Qt6 版本约束（重要）

`PyQt6` 自身的元数据只声明 `PyQt6-Qt6>=6.6.0`（**没有上界**），因此裸安装可能解析到 6.11.x，
而 PyQt6 的 abi3 扩展是按 Qt 6.6 编译的，绑定与运行库版本不一致会直接报：

```
ImportError: .../PyQt6/QtGui.abi3.so: undefined symbol: ... version Qt_6
ImportError: /lib64/libQt6Widgets.so.6: version `Qt_6_PRIVATE_API' not found
```

所以 `pyproject.toml` 与 `requirements.txt` 里显式钉住了上界（`PyQt6>=6.6.1,<6.7`、
`PyQt6-Qt6>=6.6.0,<6.7`、`PyQt6-Charts`、`PyQt6-Charts-Qt6` 同理）——**请勿放宽**。

**另外注意本机可能有第二份 PyQt6**：如果 `~/.local/lib/python3.*/site-packages/`
下存在另一版本的 PyQt6，用系统 `python3` 启动 GUI 时会被优先加载，并与系统 Qt 混用而崩溃。
项目 venv 的 `pyvenv.cfg` 里 `include-system-site-packages = false`，不受此影响——
**这也是为什么必须用 `.venv/bin/python` 启动。**

## 配置

### 配置文件位置

- 运行时配置：`~/.config/vm-tool/config.json`
- 数据库默认路径：`~/.config/vm-tool/vm_tool.db`（可用环境变量 `VMTOOL_DATABASE_PATH` 覆盖）

### 主题设置
- 支持深色/浅色/自动主题模式
- 多种主题颜色：蓝色、绿色、红色、紫色、橙色

### 导出设置
- 默认导出路径和格式
- 分表导出支持
- 自动导出到 ibus/rime 和 fcitx5/rime 目录

### 缓存设置
- 可配置缓存大小和过期时间
- 写路径会显式失效缓存，ttl 仅作兜底

## 许可证

MIT
