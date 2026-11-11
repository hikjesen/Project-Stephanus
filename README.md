# Project Stephanus

面向创作者的本地姓名与词典查询工具。提供日语姓名、同音写法、日语词义、拉丁词典、欧洲姓名关系及罗马字工具；正式的名称转译入口为 [Stephanus 名称转译 skill v1.0.1](.agents/skills/stephanus-latinization/SKILL.md)。

数据采用 compact-v1，用途、重建及该阶段交付记录见 [精简运行库说明](docs/compact-runtime.md)。skill 使用既有数据库、七个只读 MCP 工具及同源 CLI；[设计演进记录](docs/latinization-skill-design.md)保留此前决策与案例复盘。

2026-11-10 本阶段交付：运行数据约 **475.62 MiB**；整个项目含 Python 环境约 **522 MiB**，相对初始资源快照净减少 **8.993 GiB**。本阶段唯一一次验收的 14 项均通过。数字按文件长度统计，后续少量代码、报告和缓存会产生小幅增量。

## 名称转译 skill

skill 源码位于本项目的 .agents/skills/stephanus-latinization/，由项目内 Codex 自动发现，也可显式调用：

~~~text
使用 $stephanus-latinization 为这个日语姓名创作完整别名；先交流我希望保留的关联倾向。
~~~

首版面向日语原名，目标为拉丁语或罗曼语族风格。倾向未明确时先提供至少三个有效意象方向；历史拼写路线默认保留，不占意象选项。完整姓名至少四个、无固定上限，至少一条回应用户选定、至少两条从其外的独立材料出发，并含完成目标语言适配的历史路线。基础名优先生僻、有辨识度的形式，后续修饰可选且与原版合计一个候选。

完整姓名以外，可额外给零个或一个有明确象征含义的无姓氏单人名，不要求必有，也不占完整姓名及独立完整候选的数量。只有局部修改或另定范围时按用户要求处理。

日常查询 MCP 优先、CLI 备用，具体映射见 [工具指南](.agents/skills/stephanus-latinization/references/tool-usage.md)。每轮结果自动保存到被 Git 忽略的 data/examples/，使用 [精简案例模板](.agents/skills/stephanus-latinization/assets/case-template.md)；[古明地恋摘要](.agents/skills/stephanus-latinization/references/worked-example.md)演示完整流程，原始案例与复盘仍保留在 docs/examples/。

## 使用

环境为 Python 3.12，项目依赖通过 uv 管理。在项目目录执行：

```powershell
uv sync
uv run stephanus sources
uv run stephanus names '佐藤' --language ja --limit 5
uv run stephanus names 'あおい' --mode reading --limit 10
uv run stephanus names 'John' --source onomaverse --limit 5
uv run stephanus words '光' --source jmdict --limit 5
uv run stephanus words 'light' --mode meaning --language ja --limit 5
uv run stephanus words 'courage' --language la --source verba --mode meaning
uv run stephanus words 'virtus' --language la --source kaikki --limit 5
uv run stephanus transliterate 'しんじ' --scheme hepburn
uv run stephanus analyze 'amavit'
uv run stephanus targets
```

