# VMtool P0/P1 修复 — 执行报告

> 2026-09-19 · 团队 `vmtool-p0-p1-remediation` · 29 个任务 · 6 名成员
> 配套文档：`ARCHITECTURE_REVIEW.md`（本次工作的输入——架构评审与四阶段方案）

---

## 一、最终结论

**可交付。** T29 收官复评给出 `verdict=pass`：核心 P0/P1 修复经多轮独立验证全部成立、无回退，三项「必须动作」已全部闭合。

| 收官前必须动作 | 状态 |
|---|---|
| F2 `batch_import` 跨线程共享 Session | ✅ 已修（T28），精确计数 240/240 |
| F3 沙箱白名单绑定名绕过 | ✅ 已修（T27），13 条载荷独立复测无残余绕过 |
| F1 未跟踪文件导致干净克隆不可用 | ✅ 已转为可执行清单（见第二节） |

---

## 二、提交前必读（最重要的一节）

**现状：本轮全部工作 0 commit，所有改动都在工作树中（`git log -1` 仍是 552f4ea）。**

### 2.1 必须 `git add` 的 10 个未跟踪文件

```
vm-tool/ui/gui/threads/service_factory.py      ← 关键：被已跟踪模块强依赖
vm-tool/tests/unit/conftest.py                 ← T24 的唯一隔离装置
vm-tool/tests/unit/test_cache_invalidation.py
vm-tool/tests/unit/test_concurrent_writes.py
vm-tool/tests/unit/test_dependency_declarations.py
vm-tool/tests/unit/test_filter_import_concurrency.py
vm-tool/tests/unit/test_gui_thread_conventions.py
vm-tool/tests/unit/test_isolation_guard.py
vm-tool/tests/unit/test_session_ownership.py
vm-tool/tests/unit/test_thread_service_ownership.py
```

**为什么这条是硬性的**：`service_factory.py` 被**已跟踪**的 `ui/gui/threads/__init__.py` 与 `base_batch_thread.py` 强依赖。T29 实测：删掉未跟踪文件后 `import ui.gui.threads` → `ModuleNotFoundError`，pytest 从 107 掉到 27。也就是说，**用 `git add -u`（只加已跟踪文件的改动）提交会推出一个本地正常、克隆即坏的仓库**。

### 2.2 不要混入

- `.agent-teams/`（团队运行时状态，4 个条目）
- `ARCHITECTURE_REVIEW.md`、`EXECUTION_REPORT.md`（过程文档，是否入库由你决定）

### 2.3 提交后自检

```bash
git ls-files vm-tool/tests/unit | wc -l   # 应为 9（add 之前是 2）
```

### 2.4 建议的提交切分（4 组）

1. **阶段 0 止血与依赖**：`pyproject.toml`、`requirements.txt`、`vmtool.py`、`.gitignore`、`.pre-commit-config.yaml`、`.github/workflows/ci.yml`、桩测试修复
2. **会话生命周期 + 缓存 + 并发**：`database.py`、`migration.py`、`cache.py`、`compatibility.py`、`services/*`、`cli/__main__.py` + 3 个测试
3. **exec 沙箱**：`code_generator.py`（含 T27 的绕过修复）+ 对应测试
4. **GUI 线程归属与测试隔离/门禁**：`ui/gui/threads/`（含 `service_factory.py`）、4 个 tab、`pyqt_app.py`、`conftest.py` + 5 个测试 + T9 的格式化面

⚠️ `dict.py` / `weight.py` / `database.py` / `pyqt_app.py` / `code_generator.py` / `test_code_generator.py` 被多个任务共同修改，**无法按 hunk 干净切分**——这 4 组是逻辑分组，不是可机械执行的 `git add -p` 脚本。

---

## 三、终态指标（对比评审基线）

| 指标 | 评审时 | 现在 |
|---|---|---|
| 测试 | 3 个用例，**一个都不过**（collection error 掩盖） | **107 passed / 0 failed** |
| ruff | 1718 错（T4 收敛 select 后） | **0** |
| ruff format | 80 文件待格式化 | 92 files already formatted |
| mypy | 109 错 / 18 文件 | 119 错 / 18 文件（CI 档仍 continue-on-error） |
| GUI | PyQt6 ABI 崩溃，QtWidgets 完全不可导入 | **可导入可用** |
| CLI | `--help` 抛 TypeError（typer 漂移） | **12 个子命令可用** |
| 并发写库 | 静默丢写 + 进程级 segfault（exit 139） | 精确计数全落库，无异常 |
| exec 沙箱 | `exec(content, {}, local_vars)` 任意代码执行 | AST 白名单 + 沙箱命名空间，无已知绕过 |
| 缓存 | 写后读到 1 小时前的旧值 | 写路径全收敛失效，ttl 60s 兜底 |
| CI 门禁 | 无 | ruff + pytest 硬失败（已实测会拦人） |

