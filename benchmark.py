# benchmark.py
import time, csv, requests
from utils.crypto_utils import prf
from utils.data_structures import BloomFilter
from difflib import get_close_matches

SERVER = "http://192.168.228.141:5000"
QUERIES   = ["encryption", "bloom", "merkle", "email", "security"]
DISTANCES = [0, 1, 2]
TOP_K     = 5
REPEATS   = 10

# 拉参与词表
params = requests.get(f"{SERVER}/params").json()
SK = bytes.fromhex(params['key'])
m, k_hash = params['m'], params['k']
vocab = requests.get(f"{SERVER}/vocabulary").json()

with open("benchmark_results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["query", "d", "avg_latency_ms"])
    for q in QUERIES:
        for d in DISTANCES:
            tot = 0
            for _ in range(REPEATS):
                # 模糊扩展+Bloom陷门
                Wq = set(get_close_matches(q, vocab, n=50, cutoff=0.8)) | {q}
                bf = BloomFilter(m, k_hash)
                for w in Wq: bf.add(w)
                td = [prf(SK, str(i)).hex() for i in bf.bit_positions()]
                t0 = time.time()
                requests.post(f"{SERVER}/search",
                              json={"trapdoor": td, "k": TOP_K})
                t1 = time.time()
                tot += (t1 - t0) * 1000
            writer.writerow([q, d, round(tot/REPEATS, 2)])
print("Benchmark complete → benchmark_results.csv")
