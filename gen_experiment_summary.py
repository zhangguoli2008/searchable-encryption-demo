#!/usr/bin/env python3
# gen_experiment_summary.py
# 自动生成索引大小、更新延迟与陷门大小的对比表格数据

import os
import time
import json
import statistics
from utils.crypto_utils import prf  # 生成Trapdoor用
from utils.data_structures import BloomFilter
# 需要自行实现或引入update_index_*函数，用于测试更新延迟
# from update_sse import update_index_sse
# from update_abse import update_index_abse

# 配置：各方案索引文件路径 & 更新函数占位
SCHEMES = {
    '本方案': {
        'index_path': 'server/index.json',
        # 'update_func': update_index_sse,  # 单用户 SSE 更新函数
    },
    '方案A': {
        'index_path': 'server/index.json',
        # 'update_func': update_index_sse_no_validate,
    },
    '方案B': {
        'index_path': 'server/index.json',
        # 'update_func': update_index_abse,
    },
}
# Trapdoor 示例关键词
TEST_KEYWORD = 'example'
# BloomFilter 参数（可从 params.json 动态加载）
PARAMS = 'server/params.json'
params = json.load(open(PARAMS))
SK = bytes.fromhex(params['key'])
m, k_hash = params['m'], params['k']

# 测量索引大小 (MB)
def measure_index_size(path: str) -> float:
    size = os.path.getsize(path)
    return round(size / (1024*1024), 2)

# 测量更新延迟 (ms)
def measure_update_latency(update_func, repeats: int=10) -> float:
    times = []
    # 这里假设 update_func(test_doc_path) 执行一次索引更新
    dummy_doc = os.listdir('data/docs')[0]
    doc_path = os.path.join('data/docs', dummy_doc)
    for _ in range(repeats):
        t0 = time.perf_counter()
        update_func(doc_path)
        t1 = time.perf_counter()
        times.append((t1 - t0)*1000)
    return round(statistics.mean(times), 2)

# 测量陷门大小 (Bytes)
def measure_trapdoor_size(keyword: str) -> int:
    # 模糊查询扩展，可按需求调整
    Wq = {keyword}
    bf = BloomFilter(m, k_hash)
    for w in Wq:
        bf.add(w)
    td = [prf(SK, str(pos)).hex() for pos in bf.bit_positions()]
    # JSON 序列化后字节长度
    blob = json.dumps(td).encode('utf-8')
    return len(blob)

# 运行测量并输出
results = []
for name, cfg in SCHEMES.items():
    idx_size = measure_index_size(cfg['index_path'])
    # 若有更新函数，则测延迟，否则标记为 None
    if 'update_func' in cfg:
        upd_lat = measure_update_latency(cfg['update_func'], repeats=20)
    else:
        upd_lat = None
    td_size = measure_trapdoor_size(TEST_KEYWORD)
    results.append((name, idx_size, upd_lat, td_size))

# 打印结果表格
print("方案,索引大小(MB),更新延迟(ms),陷门大小(Bytes)")
for name, idx, ud, td in results:
    print(f"{name},{idx},{ud if ud is not None else '-'}, {td}")

# 可选：写入 CSV
out_file = 'summary_experiment.csv'
with open(out_file, 'w', newline='') as f:
    print("方案,索引大小(MB),更新延迟(ms),陷门大小(Bytes)", file=f)
    for name, idx, ud, td in results:
        print(f"{name},{idx},{ud if ud is not None else '-'}, {td}", file=f)
print(f"写入文件: {out_file}")
