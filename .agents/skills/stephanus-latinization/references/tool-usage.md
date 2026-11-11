# 工具与运行指南

首次需要调用查询时读取。七个只读 MCP 工具和 CLI 都使用现有 Service，不增加独立命名服务。

## 从项目接入

skill 位于项目根的 .agents/skills/stephanus-latinization/，从该目录向上三层取得项目根目录。先识别宿主暴露的 Stephanus 工具；命名空间前缀可以不同，以下表中的实际功能名为准。

MCP 未加载或连接不可用时，在项目根用现有虚拟环境执行 CLI。查询返回空列表时继续换材料或方法，不通过切换 MCP／CLI 重复同一次查询。发生连接错误的调用如尚未取得结果，可通过 CLI 完成该查询。

Windows PowerShell 示例（工作目录为项目根）：

~~~powershell
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
& '.venv/Scripts/python.exe' -m stephanus.cli names '古明地' --source jmnedict --limit 5
~~~

其他系统使用项目虚拟环境对应的 Python。已有运行数据不需要 fetch/import；环境尚未安装时按项目 README 准备虚拟环境和 compact-v1 预构建包，不在一次命名中自动重建数据。资源根另置时沿用当前 STEPHANUS_HOME；它指向数据与 vendor 资源，不改变代码位置。案例仍存于当前项目根的 data/examples/。

## 七个工具与 CLI 对应

下表 CLI 参数均接在“项目虚拟环境 Python -m stephanus.cli”之后。查询／文本为位置参数；MCP 的 identifier 对应 CLI 的位置 ID。

| MCP 功能名 | 现有 CLI | 主要用途 |
|---|---|---|
| stephanus_list_sources(include_resources=false) | sources；需要时加 --include-resources | 覆盖和后端状态未知时查看，不要求每轮调用 |
| stephanus_search_names(query, language, category, source, mode, limit, offset) | names QUERY，加对应 --language / --category / --source / --mode / --limit / --offset | 按写法、读音或释义找姓名 |
| stephanus_lookup_words(query, language, source, mode, limit, offset) | words QUERY，加对应选项；没有 --category | 词汇、汉字与英拉词目 |
| stephanus_find_related_names(identifier, relation, limit, offset) | related ID，加 --relation / --limit / --offset | 已有变体、相似、文化对应或转写关系 |
| stephanus_get_entry(identifier) | entry ID | 义项、词源、词形、历史材料及来源 |
| stephanus_transliterate_name(text, scheme) | transliterate TEXT，加 --scheme | 现代罗马字基线，先解析汉字读音 |
| stephanus_analyze_latin(text, limit) | analyze TEXT，加 --limit | 已有拉丁词形的分析线索 |

mode 支持 auto、text、reading、meaning；列表默认 limit=20、offset=0，沿 has_more／next_offset 按需翻页。limit 是检索分页大小，不是命名输出的数量上限；完整候选按[正式入口](../SKILL.md)至少四个、无固定上限。不必穷尽全部检索结果。罗马字 scheme 支持 hepburn、kunrei、hiragana、katakana；它不提供传教士历史拼写，也不直接处理汉字。

英拉语义入口：

~~~powershell
& '.venv/Scripts/python.exe' -m stephanus.cli words 'affection' --language la --source verba --mode meaning --limit 5
~~~

MCP 对应参数为 query="affection", language="la", source="verba", mode="meaning"。先读列表摘要，对实际采用的少量条目再取详情。

## 怎样解释结果

- 列表含 id、source、kind、text、language、category、readings、description 和 extra.match；description 最多 240 字。自动检索依精确写法、读音、前缀及释义等方式返回，不生成综合评分。
- get_entry 的 extra.knowledge 保留 senses、etymology、forms、related_words、attestations；部分条目还含 lemma_links 或 supplements。原文章、用例全文和原始 JSON 已移除，缺字段不是“词源不存在”的结论。
- extra.provenance 给出来源、版本与定位。ID 使用实际返回的值，不凭姓名拼出一个 ID 再当作已命中。
- Medieval 与 Onomaverse 的规范名常为 language="und"。不要一开始只过滤 la／it 而漏掉它们；用详情中的 ORIGIN、AREA、CASE、日期及本地化记录判断实际用途。
- 规范名与文献实录分别读取。Amanda 作为规范名、Amandine 作为实际写法不能互换；gen／dat 等格形式也不能直接冒充主格姓名。
- find_related_names 的 historical_variant、similar、cultural_equivalent、transliteration 等标签按实际类型说明，不一概称为同源。Onomaverse 的词义正文并不完整，按抽象概念搜索不会覆盖所有姓名。
- analyze_latin 可能返回多种分析。结合语境和姓名资料选用，不靠词形分析单独证明姓名使用，也不要求它识别新造名。
- 本地没有命中时，可换变体、概念或参考资料，并保留创作入口；不因此宣称某名字历史上不存在。少量文献记录或频率补充也不足以证明全球稀有度。

## 配置维护

本机 Codex 使用项目级 .codex/config.toml 中的 mcp_servers.stephanus，复用已有虚拟环境的 stdio 命令、项目 cwd、STEPHANUS_HOME 和 UTF-8 环境。该文件含本机路径，受 Git 忽略；通用客户端仍可使用仓库的 mcp-config.json 模板。

skill 与 MCP 分别加载：写入配置不等于当前聊天已经暴露工具。若本会话尚无 Stephanus MCP，先用上述 CLI；重新载入 Codex 后使用 MCP。只有环境配置任务才修改连接设置，普通命名不写客户端配置。
