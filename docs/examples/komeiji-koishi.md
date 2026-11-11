# 实际使用案例：古明地恋

日期：2026-11-11。按[修订设计稿](../latinization-skill-design.md)先完成输入解析与意象选择，收到用户答复后继续实际调用本地 stdio MCP。复用 compact-v1 数据库和现有七个工具，本次属于姓名创作实践。

## 输入与用户选择

输入「古明地恋」按日文 **古明地 こいし**、读音 **こめいじ こいし** 处理；姓为 Komeiji，名为 Koishi。[《东方弹幕神乐》人物介绍](https://danmaku.jp/archive/character/c009/)支持这一写法与读音。

前置查询只取得姓名读音、同音词及现代罗马字基线，随后展示四种关联可能：小石与微小的存在、恋慕与思念、闭合的心与隐匿、声音轮廓。没有在选择前生成最终名字。

用户补充的主体倾向为：**「理想中的真挚感情」**。同时表达「不对语言做出明确要求」，并在语言项选择「拉丁语名形」。本轮以拉丁语名形为主要终点，语言不严格锁定；没有另设必须覆盖多种语言的要求。

这一选择超出了原先四项的简单勾选。后续围绕值得珍重的爱、坦诚的心意与被珍爱的状态探索；这是采用用户指定意象进行创作，不把它写成「こいし」唯一确定的词源或作者命名意图。姓氏可以保留局部声音联系。

## 前置解析

| 材料 | 实际结果 | 本地记录 |
|---|---|---|
| 古明地 | 姓氏，读音包含こめいじ；结合人物资料选用 | `jmnedict:5257392:0` |
| こいし | 姓名读音匹配到小いし等形式；不据此改写角色原名 | `jmnedict:5369829:0` |
| 小石 | こいし；pebble / small stone | `jmdict:1348400:0` |
| 恋しい | こいしい；yearned for / longed for / missed，读音与こいし有别 | `jmdict:1558760:0` |
| Hepburn 基线 | komeiji koishi | `transliterate_name` |

## 从所选意象到姓名

主要采用 C → D：从用户认可的意象进入拉丁词汇，继续寻找已有姓名，读取具体词源和记录，再选择名形。姓氏补用 A 的有限拼写类推，并继续适配到真实拉丁姓名参照。

| 材料 | 本次读取到的内容 | 本地记录 |
|---|---|---|
| affection | amor、caritas 等出现在稳定善意或爱的分项；其他义项也可能表示身心状态 | `verba:sh:484` |
| sincere | sincerus、simplex、verus、candidus 等线索；列表用于继续查证 | `verba:sh:23199` |
| ideal | perfectus、exemplar、species 等；没有直接成为最终姓名 | `verba:sh:12852` |
| faith | fides 等线索，本轮未作为成品采用 | `verba:sh:9473` |
| Amanda | 女性规范名；词源释为 Latin amanda，meant to be loved | `medieval-names:app_name_data.csv:530` |
| Amanda 的相关形式 | 返回 Amandine，关系原类型为 historical_variant | `medieval-names:canonical:Amanda` 的关系查询 |
| Amandine 实录 | 1591–1593 年记录，未标格；与 Amanda 规范名分别保留 | `medieval-names:app_variations.csv:1640` |
| Amata | 女性姓名，loved / beloved；本地摘要含意大利 1285–1304 年范围 | `medieval-names:app_name_data.csv:538` |
| Candida | 女性姓名；clear, bright / lucid / candid | `medieval-names:app_name_data.csv:1300` |
| candidus | 拉丁形容词，摘要含 shining white / clear / bright | `verba:ls:candidus#a` |

`analyze_latin("amanda")` 返回 amo 的未来被动分词等分析，也返回另一动词的命令式分析。这里结合姓名资料采用 amo 的相关女性名形；词形工具的多个返回不直接决定词源，更不单独证明人名实录。

“理想中的”在本轮被理解为对感情的期待或价值判断。“值得被爱、值得珍重”是其中一个创作落点；它不等同于 Amanda 的字面含义已经包含“真挚”。Candida 另提供突出真诚、坦率的一条路径。

## 补充资料与名形选择

- [DMNES：Amanda](https://dmnes.org/name/Amanda)将 Amanda 作为女性规范名，释为 meant to be loved；当前条目列出的早期实例写作 **Amandine**。本轮选择拉丁词源基础名形 Amanda，不将这些实例说成 Amanda 原拼写的拉丁文实录。
- [DMNES：Amata](https://dmnes.org/name/Amata)释为 loved / beloved；当前条目明确列出西班牙拉丁语材料 **1488 Amata（主格）**。这比从本地规范名摘要直接推断某地区的实际拼写更具体。
- [DMNES：Candida](https://dmnes.org/name/Candida)区分意大利语 Candida 和拉丁语实录变体 Candidella。[Roman Inscriptions of Britain，RIB 689](https://romaninscriptionsofbritain.org/inscriptions/689)另记录罗马时期女性 Candida Barita，正文写 Candidae；可以支持 Candida 作为人名的使用。
- [Lewis & Short：candidus，CLD](https://cld.bbaw.de/lemma/lat/candidus)含由明亮、洁白引申至心性坦率、诚实、真挚的义项。本轮采用这个引申方向，不把“洁白”直接等同于感情。
- [大都会艺术博物馆：Cominia Tyche 墓坛](https://www.metmuseum.org/art/collection/search/253569)保存约公元 90–100 年的实际女性姓名。[CIL II 数字项目的铭文条目](https://cil2digital.web.uah.es/inscripciones/ficha/628/205-inscripciones-sepulcrales)索引内容另将 Cominia 说明为女性氏族名，并列 Cominia Marcella 等实例；该站本轮直接访问返回 403，相关内容来自搜索索引。最终采用的姓名形与双名参照可以直接由博物馆资料支持。

本次对 Caritas、Cordula、Fidelia、Dilecta 等线索的部分本地查询没有命中；不据此宣称这些名字在历史上不存在，也没有为补齐候选继续穷尽检索。

## 姓氏：历史拼写之后继续适配

本轮只在姓氏使用历史拼写作为中间材料：

**Komeiji → Comeiji → Cominia**。

第一步参考[历史日语转写指引](../references/historical-japanese-transliteration.md)及其所引论文第 220 页，将 o 前的 k 写作 c，其他部分保留；Comeiji 是本次有限类推，未声称查到角色的历史写法。

第二步按[目标语言姓名适配指引](../references/target-language-name-adaptation.md)，改用有实际姓名参照的 **Cominia**。保留的是开头 ko-m 的局部声音轮廓；后半明显改形，既有拉丁名形提供结构参照。这是音近借名的创作选择，不是 Comeiji 按某条固定音变规则必然变为 Cominia。

名的部分采用用户选定的语义方向：Koishi → 本轮认可的感情意象 → Amanda。Amanda 不是由 Koishi 的拼写或历史转写推导出来的。

## 候选与本轮推荐

| 候选 | 用途与方法 | 与用户意象的联系及取舍 |
|---|---|---|
| **Cominia Amanda**（科米尼娅·阿曼达） | 完整拉丁语风格创作姓名；姓用 A → 真实名形适配，名用 C → D | Cominia 留下 Komeiji 的局部声音；Amanda 表达“应当被爱、值得珍重”的期待，突出理想感情的愿望与价值。没有把“真挚”逐词编码进去 |
| **Candida**（坎迪达） | 有既有姓名参照的单名；C → D | 从“真挚感情”取坦率、澄明的心意；词义与人名使用分别有依据。也可与原姓「明」形成附加视觉联想，但未声称这是古明地的姓氏词源。没有直接表达爱恋 |
| **Amata**（阿玛塔） | 有拉丁语主格实录的单名；C → D | 保留“被爱、被珍惜”的状态，侧重感情已经落在某个人身上的温柔。与 Amanda 同词根，是语义侧重点不同的备选，未作为独立词源路线计数 |

完整姓名本轮推荐 **Cominia Amanda**。它以前部 Cominia、后部个人名 Amanda 的双名结构为创作参照；罗马女性族名与后世拉丁词源姓名的材料在这里重新组合，完整组合为本次创作，不声称是古罗马人物实录。

如果最看重的是“真挚、坦诚”这一层，**Candida** 更直接贴近该侧重；若看重“被珍爱”的温柔，**Amata** 更合适。后二者本轮作为单名别名给出。

## 调用与流程观察

原始 MCP 参数、结果及单次耗时保存在本机 `data/examples/komeiji-koishi/trace.json`。记录包含选择前的五次轻量调用与用户答复后的扩展查询，涉及姓名、词汇、详情、关系、罗马字和词形分析六类工具。

用户没有沿用模型预设的某一选项，而是补充“理想中的真挚感情”，使检索中心从小石、隐匿等材料转到值得珍重的爱与坦诚心意。这说明意象选择环节需要允许自由补充。

历史拼写没有停在 Comeiji；后续转用 Cominia 的真实名形参照。主要创造性在于选择联系与组合，不以增加日语拼写变体替代目标语言适配。四类方法按需要使用，本轮未另造 B 的强保音姓名。

数据库、MCP 实现和已有验收报告保持原状。仅对新增案例做一次文档检查；本轮未执行数据库或工具验收。

## 用户补充后的设计复盘与四个完整候选（2026-11-11）

以上保留为初轮记录。用户指出：至少需要四个完整姓名，至少一个回应选定的意象，至少一个通过历史拼写特点类推形成；其他候选应有不同构造或风格。选材宁可生僻，不取 Amanda 这种过于普通的名形；可以在选好基础名后再做可选修饰，同时列出修饰前后版本，仍计一个候选。

初轮的问题有三点：把用户意象当成整组候选的共同限制；用两个单名代替完整姓名，并把只处理姓氏的历史拼写当成足够的路线覆盖；知道 Amandine 等形式却仍优先采用 Amanda，混淆了自然与常见。下面补做四个完整姓名，不改写初轮的查询与提案。

### 补充材料

| 材料 | 本次取得的内容与用途 | 依据 |
|---|---|---|
| Amandine | 沿用初轮取得的具体变体，作为用户认可的基础选材；不宣称它在所有法语地区都罕见 | `medieval-names:app_variations.csv:1640`；[DMNES](https://dmnes.org/name/Amanda) |
| Cornelia | 真实女性名形，提供本次修饰中 `-elia` 收束的拼写与节奏参照；不把它说成可通用套用的词缀 | `medieval-names:app_name_data.csv:1537` |
| Cosima | Onomaverse 收为 given，详情有女性及意大利使用信息；用于从历史中间形进入实际姓名 | `onomaverse:cosima-fn` |
| Comini | 本轮 Onomaverse 未命中；意大利文化部档案目录列 Comini, Giulio Cesare、Comini, Marc'Antonio 等实际姓名，作为姓氏参照 | [国家档案目录](https://inventari-san.cultura.gov.it/inventari/1559/pdf) |
| petra | rock / crag / stone；作为「小石」方向的石头词根材料，不把基本词义误称为“小石子” | `verba:ls:petra#n1` |
| Prisca → Priscilla | 既有姓名中的指小构形参照 | `medieval-names:app_name_data.csv:4775`；[DMNES](https://dmnes.org/name/Priscilla) |
| Claramontius | Chiaramonti, Scipione 的实际拉丁化姓氏变体，作为本次姓氏加工参照 | [Deutsche Biographie](https://www.deutsche-biographie.de/11765972X.html) |
| Candidella | Candida 系列的女性历史变体，本地主格记录为 1522；当前 DMNES 为意大利拉丁语材料，范围标作 1522×1532 | `medieval-names:app_variations.csv:4520`；[DMNES](https://dmnes.org/name/Candida) |
| Celati | 真实意大利姓氏；Gianni Celati 的人物资料支持其用法 | [Treccani](https://www.treccani.it/enciclopedia/gianni-celati/) |
| celatus | concealed，提供本次对 Celati 字面外观的文学联想；不据此断言姓氏的真实词源 | `verba:sh:5014` |

Petrilla 的本地查询未命中，DMNES 同名入口本轮也未取得内容；下文采用的是参照真实构形的创作形，不将其标成数据库实录。没有为修饰形另建数据库条目或要求词形工具必须识别。

### 四条形成路径

**1. 用户选定的意象：Cominia Amandine → Cominia Amandelia（可选修饰）。**

姓沿用初轮的 Komeiji → Comeiji → Cominia；名从“理想中的真挚感情”取值得珍重的爱与期待，改用此前已取得、用户认可的 **Amandine**，作为本条基础名。Amanda 保留在词源链中，退出本轮成品选材。

可选修饰将 Amandine 改作 **Amandelia**：保留 Amand- 的辨识线索，参照 Cornelia 一类女性名形的 `-elia` 收束，重新安排后半节奏。这是本次自主加工，不声称历史上有 Amandine → Amandelia 的固定派生规则，也不要求修饰形已有收录。

基础版采用「族名／姓 Cominia＋名 Amandine」，带拉丁与法语交织的古雅风格；修饰版进一步偏向拉丁式文学名形。修饰可选，两种完整写法合计一个候选。

**2. 历史拼写主线：Coixi Comeiji → Cosima Comini。**

从西式顺序 **Koishi Komeiji** 出发，参考既有历史转写指引：o 前 k → c，sh → x，得到本次类推中间形 **Coixi Comeiji**。这不是角色的历史实录，也没有为 ji 另造规则。

继续做必要的目标语言适配：Coixi 借用实际姓名 **Cosima**，保留 co- 与后部擦音／i 的部分声音线索，缩减原元音串并改成既有名形；Comeiji 借用实际姓氏 **Comini**，压缩并重排后半。两步借名是创作选择，不是历史字母替换自动生成了这两个意大利姓名。

成品 **Cosima Comini** 采用意大利语「名＋姓」。本条主要保留声音，无需把 Cosima 的词源解释成“真挚感情”。Coixi Comeiji 是中间材料，Cosima Comini 是已适配的完整基础名；本条未再做可选修饰。

**3. 人文主义语义与构形：Petrilla Claramontia。**

名从こいし的同音词「小石」取材，经 petra 的石头词根，参照 Prisca → Priscilla 的指小名形，采用本次创作形 **Petrilla**；这是让“小而不起眼的石头”进入姓名的构形类推，不宣称 petra 本身就是小石子，或 Petrilla 已有本地实录。

姓将原姓「明、地」的视觉线索放宽为明亮的山地，以真实拉丁化姓氏 **Claramontius** 为参照采用女性形式 **Claramontia**。这是本次的语义取景与女形类推，不是古明地的历史词源，也未取得 Claramontia 的女性实录。

完整姓名采用「名 Petrilla＋拉丁化姓 Claramontia」，偏人文主义、古雅文学风格；本条不承担用户所选感情方向。Petrilla、Claramontia 已是本条创作得到的基础名，未另外执行后续修饰。

**4. 既有历史变体与人物联想：Candidella Celati。**

名直接选用具体主格实录 **Candidella**，承接 candidus 的澄明、坦诚意象；基础选材已经从常见规范名转向较有辨识度的历史形式。这里把它作为已有变体来选用，不把 Candida → Candidella 算成本轮可选修饰。

姓借用实际意大利姓氏 **Celati**，以其与拉丁语 celatus 的字面相近，联系角色闭合的心与隐匿状态；这一层是本次文学联想，不是该家族姓氏词源的断言。

完整姓名采用「名 Candidella＋姓 Celati」，呈现文艺复兴名形与意大利姓氏组合的文学风格。它也回应“真挚”的一面，同时采用角色材料；无需把四个候选都限定在同一感情词根。

### 本轮交付

| 构造方向 | 完整基础姓名 | 可选修饰后的完整姓名 | 本条主要联系 |
|---|---|---|---|
| 用户意象，C → D | **Cominia Amandine** | **Cominia Amandelia** | 理想感情的期待与值得珍重的爱；姓留局部声音 |
| 独立历史路线，A → 姓名适配 | **Cosima Comini** | — | Koishi Komeiji → Coixi Comeiji → 意大利姓名；以声音为主 |
| 人文主义语义与形态类推，C＋B | **Petrilla Claramontia** | — | 小石与明亮山地的画面；古雅拉丁化创作 |
| 既有历史变体与人物联想，D＋C | **Candidella Celati** | — | 坦诚心意与隐匿的心；历史名形＋意大利姓氏 |

四行均为完整姓名；第一行的修饰前后版本合计一个候选。本轮至少第一行明确回应用户的选定，第二行完整承担历史拼写路线；第四行也可与真挚意象重叠。保留基础版 **Cominia Amandine**，喜欢进一步修饰时采用 **Cominia Amandelia**，不再推荐 Amanda 作为本项目的成品基础名。

这些名字的完整组合均为本次选择，Petrilla、Claramontia 与修饰形 Amandelia 以创作身份给出。生僻是本项目的审美筛选，不将用户对 Amandine 的认可或单条数据库记录升级为全球使用频率结论。

本次补充调用追加到原始 trace；初轮三项候选与三十次调用的记录保留。数据库与 MCP 代码未改动，修订文档统一做一次检查，未重跑已有验收。
