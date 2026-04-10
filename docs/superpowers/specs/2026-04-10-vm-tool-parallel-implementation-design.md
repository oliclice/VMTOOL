# VM-TOOL 并行重构实施设计

**版本**: 1.0  
**日期**: 2026-04-10  
**状态**: 已批准  
**作者**: Claude Code  
**关联文档**: [2026-04-10-vm-tool-redesign.md](2026-04-10-vm-tool-redesign.md)

## 1. 实施策略选择

### 1.1 选择方案：并行开发，迭代交付
基于用户选择，采用**方案二（并行开发，迭代交付）**作为实施策略。该方案允许同时推进多个开发路径，以迭代方式交付完整功能。

### 1.2 决策记录
- **起始阶段**: 阶段一：基础框架搭建（完整实施）
- **兼容性要求**: 全新设计，不要求兼容（提供数据迁移工具）
- **项目结构**: 完全按照CLAUDE.md规范
- **技术栈**: 完全按照CLAUDE.md中描述的FastAPI + SQLAlchemy + Typer + SQLite组合
- **质量标准**: 严格执行CLAUDE.md中的质量标准

## 2. 并行开发架构

### 2.1 并行开发路径定义

| 路径 | 负责人 | 核心模块 | 迭代1目标 | 迭代2目标 | 依赖关系 |
|------|--------|----------|-----------|-----------|----------|
| **A** | Team A | 基础框架+数据层 | 数据库模型、迁移工具、配置系统 | 缓存层、性能监控 | 无外部依赖 |
| **B** | Team B | 核心服务层 | 词条CRUD、基础搜索 | 权重计算、过滤、统计、插件框架 | 依赖路径A的数据接口 |
| **C** | Team C | CLI界面 | 核心命令（增删改查） | 完整CLI功能、交互模式 | 依赖路径B的服务接口 |

*注：Team A/B/C代表逻辑上的开发路径，在实际单人开发中按此路径顺序并行推进工作。*

### 2.2 迭代交付计划

*注：时间表中的"周"指工作周（5个工作日），实际进度可根据开发情况调整。*

#### 迭代1（2周）：基础版码表管理
**目标**: 提供一个可用的基础版码表管理工具
- ✅ 数据库模型和迁移工具完成
- ✅ 词条CRUD服务（基本功能）实现
- ✅ 命令行界面（核心命令）可用
- ✅ 数据迁移工具（旧数据导入）完成

#### 迭代2（2周）：完整功能集
**目标**: 实现所有核心业务功能
- 🔄 权重计算、过滤、统计服务完成
- 🔄 插件系统框架搭建
- 🔄 命令行界面（完整功能）实现
- 🔄 性能优化基础实施

#### 迭代3（2周）：用户界面扩展
**目标**: 提供多种用户界面选择
- ⏳ Web界面（FastAPI + HTMX）开发
- ⏳ 桌面GUI（Tkinter基础版）实现
- ⏳ API文档和客户端生成
- ⏳ 多平台打包完成

## 3. 技术实现详情

### 3.1 核心技术栈配置

#### Python版本要求
- Python 3.10+（必须支持类型提示和现代异步特性）

#### 主要依赖包 (pyproject.toml)
```toml
[project]
dependencies = [
    "fastapi>=0.104.0",
    "sqlalchemy>=2.0.0", 
    "typer>=0.9.0",
    "pydantic>=2.5.0",
    "alembic>=1.12.0",
    "diskcache>=5.6.0",
    "rich>=13.0.0",
    "httpx>=0.25.0",
    "click>=8.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.7.0",
    "ruff>=0.1.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "hypothesis>=6.0.0",
]
```

### 3.2 数据库设计

#### SQLite配置优化
- 启用WAL模式（Write-Ahead Logging）
- 设置合适的页面大小和缓存
- 配置同步模式为NORMAL

#### 核心数据模型
```sql
-- 词条表 (dict_entries)
CREATE TABLE dict_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    code TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    frequency INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引优化
CREATE INDEX idx_dict_entries_code ON dict_entries(code);
CREATE INDEX idx_dict_entries_weight ON dict_entries(weight DESC);
CREATE INDEX idx_dict_entries_word_code ON dict_entries(word, code);
```

### 3.3 关键接口定义

#### 数据访问层接口 (路径A)
```python
# app/dal/interfaces.py
from typing import Protocol, Optional, List
from dataclasses import dataclass

@dataclass
class DictEntry:
    word: str
    code: str
    weight: float = 1.0
    frequency: int = 0

class DictRepository(Protocol):
    """词条仓库接口 - 确保并行开发兼容性"""
    async def get(self, word: str) -> Optional[DictEntry]
    async def add(self, entry: DictEntry) -> DictEntry
    async def update(self, word: str, **updates) -> Optional[DictEntry]
    async def delete(self, word: str) -> bool
    async def search(self, query: str, limit: int = 100) -> List[DictEntry]
```

