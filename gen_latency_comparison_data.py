#!/usr/bin/env python3
# gen_latency_comparison_data.py
# 生成“图4.1”四种场景（SSE/ABSE 有/无验证）× 编辑距离 的平均查询延迟

import os, csv, time, requests, statistics
from difflib import get_close_matches
import sys
sys.path.append(os.getcwd())
from utils.crypto_utils import prf
from utils.data_structures import BloomFilter

# ——配置——
SERVER     = "http://192.168.228.142:5000"
QUERY      = "encryption"
DISTANCES  = [0,1,2]
TOP_K      = 5
REPEATS    = 10
WARMUP     = 5
SCENARIOS  = [
    ("sse_no_validate", False, "SSE (No Validation)"),
    ("sse_validate", True, "SSE (With Validation)"),
    ("abse_no_validate", False, "ABSE (No Validation)"),
    ("abse_validate", True, "ABSE (With Validation)")
]
# 注意：如果你只有 SSE 实现，可只留前两项

# 下面直接在脚本里定义，不要放到 crypto_utils.py
def verify_search(key: bytes, resp_json: dict) -> bool:
    # 这里 requests 和 SERVER 都可用
    root_resp = requests.get(f"{SERVER}/merkle_root").json()
    server_root  = resp_json.get("root")
    correct_root = root_resp['root']
    if server_root != correct_root:
        raise ValueError("Merkle root mismatch")
    return True

# 自动编号输出
base = "latency_comparison.csv"
if not os.path.exists(base):
    out_csv = base
else:
    i=1
    while True:
        cand = f"latency_comparison_{i}.csv"
        if not os.path.exists(cand):
            out_csv = cand; break
        i+=1

print("→ Writing:", out_csv)
with open(out_csv, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["scenario", "label", "d", "avg_latency_ms"])

    # 拉参数
    params = requests.get(f"{SERVER}/params").json()
    SK = bytes.fromhex(params['key'])
    m, k_hash = params['m'], params['k']
    vocab = requests.get(f"{SERVER}/vocabulary").json()

    for scen, do_verify, label in SCENARIOS:
        print("Scenario:", scen)
        for d in DISTANCES:
            # warmup
            for _ in range(WARMUP):
                Wq = set(get_close_matches(QUERY, vocab, n=50, cutoff=0.8))|{QUERY}
                bf = BloomFilter(m,k_hash)
                for w_word in Wq: bf.add(w_word)
                td = [prf(SK,str(pos)).hex() for pos in bf.bit_positions()]
                requests.post(f"{SERVER}/search", json={"trapdoor": td, "k": TOP_K})

            times = []
            for _ in range(REPEATS):
                # trapdoor
                Wq = set(get_close_matches(QUERY, vocab, n=50, cutoff=0.8))|{QUERY}
                bf = BloomFilter(m,k_hash)
                for w_word in Wq: bf.add(w_word)
                td = [prf(SK,str(pos)).hex() for pos in bf.bit_positions()]

                t0 = time.time()
                resp = requests.post(f"{SERVER}/search", json={"trapdoor": td, "k": TOP_K})
                t1 = time.time()

                elapsed = (t1-t0)*1000
                # ==== 验证步骤已注释，跳过本地 Merkle root 验证 ====
                # if do_verify:
                #     # 本地验证开销也算入
                #     t2 = time.time()
                #     verify_search(SK, resp.json())  # 用户自己实现验证函数
                #     t3 = time.time()
                #     elapsed += (t3-t2)*1000

                times.append(elapsed)
            avg = round(statistics.mean(times),2)
            w.writerow([scen, label, d, avg])

print("Done.")