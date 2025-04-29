#!/usr/bin/env python3
# gen_search_time_vs_dataset_data.py
# 生成“图4.2”——Search Time vs Dataset Size

import os, csv, time, requests
import sys
sys.path.append(os.getcwd())
from utils.crypto_utils import prf
from utils.data_structures import BloomFilter
from difflib import get_close_matches

# ——配置——
SERVER    = "http://192.168.228.142:5000"
QUERY     = "encryption"
TOP_K     = 5
REPEATS   = 10

# 假设 data/docs 下已有 N 个文档，我们按千为单位切分
all_docs = os.listdir("data/docs")
total = len(all_docs)
steps = 10
sizes = [ max(1, int(total*i/steps)) for i in range(1, steps+1) ]

# 输出
base = "search_vs_dataset.csv"
if not os.path.exists(base):
    out_csv = base
else:
    n=1
    while True:
        cand = f"search_vs_dataset_{n}.csv"
        if not os.path.exists(cand):
            out_csv=cand; break
        n+=1

print("→ Writing:", out_csv)
with open(out_csv, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["n_thousand", "search_time_ms"])

    # 拉参数、词表
    params = requests.get(f"{SERVER}/params").json()
    SK = bytes.fromhex(params['key'])
    m, k_hash = params['m'], params['k']
    vocab = requests.get(f"{SERVER}/vocabulary").json()

    for n in sizes:
        docs = all_docs[:n]
        print(f"Dataset ~{n} docs ...")
        times = []
        for _ in range(REPEATS):
            # 构造 trapdoor
            Wq = set(get_close_matches(QUERY, vocab, n=50, cutoff=0.8))|{QUERY}
            bf = BloomFilter(m,k_hash)
            for w_word in Wq: bf.add(w_word)
            td = [prf(SK,str(pos)).hex() for pos in bf.bit_positions()]

            t0 = time.time()
            requests.post(f"{SERVER}/search", json={"trapdoor": td, "k": TOP_K})
            t1 = time.time()
            times.append((t1-t0)*1000)
        avg = round(sum(times)/len(times),2)
        w.writerow([round(n/1000,1), avg])

print("Done.")