---

## 四、已交付的修复（对应原评审的问题编号）

| 原问题 | 修复 |
|---|---|
| P0-1 psutil 未声明 | 已声明；并建立**依赖声明一致性检查**（T21），使同类缺陷不再靠人工发现 |
| P0-2 缓存只写不清 | 写路径集中失效（`dict.py:66` + `weight.py:53`），ttl 3600→60 |
| P0-3 exec 无沙箱 | AST 结构白名单 + 沙箱命名空间；**并在收官评审发现绕过（T11-F3）后修根因（T27）** |
| P1-1 4 个重依赖 0 引用 | 已移除；PyQt6/Qt6 运行时显式钉 `<6.7` 修复 ABI 错配 |
| P1-2 StaticPool 单连接 + 7 线程 | NullPool + 每会话独立连接 + WAL + busy_timeout |
| P1-3 Session 靠 GC | `get_db()` 改显式会话工厂；DAL→Core 反向依赖清零 |
| P1-4 死代码与冗余产物 | 4 文件 629 行 + 仓库根冗余产物已清 |
| P1-5 无 CI / 1339 ruff / 真 bug | CI 落地；ruff 归零；另修出 2 个真 bug（`vmtool.py` 的 `_check_dep` NameError、`refreshable_tab.py` 的 QPushButton） |
| P1-6 DictService 职责膨胀 | **未做**（阶段 2，本轮范围外） |
| 本轮新发现并修复 | GUI 7 线程共享会话致**静默丢写**与 **segfault**（T19/T25）；`batch_import` 同款问题（T28）；测试套件从未通过（T12）；`.gitignore` 吞掉整个 tests 树（T13）；`click` 未声明（T21）；`CalculateWeightThread` 丢失信号声明（T22→T25） |

---

## 五、遗留台账（全部未修，**不阻断提交**）

| 编号 | 内容 | 建议 |
|---|---|---|
| T19-F1 / T11-F5 | 特殊字符批量添加自 HEAD 起必抛 TypeError（`special_tab.py:249` → `AddBatchThread(is_special=True)`），**用户可点功能长期坏** | **建议单独立项**（本轮范围外，但它是坏的用户功能） |
| T23-A3 | 导入路径测试只覆盖 `import_from_txt`；实测只移除 `import_from_csv` 的 finally 仍全绿 → csv/json/thuocl 路径的会话释放无测试护住 | 参数化补测 |
| T23-A2 / T11-F9 | `close()` 只置空 `self.db`，`self.repo` 仍持同一会话 → close 后误用**静默重连** | 一行修复：`self.repo = None` |
| T11-F4 | 线程信号门禁只扫 `*Thread`；另有 5 个非线程类 declare+emit 却无保护（实测删 `sidebar_nav` 的信号门禁仍 6 passed） | 扩扫描根 |
| T11-F6 | `*.db-wal` / `*.db-shm` 未忽略（T8 引入 WAL 的副产品） | 一行修复 |
| T11-F11 | mypy 实测 119/18，而 `ci.yml` 注释仍写 108/17 | 一行修复（改注释） |
| T11-F12 | `pyinstaller` / `pre-commit` 已装但任何 extra 都未声明 | 加进 extra |
| T11-F13 | `README.md:143` 仍写「main.py # 程序入口」；根 `vmtool.spec` 未忽略 | 文档同步 |
| T11-F14 | `confirm_python_mode_rules()` 有定义有单测但生产代码 **0 调用点** | 三选一：接线 / 删除 / 显式登记 |
| T11-F15 / T6 | 沙箱无执行超时（`range(10**12)` 可长时间占用） | 阶段 2 |
| T23-A1 | `migration.py` 本地常量不再响应 `MAIN_DICT`/`OUTPUT_FILE` 环境变量（但那三个函数无产品调用方） | 可接受 |
| — | 覆盖率 TOTAL 19%（filter/stats/thuocl/weight 为 0%），刻意未加 `--cov-fail-under` | 阶段 3 |
| — | mypy 档在 CI 仍 `continue-on-error` | 阶段 3 收紧 |

