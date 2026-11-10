# compact-v1 数据重建与存储释放

本阶段按项目用途重建知识库，运行数据预算为 500 MiB，不含 Python 环境。它替代较早的数据整合建议稿；不保存完整词典文章、原始 JSON 或原料归档。

## 数据去向

原有公开 ID、全部姓名语言、写法、读音和姓名关系保留。JMdict 的同一词目多写法共享义项；Onomaverse 本名和本地化写法继续独立可查。数据库内部以整数引用和共享字符串减少重复。

Kaikki 的纯词形或异体记录变成写法到词目的映射，不各自保存一整份释义和元数据；词目的展开形式作为压缩明细提供。语义全文索引只覆盖真实义项、词源和姓名说明，采用 external-content，并只支持普通词项组合查询。

结构化知识按每 256 条共享压缩上下文，查询使用小型内存缓存。JMdict 保留英语释义作为语义桥接，其他释义语言不导入；姓名的跨语言覆盖不因此减少。保留字段由数据策略和构建报告记录。

Smith & Hall 保留英语词目、分义和拉丁语对应；Lewis & Short 保留词目、主要形式、词源和简明释义。verba 继续提供 Whitaker 形态分析，完整词典 JSONL 不再参与运行。

## 独立运行与重建

日常运行只需要数据库、jinmei 的两份 JSON、日语姓名 SQLite、verba 的必要代码与 Whitaker 数据、romkan、配置及来源说明。小型历史参考资料保留。

预构建数据通过 [compact-v1 Release](https://github.com/hikjesen/Project-Stephanus/releases/tag/compact-v1) 的 `stephanus-compact-v1-runtime.zip` 发布。解压到匹配版本的项目根目录，执行 `uv sync` 即可查询；无需重新下载原始资料。数据库位于包内 `data/stephanus.sqlite`，来源说明与必要原生后端一并提供。

`STEPHANUS_HOME` 指向包含 `data/`、`vendor/`、`resources.json` 和 `targets.json` 的资源根。工具没有指向旧库或完整原词典的回退路径。

普通 `fetch` 跳过按策略清理的资源。明确重建时，可执行 `stephanus fetch --include-pruned` 恢复原料，再在新的资源根中执行 `stephanus import`。已有运行库上的 `import` 只列出已索引来源，不覆盖数据库。滚动下载地址不保证恢复完全相同的历史快照。

构建入口 `scripts/build_compact_runtime.py` 用于从旧格式数据库生成独立候选根，调用 `src/stephanus/compact.py` 完成提取、词形转换和索引。候选已存在时拒绝覆盖。原料与参考工程清理前记录源码版本、来源、许可和署名。

## 本阶段一次验收与交付记录

`scripts/accept_compact_once.py` 只针对本阶段候选产物运行一次，报告存在时拒绝重跑。它以候选资源根启动新的 CLI/MCP 进程，覆盖姓名、分页、义项详情、欧洲关系、原生后端、英拉词库、词形 ID 和现成转换程序。

`scripts/install_compact_runtime.ps1` 仅在该报告通过且候选符合预算后切换并清理；所有删除、移动目标必须位于项目目录内。原有验收报告不覆盖、不重跑。候选临时副本不计入原始文件释放量。

构建、预算、验收与清理结果分别保存在本地 `data/reports/compact-build.json`、`compact-runtime-size.json`、`compact-acceptance.json` 和 `compact-cleanup.json`。清理报告区分运行数据、含 Python 环境的工作区总量及相对于初始快照的净减少量。

后续拉丁化调用设计见 [skill 设计稿](latinization-skill-design.md)。本轮不安装实际 skill。2026-11-11 按用户要求发布代码与预构建运行数据；数据库通过 Release 附件分发，Git 历史只包含代码和清单。
