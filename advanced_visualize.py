#!/usr/bin/env python3
# advanced_visualize.py
# 从 advanced_benchmark_results.csv 中读取数据，
# 为 Trapdoor 生成与 Search 两个阶段分别绘制平均延迟折线图。

import pandas as pd
import matplotlib.pyplot as plt

# 1. 读取 benchmark 输出
df = pd.read_csv("advanced_benchmark_results.csv")

# 2. 筛选出 mean 指标，并拆分出阶段名称
mean_df = df[df['metric'].str.endswith('_mean')].copy()
mean_df['stage'] = mean_df['metric'].str.replace('_mean', '', regex=False)

# 3. 创建两个子图：上图为 Trapdoor 生成，下图为 Search
fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(6, 8), sharex=True)

for ax, stage in zip(axes, ['trapdoor_gen', 'search']):
    sub = mean_df[mean_df['stage'] == stage]
    for q in sub['query'].unique():
        qdf = sub[sub['query'] == q]
        ax.plot(qdf['d'], qdf['value_ms'], marker='o', label=q)
    ax.set_title(f"{stage.replace('_', ' ').title()} Latency vs Edit Distance")
    ax.set_ylabel("Latency (ms)")
    ax.set_xticks([0, 1, 2])
    ax.grid(True)
    ax.legend(title="Query")

# 4. 统一的 X 轴标签
axes[-1].set_xlabel("Edit Distance (d)")

# 5. 布局优化并保存
plt.tight_layout()
plt.savefig("advanced_latency_plot.png", dpi=300)
print("Saved advanced_latency_plot.png")