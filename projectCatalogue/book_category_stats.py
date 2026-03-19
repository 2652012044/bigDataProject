"""
统计 BookList.json 中每个类别的书籍数量并绘制分布统计图
"""

import json
import os
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import font_manager

# ── 中文字体配置 ──
# 优先尝试系统中文字体
for font_name in ["Microsoft YaHei", "SimHei", "PingFang SC", "WenQuanYi Micro Hei"]:
    if any(font_name.lower() in f.name.lower() for f in font_manager.fontManager.ttflist):
        matplotlib.rcParams["font.family"] = font_name
        break
matplotlib.rcParams["axes.unicode_minus"] = False

# ── 加载数据 ──
DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "fqDataAPI_mitproxy", "data", "BookList.json",
)

with open(DATA_PATH, encoding="utf-8") as f:
    data: dict = json.load(f)

# ── 统计每类别书籍数量 ──
category_counts = {cat: len(books) for cat, books in data.items()}
category_counts = dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True))

categories = list(category_counts.keys())
counts     = list(category_counts.values())
total      = sum(counts)

print(f"共 {len(categories)} 个类别，{total} 本书籍\n")
print(f"{'类别':<12} {'数量':>6} {'占比':>8}")
print("─" * 30)
for cat, cnt in category_counts.items():
    print(f"{cat:<12} {cnt:>6}  {cnt/total*100:>6.1f}%")

# ── 绘图 ──
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle(f"BookList.json 书籍类别分布（共 {total} 本）", fontsize=15, fontweight="bold")

# 左图：水平条形图
colors = plt.cm.tab20.colors
ax1 = axes[0]
bars = ax1.barh(categories[::-1], counts[::-1],
                color=[colors[i % len(colors)] for i in range(len(categories))])
ax1.set_xlabel("书籍数量")
ax1.set_title("各类别书籍数量")
ax1.bar_label(bars, fmt="%d", padding=3, fontsize=9)
ax1.set_xlim(0, max(counts) * 1.18)
ax1.grid(axis="x", linestyle="--", alpha=0.4)

# 右图：饼图（超过10类则合并小类）
PIE_THRESHOLD = 10
if len(categories) > PIE_THRESHOLD:
    top_cats   = categories[:PIE_THRESHOLD]
    top_counts = counts[:PIE_THRESHOLD]
    other_cnt  = sum(counts[PIE_THRESHOLD:])
    pie_labels = top_cats + [f"其他({len(categories) - PIE_THRESHOLD}类)"]
    pie_counts = top_counts + [other_cnt]
else:
    pie_labels = categories
    pie_counts = counts

ax2 = axes[1]
wedge_colors = [colors[i % len(colors)] for i in range(len(pie_labels))]
wedges, texts, autotexts = ax2.pie(
    pie_counts,
    labels=pie_labels,
    autopct=lambda p: f"{p:.1f}%" if p >= 2 else "",
    colors=wedge_colors,
    startangle=140,
    pctdistance=0.75,
)
for t in autotexts:
    t.set_fontsize(8)
ax2.set_title("类别占比饼图")

plt.tight_layout()

# ── 保存图片 ──
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "book_category_stats.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"\n图片已保存至: {out_path}")
plt.show()

# ── 生成补采参数文件：数量 < 40 的类别，平均分为 3 份，下拉超时 120 秒 ──
RETRY_THRESHOLD = 40
SCROLL_TIMEOUT  = 120
NUM_PARTS       = 3

retry_cats = [[cat, SCROLL_TIMEOUT] for cat, cnt in category_counts.items() if cnt < RETRY_THRESHOLD]

param_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "fqDataAPI_mitproxy", "param",
)
os.makedirs(param_dir, exist_ok=True)

total_retry = len(retry_cats)
print(f"\n共找到 {total_retry} 个数量 < {RETRY_THRESHOLD} 的类别，平均分为 {NUM_PARTS} 份：")

for i in range(NUM_PARTS):
    # 尽量平均分割，余数分给前几份
    base  = total_retry // NUM_PARTS
    extra = total_retry  % NUM_PARTS
    start = i * base + min(i, extra)
    end   = start + base + (1 if i < extra else 0)
    part  = retry_cats[start:end]

    out_path = os.path.join(param_dir, f"CatRetry{i + 1}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(part, f, ensure_ascii=False, indent=2)

    print(f"  CatRetry{i + 1}.json  ({len(part)} 个): " + ", ".join(c[0] for c in part))
