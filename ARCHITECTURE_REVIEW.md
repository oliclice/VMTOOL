# VMtool 架构评审与优化方案

> 评审日期：2026-09-19
> 评审对象：`/home/wtuj/gits/VMtool/vm-tool`（版本 2.0.0）
> 方法：minread 最小化读取——按目录树 / 符号大纲 / 定向 grep / 实跑校验四步取证，未通读全量源码
> 取证环境：`vm-tool/.venv`（Python 3.14.5）

---

## 一、结论摘要

项目**分层骨架是清晰的**（DAL → Services → UI，80 个模块 13,674 行 Python），GUI 侧重构（Finder 三栏 + Material 3 主题）也已成体系。但在**依赖声明、缓存一致性、线程安全、质量门**四条命脉上存在结构性欠账，其中 3 项已达阻断级：

| 判断 | 结论 |
|------|------|
| 架构方向 | ✅ 分层设计合理，不需要推倒重来 |
| 能否交付 | ❌ 干净环境装完即坏（psutil 未声明） |
| 数据正确性 | ⚠️ 缓存永不失效 + 单连接多线程写库 |
| 安全 | ⚠️ `exec` 无沙箱，配置导入 = 任意代码执行 |
| 工程化 | ❌ 无 CI，ruff 1339 错，mypy 109 错，3 个测试用例 |

**优化路线**：不做大重写，按 4 个阶段递进——先止血（半天）→ 修正确性（1-2 天）→ 收敛架构（约 1 周）→ 建质量门（持续）。

---

## 二、架构现状（实测）

### 2.1 分层与体量

| 层 | 路径 | 模块数 | 行数 | 职责 |
|----|------|--------|------|------|
| Core | `app/core/` | 10 | — | 配置、缓存、主题、错误、兼容层、服务注册表 |
| DAL | `app/dal/` | 5 | — | SQLAlchemy 模型、仓库、迁移、建库 |
| Services | `app/services/` | 6 | — | 词条、权重、过滤、统计、编码生成、THUOCL |
| Plugins | `app/plugins/` | 3 | — | 插件基类 + 管理器（**未接线**） |
| UI-CLI | `ui/cli/` | 1 | 718 | Typer + Rich |
| UI-GUI | `ui/gui/` | 45 | 7,726 | PyQt6，tabs / settings / widgets / threads |
| Tests | `tests/` | 2 | 48 | 3 个用例 |

- **app/ 合计 5,230 行，ui/ 合计 8,444 行** → UI 占比 62%，符合 GUI 为主的定位。
- 最大单文件：`app/services/dict.py` 832 行，其次 `ui/cli/__main__.py` 718 行、`app/core/theme_config.py` 677 行。

### 2.2 关键设计决策（沿用即可，无需推翻）

- **单表多态**：`words` 表用 `is_character` / `is_special` / `manual` 布尔字段区分词条类型 —— 简单有效，配合已有索引可继续用。
- **双配置系统**：`app/core/config.py`（Pydantic Settings，静态）+ `app/core/config_manager.py`（JSON 运行时，`~/.config/vm-tool/config.json`）—— 分工明确，但存在循环依赖隐患（见 3.2）。
- **编码生成可编程**：模板语法 + Python 模式，用户自定义规则 —— 是产品差异化能力，不能砍，只能**加固**。

### 2.3 两条入口链（存在冗余）

```
[vmtool.py --install]  → pip install REQUIRED_DEPS → 转 ui/cli/__main__.py
[pyproject.scripts]    → ui.cli.__main__:app  (Typer)
[vmtool.py / main.py]  → 交互式菜单
```

`main.py`（1,923 字节）**不在任何入口点、spec 文件或构建脚本中被引用**，属遗留入口。

---

## 三、问题清单（按严重级，全部附证据）

### P0 — 阻断级（必须先修）

#### P0-1　未声明依赖 `psutil` 导致核心链路不可用

