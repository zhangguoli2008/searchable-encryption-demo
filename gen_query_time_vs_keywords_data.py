#!/usr/bin/env python3
# gen_query_time_vs_keywords_data.py
# 生成“图4.4”——Query Time vs Number of Keywords

import os, csv, time, requests
from difflib import get_close_matches
import sys
sys.path.append(os.getcwd())
from utils.crypto_utils import prf
from utils.data_structures import BloomFilter

# ——配置——
SERVER   = "http://192.168.228.142:5000"
QUERY    = "encryption"
TOP_K    = 5
REPEATS  = 10

# 从 vocab 中任取前 K 个关键字组合
params = requests.get(f"{SERVER}/params").json()
SK = bytes.fromhex(params['key'])
m, k_hash = params['m'], params['k']
vocab = requests.get(f"{SERVER}/vocabulary").json()

max_keys = 10
base = "query_vs_keywords.csv"
if not os.path.exists(base):
    out_csv = base
else:
    t=1
    while True:
        cand = f"query_vs_keywords_{t}.csv"
        if not os.path.exists(cand):
            out_csv=cand; break
        t+=1

print("→ Writing:", out_csv)
with open(out_csv, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["k_num", "query_time_s"])

    for k in range(1, max_keys+1):
        print(f"Query with {k} keywords ...")
        times = []
        for _ in range(REPEATS):
            # 从词表随机取 k 个词 + 主词
            Wq = set(get_close_matches(QUERY, vocab, n=50, cutoff=0.8))|{QUERY}
            extra = list(vocab[:100])[:k]  # 取前100个中前k个
            all_w = set(Wq) | set(extra)
            bf = BloomFilter(m,k_hash)
            for w_word in all_w: bf.add(w_word)
            td = [prf(SK,str(pos)).hex() for pos in bf.bit_positions()]

            t0 = time.time()
            requests.post(f"{SERVER}/search", json={"trapdoor": td, "k": TOP_K})
            t1 = time.time()
            times.append(t1-t0)
        avg = round(sum(times)/len(times),4)
        w.writerow([k, avg])

print("Done.")
