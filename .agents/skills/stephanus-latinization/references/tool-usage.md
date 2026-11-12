# 工具与运行指南

首次需要调用查询时读取。七个只读 MCP 工具和 CLI 都使用现有 Service，不增加独立命名服务。ChatGPT 通过 Wan MCP 转发，Codex 按原有本地 MCP／CLI 流程运行。

## ChatGPT 对话环境：通过 Wan MCP 转发（优先）

仅在用户**主动点名调用 Stephanus 名称转译 Skill** 时使用下述路径。普通翻译、音译、取名或拉丁语问题不自行进入此流程。运行数据已在腾讯云 `/opt/stephanus` 部署；ChatGPT 无需安装 Python 依赖或下载数据库，默认也不在服务器执行 shell。

固定定位：
- Wan MCP 服务器：`server="tencent-sv"`；
- 下游 MCP 别名：`mcp="stephanus"`；
- Wan 转发函数：`mcp_tools_list` 与 `mcp_tool_call`；
- `mcp_tool_call.tool`：七个已注册的只读 `stephanus_*` 工具之一；
- `mcp_tool_call.arguments`：按下游工具 schema 传入 JSON 对象，不能把 `query` 等业务参数放到 Wan 调用的顶层。

在当前 ChatGPT Code Mode 中，先通过 `ALL_TOOLS` 确认 Wan MCP 工具可用，再按实际名称调用。当前已验证的格式如下：

~~~javascript
// 第一次查询时列出下游工具
const catalog = await tools.mcp__wan_server_mcp__mcp_tools_list({
  server: "tencent-sv",
  mcp: "stephanus"
});
text(catalog);

// Wan MCP -> 腾讯云 SSH -> Stephanus MCP
const response = await tools.mcp__wan_server_mcp__mcp_tool_call({
  server: "tencent-sv",
  mcp: "stephanus",
  tool: "stephanus_search_names",
  arguments: {query: "古明地", language: "ja", limit: 5}
});
const envelope = typeof response.text === "string" ? JSON.parse(response.text) : response;
const payload = envelope.result?.structured_content
  ?? envelope.result?.content?.find(item => item.type === "text")?.text
  ?? envelope.result;
text(typeof payload === "string" ? JSON.parse(payload) : payload);
~~~

实际宿主中工具名可能由连接器重新映射；以上 `mcp__wan_server_mcp__*` 是当前已验证的名称。若名称未出现，应先通过工具发现核对实际可用的 Wan MCP `mcp_tools_list`／`mcp_tool_call` 及参数，避免构造不存在的函数。响应优先读取 `result.structured_content`，其次解析 `result.content` 中的文本 JSON；若外层 `text` 是 JSON 字符串，需先解析。检查 `is_error`。

**边界与失败处理：** 下游只调用本指南列出的七个只读接口，不使用 Wan 的 `shell_run`、文件管理或配置修改功能代替查询。Wan 连接缺失、MCP 别名不存在、SSH 或数据库失败时，明确说明无法实时检索；不得伪造词典条目、来源 ID 或已完成的查询，也不自动下载运行包。空命中按材料检索规则继续，不切换本地 CLI 重复相同查询。

**案例留存：** ChatGPT 生成案例 Markdown 供用户保存；只有用户另行明确要求写入服务器或 GitHub 时，才用对应工具处理写入。Codex 的 `data/examples/` 本地留存流程保留。

## Codex／本地项目接入

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