- **证据**：`app/core/cache.py:6` 顶层 `import psutil`；`app/services/dict.py:10` 导入 `app.core.cache`。实跑 `pytest tests/unit/test_dict_service.py` 直接 **collection error**：
  ```
  ModuleNotFoundError: No module named 'psutil'
  ```
- **事实**：`pyproject.toml` 与 `requirements.txt` 均**未声明 psutil**（实测 grep 无命中）。
- **影响**：任何干净环境 `pip install -e .` 后，`DictService` 无法导入 → CLI/GUI 全部核心功能瘫痪。这也让仅有的 3 个测试用例损失 1/3。

#### P0-2　全局缓存只写不清，读路径最长脏 1 小时

- **证据**：
  - `@cache.decorator()` 仅作用于 `DictService.get_word`（`dict.py:39`）与 `get_words_by_code`（`dict.py:76`）。
  - 全局 `cache = Cache()` 默认 `ttl=3600`（`app/core/cache.py:15, 84`）。
  - 全项目 **`cache.clear()` 零调用**（grep 无命中）；写操作只回调 `pyqt_app.py:97` 的 `stats_service.clear_cache`（只清统计缓存）。
- **影响**：GUI 中 `DictService` 是长驻单实例 → 改词/删词/改编码后，`get_word` / `get_words_by_code` 仍返回旧值，**最长 3600 秒**。属静默数据错误，用户无从察觉。

#### P0-3　`exec` 无沙箱，配置导入即任意代码执行

- **证据**：`app/services/code_generator.py:194`
  ```python
  exec(custom_rule_content, {}, local_vars)
  ```
  `globals` 传空字典 → Python 自动注入 `__builtins__`，`import os; os.system(...)`、`open(...)` 全部可用。
- **触发路径**：规则内容来源于可导入/导出的 `config.json`（`custom_rules[*].content` + `python_mode=true`）。**导入一份他人分享的配置 = RCE**；同时无超时、无资源限制，死循环会挂住调用线程。
- **影响**：任意文件读写/命令执行。这是本项目最高危的单点。

### P1 — 架构级（影响长期可维护性）

#### P1-1　依赖声明与实际使用严重脱节

| 依赖 | 声明处 | 实际引用 |
|------|--------|----------|
| `fastapi` | pyproject + requirements + `vmtool.py:16` 强装 | **0 处** |
| `uvicorn` | 同上 | **0 处** |
| `jinja2` | 同上 | **0 处** |
| `alembic` | 同上 | **0 处**；且无 `alembic.ini` / `migrations/`（迁移实为自研的 `app/dal/migration.py` 296 行） |
| `hypothesis` | pyproject[test] | **0 处** |
| `psutil` | **未声明** | 2 处（且是必需路径） |

`vmtool.py:17-19` 的 `REQUIRED_DEPS` 列表与 pyproject 硬编码对齐，把这 4 个无用重依赖（FastAPI + Starlette + Uvicorn + Jinja2 + 5 个传递依赖）装进每一个用户机器，白增安装体积与失败面，同时漏掉真正必需的 psutil。

#### P1-2　SQLite 单连接 + 7 个 QThread 并发写，且无任何锁

- **证据**：`app/dal/database.py:24` 用了 `poolclass=StaticPool`（全进程共享一条连接）+ `check_same_thread: False`（`:21`）+ `sessionmaker`（非 `scoped_session`）。
- 而 `ui/gui/threads/` 下 **7 个线程类全部直接操作 `dict_service`/`db`** 写库：`add_batch`、`calculate`、`delete_table`、`base_batch`、`auto_dedupe`、`import`、`refresh_data`。
- 全项目 grep `Lock()` / `RLock()` / `threading.` / `mutex` → **0 命中**。
- **影响**：并发写同一连接可致 `database is locked`、事务交错、读到未提交数据。SQLite 默认无行级锁，`StaticPool` 消除了连接池这一天然缓冲。