本机数据已准备完成，可以直接查询。其他机器优先使用 [compact-v1 Release](https://github.com/hikjesen/Project-Stephanus/releases/tag/compact-v1) 中的预构建数据库与运行数据包：

1. 克隆仓库或下载对应标签的源码。
2. 下载 [stephanus-compact-v1-runtime.zip](https://github.com/hikjesen/Project-Stephanus/releases/download/compact-v1/stephanus-compact-v1-runtime.zip)，解压到项目根目录，保留其中 `data/`、`vendor/` 等目录结构。
3. 执行 `uv sync`，随后直接查询或启动 MCP，无需 fetch/import。

也可以将运行包解压到独立目录，用 `STEPHANUS_HOME` 指向该目录。只有需要从原始资料重建时，才执行下方“资源获取与导入”的命令。

使用查询返回的 `id` 读取详细记录与姓名关系：

```powershell
uv run stephanus entry 'onomaverse:john-fn'
uv run stephanus related 'onomaverse:john-fn' --limit 10
```

`--limit` 默认 20，`--offset` 默认 0。`mode` 可取 `auto`、`text`、`reading`、`meaning`。姓名类别可用 `--category given` 或 `--category surname`；来源保留其自身类别信息。

JSON 输出使用 UTF-8。主要字段为 `id/source/kind/text/language/readings/description/extra`。不同来源独立返回，同名记录不会被强制合并。列表只返回最多 240 字的摘要及 `extra.match`；用 `entry` 取得 `extra.knowledge` 中的义项、词源、词形、相关词、历史资料及来源定位。原始 JSON、词典文章和用例全文不再保留。普通检索使用精确写法、精确读音、前缀和释义顺序，不计算综合评分。

纯词形仍能按原 ID 查询，其详情指向所对应的词目与语法标签；释义查询只返回真实词目，避免大量屈折形式重复占据结果。`sources` 默认返回简要覆盖信息，完整资源清单使用 `sources --include-resources`。

## MCP

```powershell
uv run stephanus serve
```

服务通过 stdio 提供以下七个只读工具：

- `stephanus_list_sources`
- `stephanus_search_names`
- `stephanus_lookup_words`
- `stephanus_find_related_names`
- `stephanus_get_entry`
- `stephanus_transliterate_name`
- `stephanus_analyze_latin`

`mcp-config.json` 是可移植的配置模板：将 `REPLACE_WITH_ABSOLUTE_PROJECT_PATH` 改为项目绝对路径，再把 `stephanus` 服务加入支持 stdio MCP 的客户端。本机已有可直接使用的 `mcp-config.local.json`，它不进入 Git 仓库。

本机 Codex 已另以项目级 .codex/config.toml 注册 stephanus，复用已有虚拟环境、项目 cwd、STEPHANUS_HOME 与 UTF-8 环境；该文件受 Git 忽略。其他机器若使用 Codex，可按下例在本项目配置，替换绝对路径后加载受信任项目：

~~~toml
[mcp_servers.stephanus]
command = "uv"
args = ["--directory", "REPLACE_WITH_ABSOLUTE_PROJECT_PATH", "run", "stephanus", "serve"]

[mcp_servers.stephanus.env]
PYTHONIOENCODING = "utf-8"
PYTHONUTF8 = "1"
~~~

skill 与 MCP 分别加载。当前聊天尚未暴露工具时可先复用 CLI，重新载入 Codex 后使用 MCP；无需安装全局 skill。

汉字姓名先查读音，再将假名交给 `transliterate_name`。英译拉丁查询使用 `lookup_words(language="la", source="verba", mode="meaning")`。

## 资源获取与导入

```powershell
uv run stephanus fetch --group sources --include-pruned
uv run stephanus fetch --group data --include-pruned
uv run stephanus fetch --group references
uv run stephanus import
```

上面的命令用于明确恢复构建原料；会临时占用较多空间。`resources.json` 保存资源地址、版本、源码 revision、历史取得状态和 `storage_state`。普通 fetch 跳过 `pruned` 项，防止清理后的项目被自动扩回原体积。`--include-pruned` 或显式 `--only ID` 才恢复相应原料和完整参考源码。已有运行库上的 import 只列出已索引来源；从头重建请使用新的资源根。原始输入经临时旧格式索引转换成 compact-v1，临时索引随后删除；恢复的下载原料不会被 import 隐式删除。

不进行下载后的全库复查或哈希校验。失败资源登记错误后继续；显式指定 `fetch --only ID` 可重新获取失败资源，不会自动循环重试。

本次发布的备用端点收集脚本为 `scripts/acquire_supplements.py`，用于 API 限流或某个下载端点失败时的已知替代来源。源码保持上游版本，业务逻辑通过适配器复用。

- JMnedict、JMdict、KANJIDIC2、欧洲姓名 CSV、Kaikki 和 CLTK 进入统一 SQLite 索引。
- jinmei-dict 直接读取原有 JSON；Japanese Personal Name Dataset 直接查询其 SQLite。
- verba 的英拉和拉英知识已提取至紧凑数据库；形态分析继续调用原有 Whitaker 引擎与约 6 MiB 的必要数据。
- python-romkan 直接加载源码模块，避开旧安装脚本对已移除的 `imp` 的依赖。
- Kuroshiro、WanaKana、Collatinus 与应用参考工程的完整副本已列入本阶段清理范围，保留取得入口、版本和署名说明。
- Kaikki 的姓名、义项、词源和词形映射提取完成后，压缩总包与 `ja-la.jsonl` 均删除。

Medieval CSV 中无法直接确定文献用语的记录使用 `language="und"`，原有 `ORIGIN/AREA/CASE` 等字段保存在 `extra` 中。Onomaverse 本名记录同样保留为 `und`，本地化记录使用其语言代码。未指定语言时可以联合查询全部来源。

历史资料、模型文档和在线资源位于本地资料库，尚未包装成独立历史转写工具。Behind the Name 等需要验证码或账号的额外数据保留获取入口。保留上游 README、许可与署名说明；具体来源见清单和各项目文件。

## 输出语言扩展

`targets.json` 是开放的输出目标注册表，首版登记拉丁语。每个目标声明 `code/name/capabilities/sources`。可用能力包括 `name_lookup/lexicon_lookup/name_relations/transliteration/morphology`。

新增目标语言时：

1. 在来源适配器中读取新数据，返回相同的宽松记录结构；需要联合搜索的内容写入现有索引。
2. 为记录填写语言代码，将特殊字段放入 `extra`。
3. 使用 `TargetAdapter` 和 `register_target()` 增加目标及能力；需要专用程序时在适配器内调用它。

工具的 `language` 参数直接接受语言代码，不依赖固定枚举。已有索引中的欧洲语言资料也可直接按代码查询。新增目标无需为每个语言复制一套 MCP 工具。日语输入处理仍保留在日语适配器中。

资源根目录可通过 `STEPHANUS_HOME` 环境变量调整；复制完整资源库后不要求联网即可查询。

## 一次验收

旧 MVP 的 `scripts/accept_once.py` 和 `data/acceptance.json` 保持历史状态，不重跑。compact-v1 新产物的唯一一次验收由 `scripts/accept_compact_once.py` 在独立候选资源根上执行，结果写入 `data/reports/compact-acceptance.json`。报告存在时拒绝重复执行。不测试语言学准确率，不生成评分或多轮评测流程。

裸 `dict` 注解导致的 MCP 结构化输出缺失已修复：七个接口均显式声明 `dict[str, Any]` 和 `structured_output=True`。原整套验收没有重复执行；此次对修复后的结构化输出做了一次单独确认，结果见本地 `data/mcp-output-fix.json`。

## 仓库与本地资源

GitHub 仓库包含项目代码、说明、配置模板、资源清单和复现工具。数据库与必要运行文件通过 Release 附件提供；`data/`、`vendor/`、`.venv/` 不进入 Git 历史。运行包不含 Python 环境、个人配置或本机路径，使用 `scripts/package_runtime.py --output ZIP_PATH` 可从已安装数据生成。

`data/` 保存紧凑数据库、必要原生姓名 SQLite、报告、来源说明与少量历史参考。`vendor/` 只保留 jinmei JSON、verba 的必要代码与 Whitaker 数据，以及 python-romkan 模块。

运行数据预算为 500 MiB，不含 Python 环境。初始资源快照见 `STORAGE.md`；本次实际体积、删除文件及净释放量见 `data/reports/compact-cleanup.json`，不再保留旧库、原料归档或永久候选副本。
