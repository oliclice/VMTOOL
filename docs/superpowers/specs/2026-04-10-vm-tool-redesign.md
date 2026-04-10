# VM-TOOL 现代化重构设计规范

**版本**: 1.0  
**日期**: 2026-04-10  
**状态**: 已批准  
**作者**: Claude Code  

## 1. 项目概述

### 1.1 背景
现有码表处理工具已具备基本功能，但存在性能瓶颈、代码质量问题和扩展性限制。本次重构旨在通过全面现代化改造，打造一个工业级、高性能、可扩展的码表管理系统。

### 1.2 设计目标
1. **性能卓越**：支持百万级词条处理，关键操作速度提升10倍以上
2. **跨平台支持**：支持Windows、Linux、macOS，多种部署方式
3. **扩展性强**：插件化架构，易于功能扩展和定制开发
4. **用户体验优秀**：提供CLI、GUI、Web多种交互方式
5. **代码质量高**：完整类型系统、全面测试覆盖、规范文档

## 2. 技术架构

### 2.1 总体架构

```
┌─────────────────────────────────────────────────────────────┐
│                   用户界面层                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │
│  │ CLI界面 │ │ Web界面 │ │ GUI界面 │ │ API接口 │         │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                   应用程序核心                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   运行模式管理器                        │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                │  │
│  │  │CLI模式││API模式││GUI模式││Web模式│                │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘                │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │
│  │ 码表服务 │ 统计服务 │ 导入服务 │ 插件管理 │         │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   数据访问抽象层                        │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                │  │
│  │  │SQLite适配│ 内存适配器│ 文件适配器│                │  │
│  │  └─────────┘ └─────────┘ └─────────┘                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                   数据存储层                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                      │
│  │SQLite文件│ 缓存文件  │  用户文件 │                      │
│  └─────────┘ └─────────┘ └─────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

#### 核心框架
- **API框架**: FastAPI + Pydantic - 高性能、自动文档、完整类型支持
- **CLI框架**: Typer - 现代CLI框架，代码即文档
- **异步框架**: asyncio + anyio - 跨平台异步支持
- **数据库ORM**: SQLAlchemy 2.0 + Alembic - 现代化ORM，支持异步

#### 数据存储
- **主数据库**: SQLite 3.40+ - 嵌入式，高性能，无需独立服务
- **缓存**: diskcache - 本地文件缓存，避免外部依赖
- **文件存储**: 结构化目录 + JSON/YAML配置文件

#### 用户界面
- **命令行界面**: Typer + Rich - 美观的命令行，支持彩色输出、进度条
- **Web界面**: FastAPI内置 + Jinja2 + HTMX - 轻量级，无需前端框架
- **桌面GUI**: Tkinter (内置) 或 PyQt6 (可选) - 跨平台桌面应用
- **API接口**: OpenAPI 3.0规范，支持自动生成客户端

#### 开发工具
- **类型检查**: mypy + Pydantic - 严格类型安全
- **代码格式化**: black + isort - 统一代码风格
- **代码检查**: ruff - 极速Python代码检查器
- **测试框架**: pytest + hypothesis + coverage - 完整测试生态
- **打包工具**: PyInstaller + Nuitka - 多平台可执行文件生成

### 2.3 部署方案

#### 1. 可执行文件（推荐）
- **Windows**: `.exe` 文件，双击运行
- **Linux**: 二进制可执行文件，`chmod +x` 后运行
- **macOS**: `.app` 应用程序包
- **特点**: 包含所有依赖，无需安装Python环境

#### 2. Python包安装
```bash
pip install vm-tool
vm-tool --help  # CLI模式
vm-tool --web   # Web模式
```

#### 3. 便携绿色版本
- 解压即用，不写注册表
- 适合U盘携带、多用户环境、临时使用
- 配置文件和数据存储在应用目录内

#### 4. Docker容器（可选）
```bash
docker run -v ./data:/app/data -p 8000:8000 vm-tool --web
```

### 2.4 更新机制

#### 自动更新
1. **版本检测**: 启动时检查GitHub Releases新版本
2. **增量下载**: 只下载变化的文件，减少带宽
3. **静默更新**: 后台下载，重启生效
4. **回滚机制**: 保留上一个版本，更新失败可回滚

#### 数据迁移
1. **数据库迁移**: Alembic自动迁移schema
2. **配置迁移**: 自动转换旧版本配置格式
3. **数据导入**: 支持导入旧版本数据文件

## 3. 核心模块设计

### 3.1 应用程序核心 (`app/core/`)

#### 运行模式管理器 (`mode_manager.py`)
```python
class AppMode(Enum):
    CLI = "cli"
    WEB = "web"
    GUI = "gui"
    API = "api"

class ModeManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.current_mode: Optional[AppMode] = None
        
    async def start(self, mode: AppMode):
        """启动指定模式"""
        self.current_mode = mode
        
        # 初始化对应模式的组件
        if mode == AppMode.CLI:
            from ui.cli.main import cli_app
            await cli_app.run()
        elif mode == AppMode.WEB:
            from ui.web.server import web_server
            await web_server.start()
        elif mode == AppMode.GUI:
            from ui.gui.main import gui_app
            await gui_app.run()
        elif mode == AppMode.API:
            from app.api.server import api_server
            await api_server.start()
```

#### 服务管理器 (`service_manager.py`)
```python
@ServiceRegistry.register("dict")
class DictService:
    """码表服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def query_word(self, word: str) -> Optional[WordEntry]:
        """查询词条"""
        from app.dal.repositories import WordRepository
        repo = WordRepository(self.db)
        return await repo.get_by_word(word)
        
    async def add_words(self, words: List[WordInput]) -> List[WordEntry]:
        """批量添加词条"""
        from app.dal.repositories import WordRepository
        repo = WordRepository(self.db)
        
        # 生成编码并创建词条
        entries = []
        for word_input in words:
            code = await self._generate_code(word_input.word)
            entry = WordEntry(
                word=word_input.word,
                code=code,
                weight=word_input.weight or 1.0
            )
            entries.append(entry)
        
        return await repo.bulk_insert(entries)
        
    async def filter_words(self, filter_rules: FilterRules) -> int:
        """过滤词条"""
        from app.dal.repositories import WordRepository
        repo = WordRepository(self.db)
        return await repo.delete_by_filter(filter_rules)
```

### 3.2 数据访问层 (`app/dal/`)

#### 数据模型 (`models.py`)
```python
class WordEntry(Base):
    __tablename__ = "words"
    
    id = Column(Integer, primary_key=True)
    word = Column(String(50), nullable=False, unique=True)
    code = Column(String(20), nullable=False, index=True)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 全文搜索索引
    __table_args__ = (
        Index('idx_word_code', 'word', 'code'),
    )

class WordRepository:
    """词条仓库"""
    
    async def bulk_insert(self, words: List[WordEntry]) -> int:
        """批量插入，使用SQLite的批量操作优化"""
        if not words:
            return 0
            
        # 使用SQLAlchemy Core进行批量插入以获得更好性能
        values = [
            {
                'word': entry.word,
                'code': entry.code,
                'weight': entry.weight
            }
            for entry in words
        ]
        
        stmt = insert(WordEntry.__table__).values(values)
        result = await self.db.execute(stmt)
        return result.rowcount
```

### 3.3 插件系统 (`app/plugins/`)

#### 插件管理器 (`plugin_manager.py`)
```python
class Plugin:
    """插件基类"""
    
    name: str
    version: str
    description: str
    
    async def initialize(self, context: PluginContext):
        """插件初始化"""
        # 注册插件提供的服务
        context.service_registry.register(self.name, self)
        # 初始化插件配置
        self.config = await context.config_manager.load_plugin_config(self.name)
        
    async def cleanup(self):
        """插件清理"""
        # 保存插件状态
        await self.config_manager.save_plugin_config(self.name, self.config)
        # 注销服务
        self.context.service_registry.unregister(self.name)

class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, Plugin] = {}
        
    async def load_plugins(self):
        """动态加载插件"""
        if not self.plugin_dir.exists():
            return
            
        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
                
            # 动态导入插件模块
            module_name = f"app.plugins.{plugin_file.stem}"
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 实例化插件
            plugin_class = getattr(module, "Plugin", None)
            if plugin_class and issubclass(plugin_class, Plugin):
                plugin = plugin_class()
                await plugin.initialize(self.context)
                self.plugins[plugin.name] = plugin
```

### 3.4 用户界面层

#### CLI界面 (`ui/cli/`)
```python
import typer

app = typer.Typer(rich_markup_mode="rich")

@app.command()
def add(
    words: List[str] = typer.Argument(..., help="要添加的词"),
    code: Optional[str] = typer.Option(None, "--code", "-c", help="指定编码"),
    weight: float = typer.Option(1.0, "--weight", "-w", help="权重值"),
):
    """添加新词到码表"""
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.console import Console
    
    console = Console()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("添加词条...", total=len(words))
        
        # 调用服务添加词条
        from app.core.service_manager import ServiceManager
        service_mgr = ServiceManager.get_instance()
        dict_service = service_mgr.get_service("dict")
        
        word_inputs = [
            WordInput(word=word, code=code, weight=weight)
            for word in words
        ]
        
        results = await dict_service.add_words(word_inputs)
        
        progress.update(task, completed=len(words))
    
    console.print(f"[green]✓ 成功添加 {len(results)} 个词条[/green]")
    return results
```

#### Web界面 (`ui/web/`)
- **前端**: Jinja2模板 + HTMX + Tailwind CSS
- **后端**: FastAPI路由
- **特性**: 实时更新、无需刷新页面、移动端友好

## 4. 性能优化方案

### 4.1 数据库优化
1. **批量操作**: 使用SQLite的 `executemany()` 批量插入
2. **索引优化**: 为高频查询字段建立复合索引
3. **连接池**: SQLAlchemy连接池，复用数据库连接
4. **读写分离**: 读操作使用连接池，写操作串行化

### 4.2 内存优化
1. **惰性加载**: 大数据集分页加载，避免全量内存占用
2. **缓存策略**: LRU缓存高频查询结果
3. **内存映射文件**: 大文件使用内存映射减少内存拷贝

### 4.3 算法优化
1. **权重计算**: 从O(n²)优化到O(n log n)
2. **过滤算法**: 使用布隆过滤器预过滤，减少全表扫描
3. **编码生成**: 预编译字库索引，O(1)复杂度生成编码

## 5. 迁移计划

### 5.1 阶段一：基础框架搭建 (1-2周)
- 项目脚手架搭建
- 数据库模型设计
- 核心服务接口定义
- 基础测试框架

### 5.2 阶段二：核心功能实现 (2-3周)
- 码表CRUD操作
- 权重计算算法
- 过滤和导入功能
- CLI界面实现

### 5.3 阶段三：高级功能开发 (1-2周)
- Web界面开发
- 插件系统实现
- 性能优化
- 多平台打包

### 5.4 阶段四：测试和发布 (1周)
- 完整测试覆盖
- 性能基准测试
- 用户文档编写
- 发布准备

## 6. 成功指标

### 6.1 性能指标
- **加载速度**: 100万词条加载时间 < 5秒
- **过滤速度**: 批量过滤10万词条 < 3秒
- **权重计算**: 全表权重计算 < 10秒
- **内存占用**: 峰值内存 < 500MB (100万词条)

### 6.2 质量指标
- **代码覆盖率**: > 90%
- **类型检查**: 100%通过mypy严格模式
- **API文档**: 100%自动生成
- **测试通过率**: 100%

### 6.3 用户体验指标
- **CLI响应**: 所有操作 < 2秒反馈
- **Web界面**: 首屏加载 < 1秒
- **安装便利**: 一键安装/解压即用
- **配置迁移**: 100%自动迁移旧版本数据

## 7. 风险评估与缓解

### 7.1 技术风险
| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| SQLite性能不足 | 低 | 高 | 提前性能测试，准备PostgreSQL迁移方案 |
| 异步框架复杂性 | 中 | 中 | 渐进式采用，提供同步兼容接口 |
| 跨平台兼容性问题 | 中 | 高 | 持续集成测试，多平台自动化测试 |

### 7.2 项目风险
| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 开发周期超时 | 中 | 中 | 分阶段交付，优先核心功能 |
| 用户接受度低 | 低 | 高 | 保持向后兼容，提供迁移工具 |
| 资源不足 | 低 | 中 | 聚焦核心功能，简化非必要特性 |

## 8. 附录

### 8.1 数据库Schema设计
```sql
-- 词条表
CREATE TABLE words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    code TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 字库表
CREATE TABLE chars (
    char TEXT NOT NULL UNIQUE,
    code TEXT NOT NULL,
    frequency INTEGER DEFAULT 0
);

-- 索引
CREATE INDEX idx_words_code ON words(code);
CREATE INDEX idx_words_weight ON words(weight DESC);
CREATE INDEX idx_chars_code ON chars(code);
```

### 8.2 API接口规范
```yaml
openapi: 3.0.0
info:
  title: 码表管理API
  version: 1.0.0

paths:
  /api/v1/words:
    get:
      summary: 查询词条
      parameters:
        - name: q
          in: query
          schema:
            type: string
      responses:
        200:
          description: 查询结果
```

### 8.3 配置文件格式
```yaml
# config.yaml
app:
  name: "码表处理工具"
  version: "2.0.0"
  
database:
  path: "./data/dict.db"
  pool_size: 10
  
ui:
  default_mode: "cli"
  web_port: 8000
  
performance:
  cache_size: 10000
  batch_size: 1000
```

---
*文档最后更新: 2026-04-10*  
*下一步: 创建详细实施计划 (plan.md)*