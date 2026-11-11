# B. 人名形态拉丁化

在用户希望保留部分音形，同时获得拉丁语式姓名时读取。先查已有拉丁形式，再决定是否按惯例类推。

## 参考来源与适用范围

- Dan H. Nicolson，*Orthography of Names and Epithets: Latinization of Personal Names*，Taxon 23(4)（1974），549–561 页。[原文](https://www.iapt-taxon.org/historic/Congress/IBC_1975/Prop030-032.pdf)；本地 `data/references/latinization-personal-names.pdf`。重点读 550、552 页的语义改名、词干与屈折说明。该文主要讨论植物命名中的人名拉丁化及相关命名法规；本项目借鉴构形思路，不将其中的种加词规则直接用于人类姓名。
- 英国国家档案馆，[How to decline personal names](https://www.nationalarchives.gov.uk/latin/reference/how-to-decline-personal-names/)。需要时查姓名在拉丁语中的格变化；它提供语法参考，姓名选取仍由实际资料及用户风格决定。
- 历史人物的实际形式可查 [Deutsche Biographie](https://www.deutsche-biographie.de/gnd118501062.html)、DMNES 或本地 Medieval 条目。先看姓名形式及来源，再决定采用或类推。

## 怎样使用

1. 用 `search_names` 查原名的罗马字或已有相关姓名，选中后读详情与变体。若已有适合的拉丁形式，可以直接采用。
2. 需要类推时，说明主要保留的音节或词干，并选择有参照的构形方式。Nicolson 第 552 页以 Albert → Albertus、Fuchs → Fuchsius 展示不同处理；这些是参照实例，不是任意日语名字加后缀的通用公式。
3. 分开考虑名与姓、基础名形与句中屈折。输出姓名一般采用基础形式；需要短语时再处理相应语法。性别和目标风格按人物／用户要求选择，不把女性名一律处理成 `-a`。
4. 仅当有具体词形疑问时调用 `analyze_latin`。返回分析可帮助识别词干或词形；是否为历史姓名、是否适合目标文化，要看姓名资料和构形参照。

历史音形处理也可以接在方法 A 后。对原拼写进行了什么改动、依据哪一类惯例，用一句话交代；新日语名字据例形成的形式标为类推或创作。

## 选择提示

保音要求高时，保留主要声音轮廓；用户更重视显著改名或自然欧洲姓名时，允许转向 C／D。`Sanaea`、`Cotia` 在旧案例中是 Agent 的加工，不能因具有拉丁外形就升级为传统形式。

最小形成链为「原读音／已有拼写 → 参照的姓名构形 → 本次保留与改动 → 基础名形」。无需让词形工具识别所有新造姓名。
