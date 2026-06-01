# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

VMtool 是一个中文输入法码表管理工具，提供 CLI 和 GUI 界面。支持词条管理、权重计算、代码生成、导入导出等功能，基于 Rime 输入法框架。

## 常用命令

### 开发环境

```bash
# 安装开发依赖
cd vm-tool
pip install -e ".[test,quality]"

# 或使用内置安装器
python vm-tool/vmtool.py --install
```

### 测试与质量检查

```bash
# 运行测试
pytest
pytest --cov=app --cov-report=html  # 带覆盖率

# 代码质量
ruff check .
mypy app/
black .
isort .
```

### 构建与打包

```bash
# 构建可执行文件
python vm-tool/scripts/build.py --linux

# PyInstaller 规格文件
vmtool.spec          # CLI 版本
vmtool-gui.spec      # GUI 版本
```

## 架构概览

采用分层架构：DAL → Services → UI

### 核心组件

- **DAL 层** (`app/dal/`): SQLAlchemy ORM，管理 SQLite 数据库
  - `database.py`: 引擎/会话管理
  - `models.py`: Word、DictConfig 模型
  - `repositories.py`: 仓库模式封装

- **Services 层** (`app/services/`): 业务逻辑
  - `DictService`: 核心服务（CRUD、代码生成、导出）
  - `WeightCalculator`: 基于词频的权重计算
  - `FilterService`: 过滤服务
  - `StatsService`: 统计服务

- **UI 层**:
  - CLI: Typer + Rich (`ui/cli/__main__.py`)
  - GUI: PyQt6 (`ui/gui/pyqt_app.py`)

### 关键设计决策

- 单表设计：`words` 表通过 `is_character`、`is_special` 布尔字段区分词条类型
- 双配置系统：`config.py`（Pydantic 静态配置）+ `config_manager.py`（JSON 运行时配置）
- 代码生成支持模板语法和 Python 模式（使用 `exec()`，注意安全风险）

## 重要注意事项

### 高风险组件

- **`generate_code`**: 15 个执行流依赖，修改前必须运行影响分析
- **`compatibility.py`**: 0% 测试覆盖率
- **测试覆盖**: 仅 2 个测试文件，需谨慎修改

### 已知问题

- 异常处理不一致（部分错误静默返回空字符串）
- `config_manager` 读取 `database_path` 可能产生循环依赖
- 服务注册表存在但实际未使用

## GitNexus 集成

项目已通过 GitNexus 索引（720 符号，2028 关系，58 执行流）。修改代码前必须：

1. 运行 `gitnexus_impact({target: "symbolName", direction: "upstream"})` 分析影响范围
2. 修改后运行 `gitnexus_detect_changes()` 验证变更范围
3. 重新提交后运行 `npx gitnexus analyze` 更新索引

### GitNexus 工具快速参考

| 工具 | 用途 |
|------|------|
| `gitnexus_query` | 按概念查找代码 |
| `gitnexus_context` | 获取符号完整上下文 |
| `gitnexus_impact` | 编辑前影响分析 |
| `gitnexus_rename` | 安全重命名 |

## grep 或 glob 搜索时

过滤掉 `.venv` 和 `.git` 文件，避免结果截断。

## 开发提示

- GUI 长时间操作使用后台线程（`ui/gui/threads/`）
- 数据库迁移使用 Alembic
- 运行时配置存储在 `~/.config/vm-tool/config.json`
- 词频数据在 `vm-tool/data/` 目录
