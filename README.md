# VM-TOOL 码表处理工具

VM-TOOL 是一个现代化、模块化的中文输入法码表管理工具，支持命令行、Web和GUI界面，提供高效的码表处理功能。

## 功能特性

- **核心功能**:
  - 过滤码表: 批量过滤不需要的词条
  - 计算权重: 自动计算和调整词频权重
  - 码表补充: 批量添加新词并自动生成编码
  - 写入码表: 生成输出文件并复制到目标位置
  - 字表去重: 刷新和优化字库
  - 查字补码: 自动补全缺失的编码
  - 高频统计: 统计高频编码

- **现代化特性**:
  - 模块化架构: 清晰的代码组织和职责分离
  - 多界面支持: 命令行(CLI)、Web界面和GUI界面
  - 性能优化: 缓存机制、批处理优化和数据库索引
  - 类型安全: 使用Pydantic进行配置管理
  - 插件系统: 支持扩展功能
  - 多平台打包: 支持Windows、Linux和macOS

## 项目结构

```
VMtool/
├── vm-tool/             # 主项目目录
│   ├── app/             # 核心应用代码
│   │   ├── core/        # 核心功能模块
│   │   ├── dal/         # 数据访问层
│   │   ├── services/    # 业务逻辑服务
│   │   └── plugins/     # 插件系统
│   ├── ui/              # 用户界面
│   │   ├── cli/         # 命令行界面
│   │   ├── web/         # Web界面
│   │   └── gui/         # GUI界面 (Tkinter和PyQt6)
│   ├── tests/           # 测试代码
│   ├── main.py          # 主程序入口
│   ├── vmtool.py        # 命令行工具入口
│   ├── requirements.txt # 依赖管理
│   └── pyproject.toml   # 项目配置
├── build.py             # 多平台打包脚本
├── install.py           # 安装脚本
├── README.md            # 项目文档
└── pyinstaller.spec     # PyInstaller配置
```

## 安装和运行

### 安装依赖

```bash
# 创建虚拟环境
python3 -m venv vm-tool/.venv

# 激活虚拟环境
source vm-tool/.venv/bin/activate  # Linux/macOS
# .\vm-tool\.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r vm-tool/requirements.txt
```

### 运行程序

#### 命令行界面

```bash
# 运行命令行工具
python vm-tool/vmtool.py

# 查看帮助
python vm-tool/vmtool.py --help
```

#### Web界面

```bash
# 启动Web服务器
python vm-tool/ui/web/main.py

# 访问 http://localhost:8000
```

#### GUI界面

```bash
# 运行Tkinter GUI
python vm-tool/ui/gui/tkinter_app.py

# 运行PyQt6 GUI
python vm-tool/ui/gui/pyqt_app.py
```

## 使用方法

### 命令行界面

VM-TOOL 提供了丰富的命令行命令：

```bash
# 添加词
vmtool add --word "测试" --code "ceshi" --weight 100

# 删除词
vmtool delete --word "测试"

# 查询词
vmtool get --word "测试"

# 更新权重
vmtool update-weight --word "测试" --weight 200

# 导入数据
vmtool import --file "path/to/file.txt"

# 导出数据
vmtool export --file "path/to/output.txt"

# 显示统计信息
vmtool stats
```

### Web界面

Web界面提供了直观的图形化操作：
- **首页**: 显示应用信息和快捷操作
- **词表管理**: 查看、添加、编辑、删除词条
- **统计分析**: 查看码表统计信息
- **数据导入**: 批量导入词条

### GUI界面

GUI界面提供了更友好的桌面应用体验：
- **Tkinter版本**: 轻量级界面，兼容性好
- **PyQt6版本**: 功能更丰富，界面更美观

## 技术架构

### 核心模块

- **Core**: 核心功能模块，包括配置管理、缓存机制、兼容性层等
- **DAL**: 数据访问层，使用SQLAlchemy ORM进行数据库操作
- **Services**: 业务逻辑服务，包括字典服务、权重计算服务、过滤服务等
- **Plugins**: 插件系统，支持扩展功能
- **UI**: 用户界面，包括CLI、Web和GUI三种界面

### 服务架构

```
┌─────────────────┐
│     UI层        │
│ (CLI/Web/GUI)   │
└────────┬────────┘
         │
┌────────▼────────┐
│   服务层        │
│ (DictService等)  │
└────────┬────────┘
         │
┌────────▼────────┐
│   数据访问层     │
│ (Repository)    │
└────────┬────────┘
         │
┌────────▼────────┐
│   数据库        │
│ (SQLite)        │
└─────────────────┘
```

### 数据模型

- **Word**: 词条模型，包含词、编码、权重等字段
- **DictConfig**: 字典配置模型，存储配置信息

## 依赖

- Python 3.8+
- 核心依赖:
  - pydantic>=2.6.0
  - pydantic-settings>=2.1.0
  - sqlalchemy>=2.0.49
  - typer==0.9.0
  - rich==13.7.0
  - fastapi==0.104.1
  - uvicorn==0.24.0.post1
  - jinja2==3.1.2
  - tkinter (标准库)
  - PyQt6 (可选)

## 构建和打包

### 构建Linux版本

```bash
python build.py --linux
```

### 构建Windows版本

```bash
python build.py --windows
```

### 构建macOS版本

```bash
python build.py --macos
```

### 构建所有平台版本

```bash
python build.py --all
```

## 测试

```bash
# 运行测试
python -m pytest vm-tool/tests/

# 运行测试并生成覆盖率报告
python -m pytest vm-tool/tests/ --cov=app
```

## 许可证

MIT License