---

## 六、复盘：captain 的 7 次错误

本轮 29 个任务里，有 **7 次故障的根因是 captain 的契约缺陷**，不是成员能力问题。记录在此，供下次同类工作参考。

### 6.1 六次契约错误（同一根因）

| # | 任务 | 错误 | 后果 |
|---|---|---|---|
| 1 | T3 | 验收写成「`pytest -q` → 3 passed」，而该套件在 HEAD 基线就是 3 failed（psutil 缺失把它伪装成 collection error） | 任务无法完成，按 failed 登记；后续由 T10 独立裁决为「实质通过」 |
| 2 | T4 | 验收写「`git diff --stat -- app/ ui/` 为空」，但工作树是 6 人共享的，T2 的改动会永久留在树里 | 该标准在共享工作树上永不可能成立 |
| 3 | T5 | verify 要求 `next(get_db())` 全仓归零，但清单只点了 2 个文件，实测另有 12 处 | 成员按同一原则机械等价替换才达成验收 |
| 4 | T16 | 验收标准点名 `CompatibilityLayer`，但 inScope **不含** `app/core/compatibility.py`——**要你改的文件，却禁止你改** | 全部工作完成后被平台拒绝交付，只能新建 T20 承接 |
| 5 | T19 | 验收要求新增 pytest 用例与门禁，但 inScope 只声明了 `ui/gui/` | 两个新测试文件无法列入 changedPaths，只能靠 output 追认 |
| 6 | T9 / T4 | 我引用的 ruff 基线 1256 是 T4 收敛 `select` **之前**的数字；真实基线是 1718 | 成员发现并纠正，避免了按错误目标收工 |

**共同根因**：我按「理想仓库」写契约——假设环境干净、测试是绿的、每个任务彼此隔离。而真实仓库是：测试从未通过、环境指向另一个 venv、6 个成员共用一棵工作树。**契约里的清单会过时，跨目录的 diff 判据在共享树上失效，而 inScope 漏掉测试路径会让成员被迫在「做不到」和「越界」之间二选一。**

### 6.2 一次流程错误

**T22 判定 needs_revision 后，我手工去改依赖、手工新建 repair 任务，两次都被拒。** 原因是框架本身会在 review 失败时自动创建 round-2 repair + round-2 review，并自动重接所有待办下游闸门。我读过协议里这条，但没有在动手前先看任务图的真实状态。

**与「dead task 阻塞下游」是同一个根源**：T16 失败后它阻塞了 t17/t9/t10；t22 失败后同样。两次都是「凭记忆推断图的状态」而没有先 `status`。

### 6.3 三条可复用的教训

1. **写验收标准时，先问「这个判据在当前环境里可能成立吗」**——不是「在理想环境里应该成立吗」。涉及共享工作树、共享数据库、未提交状态时尤其如此。
2. **inScope 必须包含该任务将要触碰的每一个路径**，特别是测试文件。这条在本轮被违反了 3 次。
3. **任何任务失败后，第一件事是查图**（框架是否已补 loop、哪些待办任务依赖这个死任务），而不是先动手修。

### 6.4 反过来，成员们纠正了我

- gui-engineer 指出我给的构造点清单有误（`special_tab.py:120` 不是构造点，且漏了 `danger_zone_panel.py` 两处）
- T9 指出我引用的 ruff 基线过时
- T5 / T7 主动上报合同口径与边界外的事实，而不是沉默照做

**我提供的行号、数字、清单都是「输入」，不是免检结论**——这一点上成员做对了。

---

## 七、这次工作最有效的三个机制

1. **独立验证者写下新证据，而不只是重跑命令。** T10 自建 14 条脏读探针、30 条逃逸载荷、真实 QThread 并发测试，还独立复现了修复前的 segfault——它找到了实现者全都漏掉的 `click` 未声明缺陷（与最初 P0-1 同类）。
2. **「用变异证明用例有效」成为团队共识。** 从 T7 起，几乎每个实现任务都被要求：回退修复 → 用例必须失败 → 还原后 sha256 逐字一致。这挡住了「测试通过」与「测试有意义」之间的差距。
3. **评审要求自建反例，而不是采信实现者结论。** T22 用 9 个线程文件与 HEAD 做 AST 对比，才发现 `CalculateWeightThread` 丢了 3 个信号声明——而当时 107→69 个用例全绿。**「69 passed 但功能坏了」这种形态，只有跟基线对比才能发现。**
