<!-- 使用说明，不写入成品：
默认至少四个完整姓名，无固定上限；按实际数量展开候选行和形成链。
至少一项回应用户意象，至少两项从用户意象之外的独立材料出发；历史路线默认保留，不占至少三个有效意象选项。
full_candidate_rows 为整组表格行，formation_chains 为对应数量的形成链，不使用固定 route_1..4 或 chain_1..4 槽位。
optional_symbolic_mononym_section：无单人名时替换为空；有时生成一个独立段落，写明唯一单人名、象征含义、与原名或人物的联系及依据。单人名额外列出，不计完整姓名名额。
candidate_count_note 记录实际完整姓名数量、独立来源项、历史项及单人名为零或一；修饰前后不重复计数。
用户已明确倾向时，imagery_options 记为已明确、未重复询问，不补造提问记录。用户限定范围时按其要求调整，删除说明与未使用的占位内容。
-->

# 名称转译案例：{{input_name}}

- 时间：{{local_time}}（{{timezone}}）
- Skill：stephanus-latinization；版本：{{skill_version}}
- 记录性质：{{record_kind}}
- 原文与姓／名：{{normalized_input}}
- 假名与 Hepburn：{{readings}}
- 提供的有效意象方向（不含默认历史路线）：{{imagery_options}}
- 用户倾向、语言及其他约束：{{user_preferences}}
- 查询途径：{{query_access}}

## 完整候选

| 构造起点及与用户意象的关系 | 完整基础姓名（注明顺序） | 可选修饰后的完整姓名 | 语言／风格 | 联系及关键依据 |
|---|---|---|---|---|
{{full_candidate_rows}}

{{candidate_count_note}}

## 简短形成链

{{formation_chains}}

{{optional_symbolic_mononym_section}}

## 关键依据与创作说明

{{sources_and_creation}}

## 推荐与用户选择

- 本次推荐：{{recommendation}}
- 用户选择状态：{{user_selection}}
- 可选修饰的采用状态：{{modification_selection}}

## 后续反馈

{{feedback}}