#### 服务层接口 (路径B)
```python
# app/services/interfaces.py
class DictService(Protocol):
    """词条服务接口"""
    async def add_word(self, word: str, code: Optional[str] = None) -> DictEntry
    async def delete_word(self, word: str) -> bool
    async def search_words(self, query: str, **filters) -> List[DictEntry]
    async def update_weight(self, word: str, delta: int) -> Optional[DictEntry]
    
    # 批量操作
    async def batch_import(self, file_path: Path, format: FileFormat) -> ImportResult
    async def batch_export(self, file_path: Path, format: FileFormat) -> ExportResult
    
    # 类型定义占位符：
    # - FileFormat: 枚举类型，支持TXT、CSV、JSON等格式
    # - ImportResult: 数据类，包含导入统计信息
    # - ExportResult: 数据类，包含导出统计信息
```

#### CLI命令接口 (路径C)
```python
# ui/cli/commands.py
import typer

app = typer.Typer(rich_markup_mode="rich")

@app.command()
def add(
    words: List[str] = typer.Argument(..., help="要添加的词语"),
    code: Optional[str] = typer.Option(None, "--code", "-c", help="指定编码"),
    weight: int = typer.Option(1, "--weight", "-w", help="初始权重"),
):
    """添加新词到码表"""
    # 实现依赖于DictService接口
    pass
```

### 3.4 并行开发协调机制

#### 接口版本控制
```python
# 所有接口都使用版本后缀
INTERFACE_VERSION = "v1"

class DictServiceV1(DictService):
    """版本化接口，确保向后兼容"""
    pass
```

#### 模拟实现（用于并行测试）
```python
# 路径C在路径B完成前可以使用的模拟服务
class MockDictService(DictService):
    """模拟服务实现，用于CLI开发测试"""
    def __init__(self):
        self._data: Dict[str, DictEntry] = {}
    
    async def add_word(self, word: str, code: Optional[str] = None) -> DictEntry:
        entry = DictEntry(word=word, code=code or f"mock_{hash(word)}")
        self._data[word] = entry
        return entry
```

#### 集成测试接口
```python
# 跨团队集成测试的公共接口
@pytest.fixture
async def dict_service():
    """提供统一的测试服务实例"""
    config = AppConfig(database_url="sqlite+aiosqlite:///:memory:")
    repo = SQLiteDictRepository(config)
    service = DictServiceImpl(repo)
    await service.initialize()
    yield service
    await service.shutdown()
```

## 4. 项目结构

### 4.1 新项目目录结构
```
vm-tool/ (新项目根目录)
├── app/
│   ├── core/                    # 应用核心（路径A）
│   │   ├── __init__.py
│   │   ├── mode_manager.py     # 运行模式管理
│   │   ├── service_registry.py # 服务注册和管理
│   │   └── error_handler.py    # 错误处理框架
│   ├── services/               # 业务服务层（路径B）
│   │   ├── __init__.py
│   │   ├── dict_service.py     # 词条服务
│   │   ├── weight_service.py   # 权重计算服务
│   │   ├── filter_service.py   # 过滤服务
│   │   ├── stats_service.py    # 统计服务
│   │   └── interfaces.py       # 服务接口定义
│   ├── dal/                    # 数据访问层（路径A）
│   │   ├── __init__.py
│   │   ├── models.py          # SQLAlchemy数据模型
│   │   ├── repositories.py    # 数据仓库实现
│   │   ├── migrations/        # Alembic迁移脚本
│   │   └── interfaces.py      # 数据访问接口定义
│   ├── plugins/               # 插件系统（迭代2）
│   │   ├── __init__.py
│   │   ├── plugin_manager.py  # 插件管理器
│   │   └── base.py           # 插件基类
│   └── config.py             # 应用配置管理
├── ui/
│   ├── cli/                  # 命令行界面（路径C）
│   │   ├── __init__.py
│   │   ├── main.py          # CLI入口
│   │   ├── commands/        # 命令定义
│   │   │   ├── __init__.py
│   │   │   ├── add.py       # 添加命令
│   │   │   ├── delete.py    # 删除命令
│   │   │   ├── search.py    # 搜索命令
│   │   │   └── manage.py    # 管理命令
│   │   └── context.py       # CLI上下文
│   ├── web/                 # Web界面（迭代3）
│   │   ├── __init__.py
│   │   ├── server.py        # FastAPI服务器
│   │   ├── routes/          # API路由
│   │   ├── templates/       # Jinja2模板
│   │   └── static/          # 静态资源
│   └── gui/                 # GUI界面（迭代3）
│       ├── __init__.py
│       ├── main_window.py   # 主窗口
│       ├── widgets/         # 界面组件
│       └── dialogs/         # 对话框
├── tests/                   # 测试代码
│   ├── unit/               # 单元测试
│   ├── integration/        # 集成测试
│   ├── performance/        # 性能测试
│   └── conftest.py         # 测试配置
├── docs/                   # 文档
│   ├── api/               # API文档
│   ├── user-guide/        # 用户手册
│   └── developer-guide/   # 开发者指南
├── data/                  # 数据文件
│   ├── migrations/        # 数据迁移脚本
│   └── imports/          # 导入文件目录
├── scripts/              # 构建和工具脚本
│   ├── build.py          # 构建脚本
│   ├── install.py        # 安装脚本
│   └── migrate.py        # 迁移脚本
└── pyproject.toml        # 项目配置
```

