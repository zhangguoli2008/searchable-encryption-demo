# visualize.py
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("benchmark_results.csv")
# 折线图
for q in df['query'].unique():
    sub = df[df['query']==q]
    plt.plot(sub['d'], sub['avg_latency_ms'], marker='o', label=q)
# plt.xlabel('编辑距离 d')
# plt.ylabel('平均查询延迟 (ms)')
# plt.title('查询延迟对比')
plt.xlabel('Edit Distance d')
plt.ylabel('Average Query Latency (ms)')
plt.title('Query Latency Comparison')
plt.xticks([0,1,2])
plt.legend()
plt.grid(True)
plt.savefig("latency_plot.png", dpi=300)
