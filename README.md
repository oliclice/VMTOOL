# VM-TOOL 码表处理工具

中文输入法码表管理工具，支持 CLI 和 GUI 界面，提供高效的码表增删改查、权重计算、过滤去重、导入导出等功能。

## 功能特性

### 核心功能
- **码表管理**：词条/字/特殊符号的增删改查，支持批量操作
- **权重计算**：基于 THUOCL 词频数据，使用 log₁₀(词频) 自动计算权重
- **过滤去重**：批量过滤不需要的词条，智能去重
- **编码生成**：基于自定义编码规则自动生成编码
- **导入导出**：支持 TXT/CSV/JSON 格式导入导出，支持分表导出
- **统计功能**：高频编码统计、词条分布分析
- **自动导出**：支持自动导出到 ibus/rime 和 fcitx5/rime 目录

引用了[清华大学开放中文词库](https://github.com/thunlp/THUOCL)
韩世依, 张钰晖, 马云山, 涂存超, 郭志芃, 刘知远, 孙茂松. THUOCL：清华大学开放中文词库. 2016.

### 数据库支持
- SQLite + SQLAlchemy ORM
- 支持数据库迁移（Alembic）
- 词条模型：word、code、weight、is_active、is_character、is_special、manual

## 界面

| 界面 | 说明 |
|------|------|
| **CLI** | Typer 构建，支持命令模式和交互式模式，带自动补全 |
| **GUI (PyQt6)** | 多标签页桌面应用，含词/字/特殊/统计/导入导出/设置/编码规则等功能页 |

## 快速开始

### 安装

```bash
cd vm-tool
pip install -e .
```

### CLI 使用

```bash
# 交互式模式
vmtool

# 直接命令
vmtool add --word 测试 --code ceshi --weight 100
vmtool query --keyword 测试
vmtool delete --word 测试
vmtool delete-batch word1 word2 word3
vmtool set-weight 测试 100
vmtool replace-code 测试 newcode
vmtool calculate-all-codes --rule first_letter
vmtool calculate-weight
vmtool import --file path/to/file.txt
vmtool export --format csv --path output.csv
vmtool stats
vmtool gui
```

### GUI 使用

```bash
# 通过CLI启动
vmtool gui

# 直接启动
python vm-tool/ui/gui/pyqt_app.py
```

## 项目结构

```
VMtool/
├── vm-tool/                    # 主项目目录
│   ├── app/                    # 核心应用代码
│   │   ├── core/               # 核心模块
│   │   │   ├── config.py       # 配置管理
│   │   │   ├── config_manager.py # 配置管理器
│   │   │   ├── cache.py        # 缓存系统
│   │   │   ├── errors.py       # 错误定义
│   │   │   ├── logging_config.py # 日志配置
│   │   │   ├── run_mode.py     # 运行模式管理
│   │   │   ├── service_registry.py # 服务注册
│   │   │   ├── compatibility.py # 兼容性层
│   │   │   └── theme_constants.py # 主题常量
│   │   ├── dal/                # 数据访问层
│   │   │   ├── database.py     # 数据库连接
│   │   │   ├── models.py       # 数据模型
│   │   │   ├── repositories.py # 数据仓库
│   │   │   ├── init_db.py      # 数据库初始化
│   │   │   └── migration.py    # 数据库迁移
│   │   ├── services/           # 业务逻辑层
│   │   │   ├── dict.py         # 词条服务
│   │   │   ├── weight.py       # 权重计算
│   │   │   ├── filter.py       # 过滤服务
│   │   │   ├── stats.py        # 统计服务
│   │   │   └── code_generator.py # 编码生成器
│   │   │   │   ├── thuocl.py       # THUOCL 词频数据加载
│   │   └── plugins/            # 插件系统
│   │       ├── base.py         # 插件基类
│   │       └── manager.py      # 插件管理器
│   ├── ui/                     # 用户界面
│   │   ├── cli/                # 命令行界面
│   │   │   └── __main__.py     # CLI入口
│   │   └── gui/                # 图形界面
│   │       ├── pyqt_app.py     # PyQt6主应用
│   │       ├── tabs/           # 功能标签页
│   │       │   ├── words_tab.py      # 词表标签页
│   │       │   ├── chars_tab.py      # 字表标签页
│   │       │   ├── special_tab.py    # 特殊字符标签页
│   │       │   ├── stats_tab.py      # 统计标签页
│   │       │   ├── import_export_tab.py # 导入导出标签页
│   │       │   └── base_table_tab.py # 基础表格标签页
│   │       ├── settings/       # 设置页面
│   │       │   ├── theme_settings.py      # 主题设置
│   │       │   ├── cache_settings.py      # 缓存设置
│   │       │   ├── code_rules_settings.py # 编码规则设置
│   │       │   ├── config_db_settings.py  # 数据库配置
│   │       │   ├── delete_table_settings.py # 删除表设置
│   │       │   ├── file_config_settings.py # 文件配置
│   │       │   ├── language_settings.py   # 语言设置
│   │       │   └── stats_settings.py      # 统计设置
│   │       ├── threads/        # 后台线程
│   │       │   ├── import_thread.py       # 导入线程
│   │       │   ├── add_batch_thread.py    # 批量添加线程
│   │       │   ├── calculate_thread.py    # 计算线程
│   │       │   └── refresh_data_thread.py # 刷新数据线程
│   │       ├── theme_manager.py # 主题管理器
│   │       ├── theme_utils.py  # 主题工具
│   │       ├── progress_bar.py # 进度条组件
│   │       ├── settings_tab.py # 设置标签页
│   │       └── code_rules_tab.py # 编码规则标签页
│   ├── plugins/                # 插件目录
│   │   └── example_plugin.py   # 示例插件
│   ├── scripts/                # 脚本目录
│   │   └── build.py            # 构建脚本
│   ├── tests/                  # 测试目录
│   │   └── unit/               # 单元测试
│   │       ├── test_code_generator.py
│   │       └── test_dict_service.py
│   ├── main.py                 # 程序入口
│   ├── vmtool.py               # CLI入口
│   ├── pyproject.toml          # 项目配置
│   ├── requirements.txt        # 依赖列表
│   ├── THUOCL-data/             # THUOCL 词频数据（清华开源中文词频）
│   └── vm_tool.db              # SQLite数据库文件
├── architecture.mmd            # 架构图（Mermaid）
├── architecture_detailed.mmd   # 详细架构图
├── description.md              # 项目描述
├── code_analysis_report.md     # 代码分析报告
├── AGENTS.md                   # AI代理指南
└── CLAUDE.md                   # 开发规范
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

支持自定义python函数编码规则,详情参考GUI界面

## 技术栈

- **Python** >= 3.10
- **CLI**: Typer + Rich
- **GUI**: PyQt6
- **数据库**: SQLite + SQLAlchemy ORM
- **配置**: Pydantic + Pydantic Settings
- **迁移**: Alembic
- **构建**: PyInstaller
- **测试**: pytest + coverage
- **代码质量**: black, isort, ruff, mypy

## 开发

```bash
# 安装开发依赖
pip install -e ".[test,quality]"

# 测试
pytest

# 代码检查
ruff check .
mypy app/

# 格式化
black .
isort .

# 构建可执行文件
python vm-tool/scripts/build.py --linux
```

## 配置

### 主题设置
- 支持深色/浅色/自动主题模式
- 多种主题颜色：蓝色、绿色、红色、紫色、橙色
- 经典主题名称

### 导出设置
- 默认导出路径和格式
- 分表导出支持
- 自动导出到 ibus/rime 和 fcitx5/rime 目录

### 缓存设置
- 可配置缓存大小和过期时间
- 性能监控

## 许可证

MIT
