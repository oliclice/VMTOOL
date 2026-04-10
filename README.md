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

### 方法一：使用构建后的可执行文件（推荐）

构建后的工具位于 `dist/linux` 目录下，包含两个版本：
- `vmtool` - 命令行工具
- `vmtool-gui` - 图形界面工具

#### 命令行界面

```bash
# 运行命令行工具
./dist/linux/vmtool/vmtool

# 查看帮助
./dist/linux/vmtool/vmtool --help
```

#### GUI界面

```bash
# 运行图形界面工具
./dist/linux/vmtool-gui/vmtool-gui
```

### 方法二：从源代码运行

#### 安装依赖

```bash
# 创建虚拟环境
python3 -m venv vm-tool/.venv

# 激活虚拟环境
source vm-tool/.venv/bin/activate  # Linux/macOS
# .\vm-tool\.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r vm-tool/requirements.txt
```

#### 运行程序

```bash
# 运行命令行工具
python vm-tool/vmtool.py

# 运行Web服务器
python vm-tool/ui/web/main.py

# 运行PyQt6 GUI
python vm-tool/ui/gui/pyqt_app.py
```

## 使用方法

### 命令行界面

VM-TOOL 提供了丰富的命令行命令：

```bash
# 添加词
vmtool add --word 测试 --code ceshi --weight 100

# 批量添加词
vmtool add-batch --file path/to/file.txt

# 删除词
vmtool delete --word 测试

# 批量删除词
vmtool delete-batch --file path/to/file.txt

# 查询词
vmtool query --keyword 测试

# 更新权重
vmtool update-weight --word 测试 --weight 200

# 直接设置权重
vmtool set-weight --word 测试 --weight 200

# 替换词条编码
vmtool replace-code --word 测试 --old-code oldcode --new-code newcode

# 导入数据
vmtool import --format txt --path path/to/file.txt

# 导出数据
vmtool export --format csv --path path/to/output.csv

# 显示统计信息
vmtool stats

# 迁移旧数据
vmtool migrate

# 交互式模式
vmtool interactive

# 旧版本接口兼容
vmtool old
```

### 添加字典和词典

#### 字典（Dict）

字典是指单个文字的集合，每个文字可以对应多个编码（支持多音字），通过以下方式添加：

1. **命令行添加单个文字**：
   ```bash
   # 添加单个文字和编码
   vmtool add --word 行 --code xing --weight 100
   # 为同一文字添加另一个编码（多音字）
   vmtool add --word 行 --code hang --weight 100
   ```

2. **命令行批量添加文字**：
   ```bash
   vmtool add-batch --file path/to/file.txt
   ```

3. **Web界面添加**：
   - 打开Web界面，进入"词表管理"页面
   - 点击"添加词条"按钮
   - 输入单个文字、编码和权重，点击"保存"
   - 可以为同一文字多次添加不同编码

4. **GUI界面添加**：
   - 打开GUI界面（Tkinter或PyQt6版本）
   - 点击"添加"按钮
   - 输入单个文字、编码和权重，点击"保存"
   - 可以为同一文字多次添加不同编码

#### 词典（Dictionary）

词典是指整个词库，包括编码的自动生成和导出功能：

1. **词典编码的自动生成**：
   - 当添加词条时，如果不指定编码，系统会自动生成编码
   - 例如：
     ```bash
     vmtool add --word 测试 --weight 100
     ```
     系统会自动为"测试"生成编码

2. **词典编码的自动导出**：
   - 导出为TXT格式：
     ```bash
     vmtool export --format txt --path path/to/output.txt
     ```
   - 导出为CSV格式：
     ```bash
     vmtool export --format csv --path path/to/output.csv
     ```
   - 导出为JSON格式：
     ```bash
     vmtool export --format json --path path/to/output.json
     ```

3. **词典的导入**：
   - 从TXT文件导入：
     ```bash
     vmtool import --format txt --path path/to/file.txt
     ```
   - 从CSV文件导入：
     ```bash
     vmtool import --format csv --path path/to/file.csv
     ```
   - 从JSON文件导入：
     ```bash
     vmtool import --format json --path path/to/file.json
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
  - typer==0.24.1
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
