#!/usr/bin/env python3
# advanced_benchmark.py
# 精细化基准测试：支持输出文件自动编号，若已有 advanced_benchmark_results.csv，
# 则生成 advanced_benchmark_results_1.csv、advanced_benchmark_results_2.csv...

import os
import sys
import time
import csv
import requests
import statistics
from difflib import get_close_matches

# 确保能导入项目根目录下的 utils 模块
sys.path.append(os.getcwd())
from utils.crypto_utils import prf
from utils.data_structures import BloomFilter

# ---- 配置区 ----
SERVER    = "http://192.168.228.142:5000"
QUERIES   = ["encryption", "bloom", "merkle", "email", "security"]
DISTANCES = [0, 1, 2]
TOP_K     = 5
WARMUP    = 10
REPEATS   = 50
# ----------------

# 自动生成输出文件名
base_name = "advanced_benchmark_results.csv"
if not os.path.exists(base_name):
    output_csv = base_name
else:
    idx = 1
    while True:
        candidate = f"advanced_benchmark_results_{idx}.csv"
        if not os.path.exists(candidate):
            output_csv = candidate
            break
        idx += 1

print(f"[+] Benchmark results will be written to: {output_csv}")

# 拉取参数与词表
params = requests.get(f"{SERVER}/params").json()
SK     = bytes.fromhex(params['key'])
m, k_hash = params['m'], params['k']
vocab  = requests.get(f"{SERVER}/vocabulary").json()

# 写入 CSV
with open(output_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["query", "d", "metric", "value_ms"])

    for q in QUERIES:
        print(f"=== Benchmarking '{q}' ===")
        for d in DISTANCES:
            # 预热
            for _ in range(WARMUP):
                Wq = set(get_close_matches(q, vocab, n=50, cutoff=0.8)) | {q}
                bf = BloomFilter(m, k_hash)
                for w in Wq:
                    bf.add(w)
                td = [prf(SK, str(pos)).hex() for pos in bf.bit_positions()]
                requests.post(f"{SERVER}/search", json={"trapdoor": td, "k": TOP_K})

            # 正式测量
            trap_times = []
            search_times = []
            for _ in range(REPEATS):
                # Trapdoor 生成
                t0 = time.perf_counter_ns()
                Wq = set(get_close_matches(q, vocab, n=50, cutoff=0.8)) | {q}
                bf = BloomFilter(m, k_hash)
                for w in Wq:
                    bf.add(w)
                td = [prf(SK, str(pos)).hex() for pos in bf.bit_positions()]
                t1 = time.perf_counter_ns()
                trap_times.append((t1 - t0) / 1e6)

                # Search 请求
                t2 = time.perf_counter_ns()
                requests.post(f"{SERVER}/search", json={"trapdoor": td, "k": TOP_K})
                t3 = time.perf_counter_ns()
                search_times.append((t3 - t2) / 1e6)

            # 剔除上下 5% 极值
            def trim(data):
                data_sorted = sorted(data)
                cut = int(0.05 * len(data_sorted))
                return data_sorted[cut:-cut] if cut > 0 else data_sorted

            trap_clean   = trim(trap_times)
            search_clean = trim(search_times)

            # 写入统计指标
            for name, data in [("trapdoor_gen", trap_clean), ("search", search_clean)]:
                if data:
                    writer.writerow([q, d, f"{name}_mean",   statistics.mean(data)])
                    writer.writerow([q, d, f"{name}_median", statistics.median(data)])
                    writer.writerow([q, d, f"{name}_std",    statistics.stdev(data)])
                    writer.writerow([q, d, f"{name}_p95",    data[int(0.95 * len(data))]])
                else:
                    # 若数据不足，写 0
                    writer.writerow([q, d, f"{name}_mean",   0])
                    writer.writerow([q, d, f"{name}_median", 0])
                    writer.writerow([q, d, f"{name}_std",    0])
                    writer.writerow([q, d, f"{name}_p95",    0])