#### P1-3　Session 生命周期交给 GC

- **证据**：`dict.py:25` `self.db = next(get_db())`；`database.py:45-51` 中 `get_db` 是 generator，`finally: db.close()` 只在生成器被回收时执行。
- **影响**：会话不显式释放，事务边界不确定，长驻 GUI 下连接与未提交事务可能长期悬挂。这是 项目规范 中"`config_manager` 读取 `database_path` 可能产生循环依赖"的同一根因面——`database.py:6` 在 DAL 层反向导入 `app.core.config_manager`。

#### P1-4　死代码与重复实现（合计约 553 行 + 三套同功能 UI）

| 项 | 位置 | 证据 |
|----|------|------|
| 被遮蔽的死模块 | `ui/gui/threads.py`（110 行，4 个 Thread 类） | 与同名 package `ui/gui/threads/` 共存；Python 包优先级高于同名模块，`pyqt_app.py:38` 的 `from .threads import ...` 实际解析到 package → **该文件永不加载** |
| 零引用模块 | `ui/gui/settings/code_rules_settings.py`（388 行） | grep `CodeRulesSettings` 无任何使用方 |
| 功能重复 | `ui/gui/code_rules_tab.py`（578 行）vs `ui/gui/settings/code_rules_panel.py`（405 行） | 两者都被 `pyqt_app.py:402` / `settings/__init__.py:9` 实际使用 → 同一功能两套实现并行维护 |
| 未接线设施 | `app/core/service_registry.py`（55 行，12 个方法）+ `main.py` | `service_registry` 仅被 `main.py` import，而 `main.py` 无任何被引用方 → 整条链为死链 |
| 重复构建产物 | 仓库根 `build/`、`dist/`、`htmlcov/`(1.8M)、`.pytest_cache/`、`.coverage`、`vmtool.spec` | 与 `vm-tool/` 下同名产物重复；`vm-tool/dist` 已 588M、`build` 167M |

#### P1-5　质量门形同虚设，且藏有真 bug

- **ruff**：`Found 1339 errors`（916 个可自动修）
  - `W293` 空行含空白 **757**、`E501` 行过长 **355**、`F401` 未用导入 **119**、`E402` 导入不在顶部 30、`E712` 与 False 比较 25
- **mypy**：`Found 109 errors in 18 files (checked 28 source files)`
  - 典型：`app/services/dict.py` 把 SQLAlchemy 的 `Column[str]` / `Column[int]` 当原生 `str`/`int` 用（`:346 :347 :362 :380 :561 :593 :596 :680 :714 :739 :752`），另有 `:462`、`:680` 对 `Result` 取 `.rowcount`
- **真 bug（会 NameError）**：`ui/gui/tabs/refreshable_tab.py:113-114` `F821 Undefined name 'QPushButton'` —— 运行到该分支即崩
- **测试**：仅 3 个用例（`test_code_generator.py` 2 个 + `test_dict_service.py` 1 个且无法收集）；`app/core/compatibility.py`（356 行）覆盖率 0%
- **CI**：无 `.github/`、无 `.pre-commit-config.yaml`、无 `tox.ini` / `Makefile` —— **没有任何自动门禁**，上述数字只会继续增长

#### P1-6　Service 层职责膨胀，DAL 抽象被绕过

- `DictService`（832 行）同时承担：CRUD、编码生成、批量导入、自动去重、删表、导出、统计通知。
- `delete_table`（`:424-469`）与 `auto_dedupe`（`:689-782`）内直接写 `text("DELETE FROM words WHERE ...")` 原生 SQL，**绕过了 `WordRepository`**，使仓库抽象形同虚设；`repositories.py` 里 `bulk_create` 用 `bulk_insert_mappings` 后返回空列表（`:112`），调用方无法拿到实体。

---

## 四、优化方案（4 阶段，按 ROI 递进）

