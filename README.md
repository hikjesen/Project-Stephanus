# Project Stephanus

面向创作者的本地姓名与词典查询工具。首版提供日语姓名、同音写法、日语词义、拉丁词典、欧洲姓名关系及罗马字工具；创作与名称拉丁化 skill 后续另做。

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

本机数据已准备完成，可以直接查询。首次从 GitHub 克隆到新机器时，先按下方“资源获取与导入”下载数据并构建索引，再执行查询。

使用查询返回的 `id` 读取详细记录与姓名关系：

```powershell
uv run stephanus entry 'onomaverse:john-fn'
uv run stephanus related 'onomaverse:john-fn' --limit 10
```

`--limit` 默认 20，`--offset` 默认 0。`mode` 可取 `auto`、`text`、`reading`、`meaning`。姓名类别可用 `--category given` 或 `--category surname`；来源保留其自身类别信息。

JSON 输出使用 UTF-8。主要字段为 `id/source/kind/text/language/readings/description/extra`。不同来源独立返回，同名记录不会被强制合并。普通检索使用简单的精确、前缀、释义匹配顺序，不计算综合评分。

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

汉字姓名先查读音，再将假名交给 `transliterate_name`。英译拉丁查询使用 `lookup_words(language="la", source="verba", mode="meaning")`。

## 资源获取与导入

```powershell
uv run stephanus fetch --group sources
uv run stephanus fetch --group data
uv run stephanus fetch --group references
uv run stephanus import
```

`resources.json` 同时保留本次版本的资源地址及历史取得状态；`data/import-summary.json` 记录实际导入结果。下载仅在本地文件也存在时跳过，因此克隆代码到新机器后仍能取回资源。已有备用来源的失败端点沿用记录中的 `resolved_by`；数据优先按清单快照复现，不依赖重新查询最新发布版。

不进行下载后的全库复查或哈希校验。失败资源登记错误后继续；显式指定 `fetch --only ID` 可重新获取失败资源，不会自动循环重试。

本次发布的备用端点收集脚本为 `scripts/acquire_supplements.py`，用于 API 限流或某个下载端点失败时的已知替代来源。源码保持上游版本，业务逻辑通过适配器复用。

- JMnedict、JMdict、KANJIDIC2、欧洲姓名 CSV、Kaikki 和 CLTK 进入统一 SQLite 索引。
- jinmei-dict 直接读取原有 JSON；Japanese Personal Name Dataset 直接查询其 SQLite。
- verba 通过原有 CLI 提供词典及形态分析。
- python-romkan 直接加载源码模块，避开旧安装脚本对已移除的 `imp` 的依赖。
- Kuroshiro、WanaKana、Collatinus 与应用项目保留作后续接入和实现参考。
- Kaikki 共享源仅保留压缩包；流式提取日语、拉丁语到 `ja-la.jsonl`，不保存全语言解压副本。

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

`scripts/accept_once.py` 使用实际数据和 stdio MCP 集中执行一轮功能验收，结果保存到 `data/acceptance.json`。报告存在时拒绝重复执行。不测试语言学准确率，不生成评分或多轮评测流程。

裸 `dict` 注解导致的 MCP 结构化输出缺失已修复：七个接口均显式声明 `dict[str, Any]` 和 `structured_output=True`。原整套验收没有重复执行；此次对修复后的结构化输出做了一次单独确认，结果见本地 `data/mcp-output-fix.json`。

## 仓库与本地资源

GitHub 仓库包含项目代码、说明、配置模板、资源清单和复现工具。`data/`、`vendor/`、`.venv/` 保留在本地，不进入 Git 历史。

`data/` 包含原始压缩包、筛选后的词典及生成索引。`vendor/` 包含第三方原版源码；jinmei-dict、verba、python-romkan 会直接用于运行，其余项目主要供导入、重建或后续参考。

常规查询需要数据库及已接入后端。原始压缩包和参考应用源码主要用于重建及后续开发；本次不会自动清理这些文件。存储占用及各部分用途见 `STORAGE.md`。
