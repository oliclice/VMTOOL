# VM-TOOL 码表处理工具

中文输入法码表管理工具，支持 CLI 和 GUI 界面，提供高效的码表增删改查、权重计算、过滤去重、导入导出等功能。

## 功能

- **码表管理**：词条/字/特殊符号的增删改查，支持批量操作
- **权重计算**：基于词频自动计算和调整权重
- **过滤去重**：批量过滤不需要的词条，智能去重
- **编码生成**：基于自定义编码规则自动生成编码
- **导入导出**：支持 TXT/CSV/JSON 格式导入导出，分表导出
- **统计功能**：高频编码统计、词条分布分析
- **查字补码**：自动补全缺失的编码

## 界面

| 界面 | 说明 |
|------|------|
| **CLI** | Typer 构建，支持命令模式和交互式模式，带自动补全 |
| **GUI (PyQt6)** | 多标签页桌面应用，含词/字/特殊/统计/导入导出等功能页 |
| **GUI (Tkinter)** | 轻量版图形界面 |

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
vmtool import --file path/to/file.txt
vmtool export --format csv --path output.csv
vmtool stats
```

### GUI 使用

```bash
python vm-tool/ui/gui/pyqt_app.py     # PyQt6 版本
python vm-tool/ui/gui/tkinter_app.py  # Tkinter 版本
```

## 项目结构

```
VMtool/
├── vm-tool/
│   ├── app/               # 核心应用代码
│   │   ├── core/          # 配置、缓存、运行模式、服务注册
│   │   ├── dal/           # 数据访问层 (SQLAlchemy)
│   │   ├── services/      # 业务逻辑 (字典/权重/过滤/统计/编码生成)
│   │   └── plugins/       # 插件系统
│   ├── ui/
│   │   ├── cli/           # 命令行界面 (Typer)
│   │   └── gui/           # 图形界面 (PyQt6 + Tkinter)
│   ├── tests/             # 测试
│   ├── main.py            # 程序入口
│   ├── vmtool.py          # CLI 入口
│   └── pyproject.toml     # 项目配置
├── dist/linux/            # 构建产物
├── docs/                  # 文档
├── AGENTS.md              # AI 代理指南
└── CLAUDE.md              # 开发规范
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

## 技术栈

- **Python** >= 3.10
- **CLI**: Typer + Rich
- **GUI**: PyQt6 / Tkinter
- **数据库**: SQLite + SQLAlchemy ORM
- **配置**: Pydantic + Pydantic Settings
- **迁移**: Alembic
- **构建**: PyInstaller

## 开发

```bash
# 安装开发依赖
pip install -e ".[test,quality]"

# 测试
pytest

# 代码检查
ruff check .
mypy app/

# 构建可执行文件
python vm-tool/scripts/build.py --linux
```

## 许可证

MIT