### 阶段 0：止血 —— 让项目在干净环境能跑（约半天）

1. **修依赖声明**（P0-1 + P1-1）
   - `pyproject.toml`：`dependencies` 加入 `psutil>=5.9`；**移除** `fastapi`、`uvicorn`、`jinja2`、`alembic`；`[test]` 移除 `hypothesis`。
   - `requirements.txt` 同步。
   - `vmtool.py:16-19` 的 `REQUIRED_DEPS` 改为与 pyproject 单一来源（建议运行时读 `importlib.metadata.requires("vm-tool")`，彻底消除双份清单）。
2. **修真 bug**：`ui/gui/tabs/refreshable_tab.py` 补 `QPushButton` 导入。
3. **删死代码**（P1-4）：`ui/gui/threads.py`、`ui/gui/settings/code_rules_settings.py`、`app/core/service_registry.py`、根目录 `build/ dist/ htmlcov/ .pytest_cache/ .coverage vmtool.spec`。
   - 删除前先确认 `rm -rf` 目标在 `.gitignore` 内，`main.py` 的去留需你确认（可能仍在本地脚本中用到）。
4. **验收**：`.venv/bin/python -m pytest -q` 三个用例全绿；`pip install -e .` 后 `python -c "from app.services.dict import DictService"` 无错。

### 阶段 1：正确性与安全 —— 消除静默数据错误与 RCE（1-2 天）

5. **缓存失效闭环**（P0-2）
   - 在 `DictService` 的所有写路径（`add_word(s)`、`update_word`、`delete_word(s)`、`replace_code`、`calculate_all_codes`、`auto_dedupe`、`delete_table`、`set_all_manual_to_false`）统一调用 `cache.clear()`（或按 key 前缀失效）。
   - 更稳的做法：把缓存键的空间限定到实例，并在 `_notify_data_changed` 里集中失效，避免遗漏。
   - 建议同时把 `ttl` 从 3600 降到 30-60 秒作为兜底。
6. **`exec` 加固**（P0-3）——三选一，按成本递增：
   - **最小改动**：`exec(code, {"__builtins__": {}}, local_vars)` 并白名单注入 `len/str/int/...`；
   - **推荐**：Python 模式改为「受限 AST 校验 + 白名单内建」——解析后拒绝 `Import`/`Attribute` 到 `__`/`Call` 到非白名单名；
   - **最稳**：规则执行移入独立子进程（`multiprocessing` + 超时 + `resource.setrlimit`），超时即杀。
   - 无论哪种，都补「导入配置时显式提示含 Python 规则并要求确认」。
7. **Session 生命周期显式化**（P1-3）
   - `DictService` 增加 `close()` / 上下文管理器协议（`__enter__` / `__exit__`），GUI 长驻实例在关闭时释放；`next(get_db())` 改为显式 `session_factory()` 并成对 `close()`。
   - 顺带解开 DAL → Core 反向依赖：`database.py` 的 `database_path` 改为由调用方注入或经 `app/core/config.py` 的 Settings 读取。
8. **并发写库收敛**（P1-2）
   - 最低成本：`StaticPool` 换成 `NullPool` + 每线程独立 session，并开启 SQLite WAL（`PRAGMA journal_mode=WAL`）。
   - 或引入一把全局 `threading.RLock` 串行化写操作（GUI 场景写入频率低，串行化代价可接受）。
   - 更彻底：写操作全部走单一 worker 线程 + 队列（现有 `threads/` 结构天然适配）。
9. **补测试基线**：`app/core/compatibility.py`（0% 覆盖）补 parse/convert 的纯函数用例；`code_generator` 补 Python 模式加固后的用例。

### 阶段 2：架构收敛 —— 拆分胖 Service、统一数据访问（约 1 周）