print("=== Advanced benchmark complete ===")
print("Results saved to:", output_csv)













# 第一版
# #!/usr/bin/env python3
# # advanced_benchmark.py
#
# import time, csv, requests, statistics, os, sys
# from difflib import get_close_matches
#
# # -----------------------------------------------------------------------------
# # 如果你在脚本目录下运行，则确保项目根在 PYTHONPATH 中，以便导入 utils
# sys.path.append(os.getcwd())
# from utils.crypto_utils import prf
# from utils.data_structures import BloomFilter
# # -----------------------------------------------------------------------------
#
# # ---- 配置区 ----
# SERVER    = "http://192.168.228.142:5000"      # 搜索服务地址
# QUERIES   = ["encryption", "bloom", "merkle", "email", "security"]
# DISTANCES = [0, 1, 2]                          # 编辑距离
# TOP_K     = 5                                  # Top-k 返回
# WARMUP    = 10                                 # 预热次数
# REPEATS   = 50                                 # 正式测量次数
# OUTPUT_CSV = "advanced_benchmark_results.csv"
# # ----------------
#
# # 1. 拉取参数与词表
# params = requests.get(f"{SERVER}/params").json()
# SK     = bytes.fromhex(params['key'])
# m, k_hash = params['m'], params['k']
# vocab  = requests.get(f"{SERVER}/vocabulary").json()
#
# # 2. 打开 CSV 写表头
# with open(OUTPUT_CSV, "w", newline="") as f:
#     writer = csv.writer(f)
#     writer.writerow(["query", "d", "metric", "value_ms"])
#
#     # 3. 对每个 query × d 分组做测试
#     for q in QUERIES:
#         print(f"=== Benchmarking '{q}' ===")
#         for d in DISTANCES:
#
#             # 3.1 预热（不计时）
#             for _ in range(WARMUP):
#                 Wq = set(get_close_matches(q, vocab, n=50, cutoff=0.8)) | {q}
#                 bf = BloomFilter(m, k_hash)
#                 for w in Wq: bf.add(w)
#                 td = [prf(SK, str(pos)).hex() for pos in bf.bit_positions()]
#                 requests.post(f"{SERVER}/search", json={"trapdoor": td, "k": TOP_K})
#
#             # 3.2 正式测量
#             trap_times, search_times = [], []
#             for _ in range(REPEATS):
#                 # 3.2.1 生成 Trapdoor
#                 t0 = time.perf_counter_ns()
#                 Wq = set(get_close_matches(q, vocab, n=50, cutoff=0.8)) | {q}
#                 bf = BloomFilter(m, k_hash)
#                 for w in Wq: bf.add(w)
#                 td = [prf(SK, str(pos)).hex() for pos in bf.bit_positions()]
#                 t1 = time.perf_counter_ns()
#                 trap_times.append((t1 - t0) / 1e6)
#
#                 # 3.2.2 发送搜索请求
#                 t2 = time.perf_counter_ns()
#                 requests.post(f"{SERVER}/search", json={"trapdoor": td, "k": TOP_K})
#                 t3 = time.perf_counter_ns()
#                 search_times.append((t3 - t2) / 1e6)
#
#             # 4. 剔除上下 5% 极值
#             def trim(data):
#                 data = sorted(data)
#                 cut = int(0.05 * len(data))
#                 return data[cut:-cut]
#
#             trap_clean   = trim(trap_times)
#             search_clean = trim(search_times)
#
#             # 5. 写入各项统计指标
#             for name, data in [("trapdoor_gen", trap_clean), ("search", search_clean)]:
#                 writer.writerow([q, d, f"{name}_mean",   statistics.mean(data)])
#                 writer.writerow([q, d, f"{name}_median", statistics.median(data)])
#                 writer.writerow([q, d, f"{name}_std",    statistics.stdev(data)])
#                 writer.writerow([q, d, f"{name}_p95",    data[int(0.95 * len(data))]])
#
# print("=== Advanced benchmark complete ===")
# print("Output CSV:", OUTPUT_CSV)
