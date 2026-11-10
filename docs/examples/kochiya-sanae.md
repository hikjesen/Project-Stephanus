# 实际使用案例：东风谷早苗

日期：2026-11-10。性质：一次实际创作调用，未运行或重复项目验收，未修改数据库及查询实现。通过真实 stdio MCP 使用本地 compact-v1 工具。

## 输入确认

- 用户输入：东风谷早苗。
- 日文：東風谷 早苗。
- 假名：こちや さなえ。
- Hepburn：Kochiya Sanae；西式名在前写作 Sanae Kochiya。
- 训令式姓氏：Kotiya。

人物读音参照 [《东方弹幕神乐》官方人物卡](https://danmaku.jp/archive/card/ssr013/)。本地姓名工具也分别查到姓氏和名字，罗马字由本项目 romkan 工具实际转换。

## 查询过程与关键记录

完整姓名「東風谷早苗」没有直接命中；分别查询「東風谷」与「早苗」后得到下列资料。读音选择结合人物资料，不将其他同字读法直接套用到角色。

| 环节 | 实际结果 | 本地记录 |
|---|---|---|
| 姓氏 | 東風谷 → こちや，surname | jmnedict:5557252:0 |
| 名字 | 早苗 → さなえ，女性名 | jmnedict:5475972:0 |
| 整体词义 | 早苗 → rice seedling | jmdict:1844650:0 |
| 姓氏意象 | 東風 → east wind / spring wind | jmdict:1582280:0 |
| 字义 | 谷 → valley | kanjidic2:谷 |
| 同音写法 | 佐名恵等 → さなえ | jmnedict:5301996:0 |
| 新意象 | 恵 → favor / blessing / grace / kindness | kanjidic2:恵 |

没有拆字拼接「早」和「苗」的字义，因为普通词「早苗」已经提供了直接义项。

英拉检索先试 seedling，当前精简条目只返回宽泛的 arbor，不直接将它当作稻苗的对应。随后继续查询 sprout、词根及相关词目，选择可用于创作的意象，而非固定采用第一个结果。

| 材料 | 本次取得的知识 | 本地记录 |
|---|---|---|
| germen / germinis | 新芽、嫩枝、芽苞；第三变格中性名词 | verba:ls:germen#n |
| oryza | 水稻，用于保留「稻」的另一种可选意象 | verba:sh:21549 |
| Solanus | 东风；阳性，属格形式依据词典的 -i | verba:ls:solanus#n |
| vallis | 山谷；valle 可作单数夺格 | verba:sh:27739；Whitaker 对 valle 的实际分析 |
| Chloe | 拉丁词典所收的希腊女子名 | verba:ls:chloe#n |
| Chloe / Chloé | 现有姓名及转写关联 | onomaverse:localized:286745 → onomaverse:chloe-fn |
| gratia | 恩惠、优雅等 | verba:sh:11401 |
| Gratia | 历史女性姓名，关联规范名 Grace；本条记录为英格兰 1558 年 | medieval-names:app_variations.csv:10051 |

Chloe 的「青苗」桥接另外查阅 [Perseus LSJ 的 χλόη 条目](https://atlas.perseus.tufts.edu/dictionaries/entry/urn%3Acite2%3Ascaife-viewer%3Adictionaries.v1%3Alsj-n114179/)，其义项包括春季新生的绿芽及幼嫩谷物。这个希腊词义来自本轮外部补充，不能表述为本地数据库已经包含希腊语词库。

姓氏采用语义创作：東風谷 → 东风之谷 → de Valle Solani。de 后使用 valle；Solani 表达「东风的」。整段姓氏组合由 Agent 构造，本次没有检得这一完整姓氏的历史用例。

曾考虑 Eurus；本地拉丁词典释义为 southeast wind，所以本次选择直接释为 east wind 的 Solanus。

## 五个候选

下列完整姓名均为本次 Agent 组合。既有名字和词汇是查询素材，不代表数据库收录了这些完整姓名。

| 候选 | 路线与形成过程 | 使用取向 |
|---|---|---|
| **Sanaea Cotia** | Sanae → Sanaea；Kotiya → Cotia。保留字母及声音轮廓，采用拉丁语式外形；两处加工均为本次创作 | 重视原名辨识度 |
| **Sanaea de Valle Solani** | 名保留 Sanae 的轮廓；姓改用「来自东风之谷」的语义组合 | 折中，名保音、姓取意 |
| **Germina de Valle Solani** | 早苗 → 幼芽意象 → germen / germinis → 以 germin- 为材料创作 Germina | 更直接使用拉丁词根；Germina 在这里是造名 |
| **Chloë de Valle Solani** | 早苗 → 青苗、新芽 → 已有女子名 Chloe；用 Chloë 提示分音；姓采用语义组合 | 本轮偏好，作为可使用的西式姓名 |
| **Gratia de Valle Solani** | さなえ → 同音写法佐名恵 → 恵 → grace / gratia → 历史姓名 Gratia | 同音意象再选择；借用「恵」，不将其说成原名已有含义 |

本轮首选 **Chloë de Valle Solani**，可意会为「来自东风之谷的青苗」。它将「稻苗」放宽为青苗、新芽；如果更重视原名声音，则选 **Sanaea Cotia**。

## 调用记录

完整工具参数、结构化结果和单次调用耗时保存在本机 `data/examples/kochiya-sanae/trace.json`。实际使用姓名查询、词汇查询、详情、关系、罗马字转换和拉丁语分析六类工具，未模拟工具输出。

本轮暴露的实际衔接需求是：完整姓名未命中时允许拆分；读音由人物上下文选择；词义过泛时继续选词；现成名字与自由造名并列呈现。当前创作与语义选择由 Agent 完成，独立拉丁化 skill 尚未安装。