10. **拆分 `DictService`**（P1-6）：按已存在的调用边界切成
    - `DictQueryService`（查询/搜索/分页）
    - `DictWriteService`（增删改）
    - `BatchService`（`add_words`、`calculate_all_codes`、`auto_dedupe`）
    - `ExportService`（`export_data`、`_get_table_data`）
    - 保留 `DictService` 为 facade 转发，**GUI/CLI 调用点零改动** → 可分批迁移、随时回滚。
    - **前置动作**：按项目规范，改 `generate_code` 等符号前必须跑 `gitnexus_impact`，`generate_code` 有 15 个执行流依赖，属高风险区。
11. **收口原生 SQL**：把 `delete_table` / `auto_dedupe` 中的 `text("DELETE ...")` 下沉到 `WordRepository.delete_by_type()` / `iter_by_type()`。
12. **修 `bulk_create` 返回空列表**（`repositories.py:112`）：改用 `insert().returning()` 或 `bulk_save_objects`，让调用方能拿到实体。
13. **UI 去重**（P1-4）：`code_rules_tab.py` 与 `settings/code_rules_panel.py` 合并为一套（建议保留 `settings/` 版，`tab` 改为薄壳复用），消除双份维护。
14. **插件系统决策**：`app/plugins/manager.py`（247 行）+ `plugins/example_plugin.py` 目前未接线。要么接入启动流程（`app/plugins` 在 `pyqt_app`/CLI 初始化时 `load_all_plugins`），要么明确标注为实验特性——避免又一个"存在但不用"的设施。

### 阶段 3：建立质量门（持续）

15. **ruff 自动修**：`ruff check . --fix` 一次清掉 916 个（主要是 W293/E501/F401），随后在 pyproject 收敛规则集（当前只开了 `E,F,W`，建议加 `I`（isort）、`B`（bugbear）、`UP`）。
16. **mypy 分模块收紧**：先对 `app/dal/` 与 `app/core/` 开 `strict`，`app/services/dict.py` 的 14 处 `Column[...]` 类型误用配合阶段 2 拆分一并修，逐步全绿。
17. **加 CI**（当前完全没有）：`.github/workflows/ci.yml` 三档 —— `ruff check` → `mypy app/` → `pytest --cov`，PR 必过。
18. **加 `.pre-commit-config.yaml`**：ruff + ruff-format + mypy（对改动文件），让门禁前移到本地。
19. **测试补齐目标**：先把覆盖率从当前基线提到 40%（重点 Services + DAL），再对 `generate_code`、缓存失效、并发写做回归用例——这三处正是本次评审的高危点。

---

## 五、优先级总表

| # | 问题 | 级别 | 工作量 | 收益 |
|---|------|------|--------|------|
| P0-1 | psutil 未声明，干净环境装完即坏 | 阻断 | 10 分钟 | 项目可用 |
| P0-2 | 缓存只写不清，读脏 1 小时 | 阻断 | 2-4 小时 | 数据正确 |
| P0-3 | exec 无沙箱 → RCE | 阻断 | 半天（最小版 1 小时） | 安全 |
| P1-1 | 4 个重依赖 0 引用 + 漏声明 | 高 | 30 分钟 | 安装体积/失败面 |
| P1-5 | 真 bug QPushButton F821 | 高 | 5 分钟 | 消除崩溃 |
| P1-2 | StaticPool 单连接 + 7 线程写库无锁 | 高 | 1 天 | 稳定性 |
| P1-3 | Session 靠 GC 释放 | 高 | 半天 | 资源/事务确定性 |
| P1-4 | 553 行死代码 + 三套重复 UI + 1.8G 冗余产物 | 中 | 半天 | 可维护性 |
| P1-6 | DictService 832 行 + 绕过仓库层 | 中 | 3-5 天 | 可维护性 |
| P1-5 | 无 CI、1339 ruff / 109 mypy 错、3 个测试 | 中 | 持续 | 防回归 |

---

## 六、建议的执行顺序（最小风险路径）

