"""Measure file lengths in one traversal; no content inspection or hashing."""

from collections import defaultdict
from datetime import datetime, timezone
import json
import os

from stephanus.paths import ROOT

def main():
    groups = defaultdict(int)
    breakdown = defaultdict(int)
    vendor = defaultdict(int)
    files = 0
    for directory, _, names in os.walk(ROOT):
        for name in names:
            path = os.path.join(directory, name)
            relative = os.path.relpath(path, ROOT)
            parts = relative.replace("\\", "/").split("/")
            size = os.stat(path).st_size
            group = parts[0] if parts[0] in ("data", "vendor", ".venv", ".git") else "project"
            groups[group] += size
            files += 1
            if group == "vendor" and len(parts) > 1:
                vendor[parts[1]] += size
            if group == "data":
                if parts[-1].startswith("stephanus.sqlite"):
                    bucket = "query_index"
                elif parts[-1] == "raw-wiktextract-data.jsonl.gz":
                    bucket = "kaikki_shared_archive"
                elif parts[-1] == "ja-la.jsonl":
                    bucket = "kaikki_selected_languages"
                elif len(parts) > 1 and parts[1] == "raw":
                    bucket = "other_raw_datasets"
                elif len(parts) > 1 and parts[1] == "references":
                    bucket = "reference_documents"
                else:
                    bucket = "reports_and_other"
                breakdown[bucket] += size
    report = {"measured_at": datetime.now(timezone.utc).isoformat(), "basis": "logical file lengths, bytes", "files": files,
              "total_bytes": sum(groups.values()), "groups": dict(groups), "data_breakdown": dict(breakdown),
              "vendor_projects": dict(sorted(vendor.items(), key=lambda item: item[1], reverse=True))}
    (ROOT / "storage-usage.local.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    gib = lambda value: f"{value / 1024 ** 3:.3f} GiB"
    lines = ["# 存储占用与本地资源", "", "统计日期：2026-11-10。按文件长度统计，1 GiB = 1024³ 字节。", "", "| 部分 | 体积 |", "|---|---:|"]
    labels = {"data": "数据、索引与资料", "vendor": "第三方源码（包含其浅克隆 Git 数据）", ".venv": "Python 运行依赖", ".git": "本项目 Git 元数据", "project": "项目代码、文档与资源清单"}
    for group in ("data", "vendor", ".venv", ".git", "project"):
        lines.append(f"| {labels[group]} | {gib(groups[group])} |")
    lines.extend([f"| **本地合计** | **{gib(report['total_bytes'])}** |", "", "## 数据内部组成", "", "| 内容 | 体积 |", "|---|---:|"])
    data_labels = {"query_index": "生成的 SQLite 查询索引", "kaikki_shared_archive": "Kaikki 全语言共享原始压缩包", "kaikki_selected_languages": "从中筛选的日语、拉丁语 JSONL", "other_raw_datasets": "其他词典、CSV、姓名 SQLite 与压缩包", "reference_documents": "历史文献与参考资料", "reports_and_other": "运行记录及其他"}
    for group, size in breakdown.items():
        lines.append(f"| {data_labels[group]} | {gib(size)} |")
    lines.extend(["", "## 为什么保留这些文件", "", "- SQLite 索引直接支持日常查询；JSONL 与原始数据用于重建或扩展。", "- Kaikki 的上游将多种语言放在同一个压缩包中；项目只提取日语、拉丁语，没有保存全语言解压副本。", "- 第三方源码保留了上游 README、许可、数据与实现；jinmei-dict、verba、python-romkan 直接参与运行，其余主要供导入和参考。", "- 本次不清理本地归档。", "", "## GitHub 上传范围", "", "仓库包含代码、文档、资源地址与下载导入工具；大型数据、第三方源码、虚拟环境和本机路径配置均不进入 Git 历史。克隆仓库后使用 README 中的 fetch/import 命令准备资源。", "", "本表为本地资源快照，Git 提交及少量后续说明文件会产生小幅增量。", ""])
    (ROOT / "STORAGE.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
