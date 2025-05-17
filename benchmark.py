#!/usr/bin/env python3
# benchmark.py
# 批量基准测试：支持输出文件自动编号，若已有 benchmark_results.csv，
# 则生成 benchmark_results_1.csv、benchmark_results_2.csv...

import os
import time
import csv
import requests
from difflib import get_close_matches
import sys

# 确保能导入项目根的 utils 模块
sys.path.append(os.getcwd())
from utils.crypto_utils import prf
from utils.data_structures import BloomFilter

# ---- 配置区 ----
SERVER    = "http://192.168.228.142:5000"
QUERIES   = ["encryption", "bloom", "merkle", "email", "security"]
DISTANCES = [0, 1, 2]
TOP_K     = 5
REPEATS   = 10
# ----------------

# 自动生成输出文件名
base_name = "benchmark_results.csv"
if not os.path.exists(base_name):
    output_csv = base_name
else:
    idx = 1
    while True:
        candidate = f"benchmark_results_{idx}.csv"
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
    writer.writerow(["query", "d", "avg_latency_ms"])

    for q in QUERIES:
        for d in DISTANCES:
            tot = 0
            for _ in range(REPEATS):
                # 模糊扩展 + Bloom 陷门
                Wq = set(get_close_matches(q, vocab, n=50, cutoff=0.8)) | {q}
                bf = BloomFilter(m, k_hash)
                for w in Wq:
                    bf.add(w)
                td = [prf(SK, str(pos)).hex() for pos in bf.bit_positions()]
                # 测时
                t0 = time.time()
                requests.post(f"{SERVER}/search", json={"trapdoor": td, "k": TOP_K})
                t1 = time.time()
                tot += (t1 - t0) * 1000
            avg_ms = round(tot / REPEATS, 2)
            writer.writerow([q, d, avg_ms])

print(f"Benchmark complete → {output_csv}")