```
第 1 天  → 阶段 0（止血）+ 阶段 3 的 ruff --fix + CI 落地
           ⇒ 项目可交付、门禁生效，后续所有改动被自动守住
第 2-3 天 → 阶段 1 的 P0-2 / P0-3 / P1-3（正确性与安全）
第 4-5 天 → 阶段 1 的 P1-2（并发）+ 补测试基线
第 2 周  → 阶段 2（Service 拆分 / SQL 下沉 / UI 去重）
        每次动 generate_code 前先跑 gitnexus_impact
```

**关键提醒**：阶段 2 触及 `generate_code`（15 个执行流依赖）与 DAL 层，属项目规范定义的高风险区，必须先用 GitNexus 做影响分析并分批提交；`ui/gui/threads/` 与 `DictService` 是所有并发问题的交汇点，阶段 1 完成后建议先跑一轮 GUI 手工回归再进入阶段 2。

---

## 附录：基线更新（2026-09-19 下午，修复进行中）

本文档第二节的实测数字是**评审当时**的快照。此后有两件事改变了几项指标，实际基线如下：

| 指标 | 评审时 | 现在 | 变化原因 |
|------|--------|------|----------|
| ruff 错误 | 1339（916 可修） | **1256（850 可修）** | 死代码删除（4 个文件）+ 在修复后的 venv 中重测 |
| mypy 错误 | 109 / 18 文件（checked 28） | **108 / 17 文件（checked 27）** | 同上（`app/core/service_registry.py` 已删） |
| pytest | collection error（psutil 缺失） | **3 failed** | psutil 修好后 3 个用例才真正执行——**该套件从未通过**，详见下条 |
| PyQt6 | QtWidgets 完全不可导入 | **可用**（runtime Qt 6.6.3） | 声明补 `<6.7` 上界，见下条 |

两处评审时未能发现、后续才暴露的问题：

1. **测试套件长期为红**：psutil 缺失把它表现为 collection error，掩盖了「3 个用例全部失败」的事实（`NameError: name 'Mock' is not defined`，在 HEAD 基线用 `git worktree` 可复现）。因此本报告"测试覆盖"一节应读作：**不是"只有 3 个用例"，而是"3 个用例且一个都没通过"**。
2. **PyQt6/Qt6 ABI 错配**：`PyQt6 6.6.1` 的元数据只声明 `PyQt6-Qt6>=6.6.0`（无上界），被解析到 6.11.0 → `QtGui.abi3.so: undefined symbol`，QtWidgets/QtGui 完全不可用；`PyQt6-Charts-Qt6` 同款。已显式声明 `<6.7` 并验证修复。
3. **`.venv` 是从 `/home/wtuj/tools/VMtool/...` 复制的**：35 个 console script 的 shebang 指向旧 venv，导致 `.venv/bin/pip`、`.venv/bin/pytest`、`source .venv/bin/activate` 全部作用在另一个 venv 上（已修复）。**本报告第三节的 ruff / mypy 数字当时也经旧 venv 执行**，工具版本相同故结论方向不变，但已按上表重测。

4. **第三节 P1-3 对 `next(get_db())` 的失败机制描述反了，特此更正**：报告写的是「会话不显式释放、靠 GC 兜底」，实测恰好相反——在 CPython 下，`self.db = next(get_db())` 里的生成器在语句结束、临时引用消失的瞬间就被回收，`finally: db.close()` **先于下一条语句执行**，所以会话是**刚创建就被关闭**，而服务随后仍在对一个已关闭的会话做操作（SQLAlchemy 会隐式重开事务）。真实后果是事务边界由引用计数决定，而不是连接泄漏。结论「会话生命周期不可靠」仍然成立，但方向必须按此更正；并且同样的代码在其他 Python 实现下行为可能不同。修复方式见 T5：`get_db()` 改为显式会话工厂 + 调用方负责释放。
