# 最小化读取原则
## 一、为什么需要最小化读取

- 上下文窗口有限
- 关键信息被稀释，回答准确性下降
- 响应延迟显著增加

**目标**：用最少文件内容，获取足够完成任务的信息。

## 二、核心原则
### 原则 1：先搜后读
- 使用 `grep` / 全局搜索 / 语义搜索定位相关代码，而不是盲目打开文件
- 只在确认文件包含必要信息再读取其内容

### 原则 2：片段优先
- 优先使用 **行号范围读取**（如 `read_file offset/limit`）
- 优先读取函数 / 类定义，而非整个文件
- 利用代码大纲（symbols / outline）快速定位

### 原则 3：结构化摘要优先
- 先查看目录树、文件列表、导出符号列表
- 再决定是否需要深入具体实现

## 三、具体操作指南

### 推荐做法

| 查找函数定义位置 | `grep "func name" --include="*.go" -n` 后按需读取行范围 |
| 了解文件结构 | 使用 `read_file` 时加上 `limit` 参数，只取前 100 行 |
| 查看类有哪些方法 | 依赖 LSP 的 `textDocument/documentSymbol`，而非读完整文件 |
| 检查导入依赖 | 只读取文件头部 import 区域 |
| 修改特定函数 | 先 `grep` 定位，再读取函数所在的行范围（如 45-80 行） |
| 理解模块作用 | 优先读取 `README`、注释头、导出符号列表 |

### 错误做法

`read_file` 整个 `main.go`
读取整个 `node_modules` 下的库文件
同时读取多个文件
使用通配符 `cat *.js` 输出全部

## 四、实操示例
### 场景：修复 `api/user.go` 中 `CreateUser` 函数的 bug
#### 低效流程

1. read_file api/user.go           # 读取整个 800 行文件
2. read_file models/user.go        # 读取整个 500 行模型文件
3. read_file services/auth.go      # 又读一个 600 行文件

**结果**：读取大量文件,还未开始分析问题。

#### 最小化流程
1. grep "func CreateUser" api/user.go -n
   → 返回：api/user.go:245
2. read_file api/user.go offset=240 limit=40   # 只读函数及周边
3. 发现调用 models.NewUser，执行 grep "func NewUser" models/user.go -n
   → 返回：models/user.go:78
4. read_file models/user.go offset=75 limit=30
5. 分析完成，无需读取其他无关部分

**结果**：仅读取 70 行代码，约 200 token，上下文空间充裕。

## 五、常用命令速查

| 操作 | 命令示例 |
|------|----------|
| 搜索关键词 | `grep "pattern" --include="*.ext" -r .` |
| 只读文件头部 | `read_file file.go limit=50` |
| 读取指定行范围 | `read_file file.go offset=120 limit=80` |
| 列出目录结构 | `list_dir --depth=2` |
| 获取符号大纲 | 依赖 IDE 提供的 LSP 功能，或 `ctags` 输出 |

## 六、检查清单
每次请求读取文件前，问自己：

- [ ] 能否通过**搜索**先定位到具体位置？
- [ ] 能否只读其中一部分？
- [ ] 是否真的需要文件的**全部内容**？
- [ ] 这个文件是否属于**第三方库**或**无关内容**？尽量不读。
