# 实际使用案例：若叶睦

日期：2026-11-11。用户暂时通过修订设计后，按 [暂定原则](../latinization-skill-design.md) 实际调用本地 stdio MCP。保留 compact-v1 数据库、现有七个工具及原验收报告；本次属于姓名创作实践。

## 输入与创作方向

输入「若叶睦」按《BanG Dream!》角色的日文写法 **若葉 睦**、读音 **わかば むつみ** 处理。官方[人物页](https://anime.bang-dream.com/bandorichan/character/avemujica/)列出假名，官方[英文介绍](https://en.bang-dream.com/anime/avemujica/)使用 Mutsumi Wakaba；本地也查到相应读音。

用户未另指定时代或地区，因此采用暂定默认方向：优先探索自然的欧洲姓名和有历史材料的形式，允许外观显著变化、部分保义；另给历史拼写类推作保音参考。姓名含义作为创作材料，不据此推定作品作者的命名意图。

本轮围绕姓名本身选材；角色另有舞台名 Mortis，这不替代本次对「若葉 睦」的推演。

## 姓与名分别解析

完整写法在本次 JMnedict 查询中没有命中，分别查姓、名。候选读音不止一种；结合人物资料，采用下表的 Wakaba／Mutsumi。

| 材料 | 实际查询结果 | 条目或工具 |
|---|---|---|
| 若葉作为姓名 | わかば；包括 surname 类别 | `jmnedict:5346352:0` |
| 睦作为姓名 | むつみ；包括 given 类别 | `jmnedict:5647997:0` |
| 若葉整体词义 | new leaves／young leaves／fresh verdure | `jmdict:1324460:0` |
| 睦字义 | intimate／friendly／harmonious | `kanjidic2:睦` |
| Hepburn 基线 | wakaba mutsumi | `transliterate_name` |
| 训令式基线 | wakaba mutumi | `transliterate_name` |

姓氏保留「新绿」或「新生、年轻」中的一个意象即可；名字从「友好、亲近」或「和睦」继续推演。无需拆开翻译「若」「葉」，也无需把所有意象同时塞入一个完整姓名。

## 从概念继续寻找姓名

### 睦：友好 → amica → Amice／Amica

英拉词库将 friendship 对应为 amicitia（`verba:sh:10609`）。据“朋友”的相关概念提出 Amice 作为姓名线索后，Medieval 实际返回其拉丁词源 **amica** 和女性姓名记录：

- `medieval-names:app_name_data.csv:561`：Amice，英格兰记录范围为 1279–1560，来源标明 Latin amica。
- `find_related_names(medieval-names:canonical:Amice)`：返回历史异写；其中 `medieval-names:app_variations.csv:1719` 为 **Amica**，1147 年法国记录、主格。
- 外部 [DMNES Amice 条目](https://dmnes.org/name/Amice)同样解释其词源。

这里由词汇进入已有姓名，再沿历史关系选形。amicitia 与 amica 是相关词汇材料；不把前者自动改词尾生成 Amice。

### 睦：和睦 → 和平意象 → Irene

英拉 harmony 条目提供 concordia 等词，并区分音乐和谐与比喻意义上的一致（`verba:sh:11963`）。本轮 Onomaverse 查询没有返回 Concordia；随后将“和睦”放宽为“和平”，提出已有姓名 Irene。

Onomaverse 返回 `onomaverse:irene-fn`；沿其转写关系取得意大利语形式 `onomaverse:localized:524157`。该关系支持本地化形式，词源另由 [Treccani 的 Irene 说明](https://emporium.treccani.it/product/tonki-irene/)补充：来自希腊语 Eirene，含“和平”义。

这是一条**意象借鉴 → 希腊来源的既有欧洲姓名 → 意大利语形式**的路线。Irene 与拉丁 concordia 在本次推演中是意义接近，不表述为同源。

### 若葉：新绿 → viridis → 有记录的姓名 Virida

英拉 green 条目包含 viridis，并列有颜色、鲜嫩等义项（`verba:sh:11542`）。继续查询姓名，得到：

- `medieval-names:app_name_data.csv:5860`：规范名 **Viridis**，女性，拉丁词源，释义涉及鲜绿、青春；有意大利记录。
- `medieval-names:app_variations.csv:23437`：1285 年的实录形式 Viridis，`CASE=gen`，即属格。
- 查外部 [DMNES Viridis 条目](https://dmnes.org/name/Viridis)后，取得主格实录 **Virida**，年代范围记为 1265×1339；当前条目为 2023 版，本地资料引用 2019 版。

因此选 **Virida** 作为拉丁语历史名形的单名候选。它具有实际姓名材料支持，不是本次给 virid- 临时加 `-a`。

因涉及词形，又调用一次 `analyze_latin("virida")`；工具将其分析为 virido／viridor 的动词形式。这一输出保留在调用记录中，姓名的主格依据仍采用 DMNES 的历史记录。此例体现普通词形分析与姓名文献可以提供不同层面的信息。

### 姓氏的两个独立选择

- **Novelli**：本地 `onomaverse:novelli-sn` 是 surname，详情有意大利分布资料。[Dictionary of American Family Names 经 Ancestry 提供的条目](https://www.ancestry.com/last-name-meaning/novelli)将其解释为 Novello 的父称或复数形式；[Treccani novello 词条](https://www.treccani.it/vocabolario/novello/)说明 novello 来自拉丁 novellus，涉及新近、年轻等含义。本轮由「若葉 → 新生、年轻」借用这个真实姓氏，舍弃“叶”的具体形象。
- **Greene**：本地 `onomaverse:localized:457983` 是英语 surname。[姓氏资料](https://surnames.behindthename.com/name/greene)将其列为 Green 的变体。本轮利用词面的绿意与「若葉」建立联想，不推定具体家族的历史来由。

同时查到的 Verdi 没有进入最终候选：现成姓氏固然可用，但本轮已获得两种有区别的姓氏策略，无需再凑一个同类结果。Novelli 的关系查询为空，也没有阻断依据其自身条目进行选用。

## 历史拼写与形态路线

采用 [方法 A 的参考](../references/historical-japanese-transliteration.md)，按 *Found in Transliteration* 第 220 页的拼写特点，作有限类推：

- Mutsumi 的 `ts` 参考文献中的 `c/ç` 写法，得到 **Muçumi**。
- Wakaba 的 `k` 在 `a` 前参考 `c` 写法，得到 **Wacaba**。

其他音节沿用基线，因此 **Muçumi Wacaba** 是本次采用部分历史拼写特点的保音候选，未声称这个完整写法有历史实录，也未把它称为一套完整葡萄牙语转写。

方法 B 的考虑是先找已有名形与构形参照。本次没有取得值得采用的 Mutsumi 拉丁化形式；已有 A 的保音方向及 C／D 的姓名材料，因此没有另给 Mutsumi 强加 `-a` 或 `-us`。四类方法作为方法库选择使用，无需为每类都制造一项结果。同音借义本次也未启用，因为原字义已有足够的可用入口。

## 四个候选

以下两个完整姓名由本次 Agent 组合；所选名、姓分别有资料依据。单名与历史拼写类推另列其用途。

| 候选 | 语言／风格与方法 | 形成链与取舍 |
|---|---|---|
| **Irene Novelli** | 意大利语姓名；C → D | 睦 → 和睦 → 和平意象 → Irene；若葉 → 新生、年轻 → novello → 已有姓氏 Novelli。偏向自然、外观变化明显的完整姓名 |
| **Amice Greene** | 英语姓名，名带中世纪气息；D | 睦 → 友好 → amica → 已有姓名 Amice；若葉 → 绿意 → 真实姓氏 Greene。保留亲近、绿色的间接联系 |
| **Virida** | 有中世纪拉丁语主格实录的单名；C → D | 若葉 → 鲜绿、青春 → viridis 姓名线索 → 文献主格 Virida。优先保留姓氏意象，允许用其作为新的单名别名，未同时转译「睦」 |
| **Muçumi Wacaba** | 历史拼写特点类推；A | 按读音与两项有文献参照的拼写特点改写，采用西式名在前。保音优先，表面差异较小 |

按本次默认方向，完整姓名优先选 **Irene Novelli**；若更看重有文献名形依据的拉丁语单名，则选 **Virida**。这是此次创作选择，不是统一排名；Amice Greene 更适合希望保留友善含义并接受古雅英语名形的使用者。

## 调用记录与实践观察

实际 MCP 参数、结构化结果与单次耗时保存在本机 `data/examples/wakaba-mutsumi/trace.json`，含姓名、词汇、详情、关系、罗马字及一次词形分析六类工具调用；外部来源与采用结果另存为该记录的元数据。数据库和 MCP 实现未作修改，也未运行项目验收脚本。

本次最有用的衔接发生在“查到词”之后：从 amica 继续找到 Amice／Amica，从 viridis 继续找到历史姓名及具体格形式，随后分别选择完整姓名或单名。没有把所有材料强制拼成一个拉丁短语，也没有要求每个方法都产出候选。
