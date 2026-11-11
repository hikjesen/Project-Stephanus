# A. 历史日语转写

在用户希望保留日语声音、采用早期欧洲拼写或传教士文献风格时读取。现代罗马字可作为读音基线；历史写法需另选时代与文献传统。

## 参考来源与适用范围

- Jaime González-Bolado，*Found in Transliteration: Japanese Names in Missionary Sources on Hideyoshi’s Invasions of Korea*，Japan Review 40（2025），213–240 页。[论文入口](https://doi.org/10.69307/japanreview.2025.Gonzalez-Bolado)；本地 `data/references/found-in-transliteration-jstage.pdf`。217–220 页讨论文献差异与拼写特点，附录用于找已有姓名／地名写法。研究对象主要为十六世纪末至十七世纪初相关传教士资料。
- 国立国语研究所，[罗马字表记为何有不同种类](https://kotoba.ninjal.ac.jp/qa/yokuaru/qa-183/)；本地 `data/references/ninjal-romanization.html`。用于了解现代体系的区别。
- 《日葡辞书》线索：本地 `data/references/nippo-jisho.html` 是目录入口。需要具体词形时，循入口查相应词条或文献，不将目录页视为词典全文。

## 怎样使用

先用 `search_names` 确认读音；需要时用 `transliterate_name` 得到现代基线。再按用户的时代风格查历史名字或相近音节的写法，保留具体文献传统；未指定时可采用上述传教士资料作为一种候选风格，简短注明。

论文第 220 页列举的常见拼写特点，可作为人工类推的起点：

| 现代读音／写法线索 | 文献中的例子 | 使用提示 |
|---|---|---|
| `h` 与 `f` 的对应 | Hakata → Fakata | 先看该音节和文献环境 |
| `sh` 与 `x` 的对应 | Shimo → Ximo | 可用于识别该历史拼写风格 |
| `ts` 与 `c/ç` 的对应 | Tsushima → Çuxima | 结合该文献的其他拼写特点选用 |
| `k` 在 `a/o/u` 前的写法 | 文献用 `c` 表示相应音 | 不扩展为对所有 `k` 的替换 |

这些特点在文献中存在变体，不组成一个统一的“耶稣会转换器”。以上历史例子用于说明参照方法；现代姓名应用相近规律所得的形式，标为“据某文献习惯类推”。其他音节需要时再查原文，不为制造差异叠加未经参考的字母变化。

按姓、名分别决定是否采用此法。历史文献中还可能含头衔、敬称与当时读音，选取时识别其成分；创作别名无需照搬头衔。

## 最小说明

保留「输入读音 → 参考的文献／拼写特点 → 历史实录或本次类推」。A 的结果可直接作历史风格别名，或继续作为 B 的材料；是否适合用户要求的外观差异，由具体结果决定。