### 4.2 现有代码迁移策略
1. **数据迁移优先**: 提供工具将现有`dicts/main.txt`和`singleWord/小鹤字库.txt`导入新数据库
2. **功能对等**: 确保新系统支持所有现有功能
3. **渐进迁移**: 新系统运行稳定后再完全切换

## 5. 开发工作流

### 5.1 代码质量要求
1. **类型检查**: `mypy --strict app/ ui/ tests/` 必须通过
2. **代码格式化**: `ruff format .` 和 `ruff check --fix .` 必须通过
3. **测试覆盖**: `pytest --cov=app --cov-report=html` 核心功能覆盖率>90%
4. **文档完整**: 所有公共API必须有类型提示和文档字符串

### 5.2 并行开发协调计划

| 时间点 | 路径A任务 | 路径B任务 | 路径C任务 | 集成任务 |
|--------|-----------|-----------|-----------|----------|
| **第1周结束** | 数据库模型完成 | 服务接口定义完成 | CLI框架搭建 | 接口评审会议 |
| **第2周结束** | 数据迁移工具完成 | 基础服务实现 | 核心命令实现 | 第一次集成测试 |
| **第3周结束** | 性能优化基础 | 高级服务开发 | 交互模式开发 | 第二次集成测试 |
| **第4周结束** | 缓存层完成 | 插件框架完成 | 完整CLI功能 | 迭代1验收 |

### 5.3 错误处理和日志
```python
# 统一错误类型
@dataclass
class ServiceError(Exception):
    """服务层统一错误类型"""
    code: str  # 错误代码，如 "DICT_NOT_FOUND"
    message: str
    details: Optional[Dict] = None

# 结构化日志
import structlog
logger = structlog.get_logger(__name__)
```

## 6. 风险管理和缓解措施

### 6.1 技术风险
| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 并行开发接口不一致 | 中 | 高 | 提前定义接口契约，定期接口评审 |
| 集成测试复杂 | 中 | 中 | 使用模拟实现，分阶段集成 |
| 性能达不到目标 | 低 | 高 | 早期性能测试，准备优化方案 |

### 6.2 项目风险
| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 团队协调成本高 | 中 | 中 | 明确接口定义，定期同步会议 |
| 进度不同步 | 中 | 中 | 制定详细时间表，及时调整计划 |
| 质量要求冲突 | 低 | 中 | 统一质量标准，自动化检查 |

## 7. 成功标准

### 7.1 迭代1成功标准
- ✅ 数据库模型完整并通过迁移测试
- ✅ 基础词条CRUD服务可用
- ✅ 核心CLI命令功能正常
- ✅ 数据迁移工具工作正常
- ✅ 代码质量检查100%通过

### 7.2 最终成功标准
- ✅ 所有核心功能实现并通过测试
- ✅ 性能达到设计目标（100万词条加载<5秒）
- ✅ 代码覆盖率>90%，类型检查100%通过
- ✅ 多平台打包成功，可独立运行
- ✅ 用户文档和API文档完整

## 8. 下一步行动

1. **立即开始**: 创建新项目目录结构
2. **并行开发**: 
   - Team A: 实现数据库模型和迁移工具
   - Team B: 定义服务接口和基础实现
   - Team C: 搭建CLI框架和核心命令
3. **集成测试**: 第1周结束时进行首次接口集成测试
4. **迭代交付**: 按照迭代计划交付功能

---

*设计文档创建日期: 2026-04-10*  
*设计状态: 已批准*  
*下一步: 创建详细实施计划并开始并行开发*