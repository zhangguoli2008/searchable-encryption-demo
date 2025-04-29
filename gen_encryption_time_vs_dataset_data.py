#!/usr/bin/env python3
# gen_encryption_time_vs_dataset_data_improved.py

import os, csv, random, time
import sys
sys.path.append(os.getcwd())
from utils.crypto_utils import encrypt    # 你的 encrypt(key, plaintext)

# ——配置——
PARAMS = "server/params.json"              # 从这里拿 key
DOC_DIR = "data/docs"
STEPS   = 10
REPEATS = 5

# 1) 读取密钥
import json
with open(PARAMS) as f:
    key = bytes.fromhex(json.load(f)['key'])

# 2) 构造文档列表
all_files = [os.path.join(DOC_DIR,fn) for fn in os.listdir(DOC_DIR)]
random.shuffle(all_files)                  # 随机打乱
total = len(all_files)
sizes = [ max(1, int(total * i / STEPS)) for i in range(1, STEPS+1) ]

# 3) 预热：把所有文件先读一遍到内存
print("[*] Warming up I/O cache...")
cached = []
for path in all_files:
    with open(path, "rb") as f:
        cached.append(f.read())
print("[*] Warmup done.")

# 4) 开始测量
out = "encryption_vs_dataset.csv"
if os.path.exists(out):
    # 自动编号
    base, ext = os.path.splitext(out)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    out = f"{base}_{i}{ext}"

print(f"→ Writing: {out}")
with open(out, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["n_thousand", "encrypt_time_s"])

    for n in sizes:
        docs = cached[:n]
        print(f"[+] Encrypting {n} docs x{REPEATS} times …", end="", flush=True)

        durations = []
        for _ in range(REPEATS):
            t0 = time.perf_counter()
            for data in docs:
                encrypt(key, data)
            t1 = time.perf_counter()
            durations.append(t1 - t0)
        avg = round(sum(durations)/len(durations), 4)

        writer.writerow([round(n/1000, 2), avg])
        print(f" done: {avg:.4f}s")

print("All done.")
















# #!/usr/bin/env python3
# # gen_encryption_time_vs_dataset_data.py
# # 生成“图4.3”——Encryption Time vs Dataset Size
#
# import os, csv, time
# import sys
# sys.path.append(os.getcwd())
# from utils.crypto_utils import encrypt  # 假设 encrypt(key, plaintext) 返回密文
#
# # ——配置——
# KEY     = b'\x00'*16  # 或者从 params 里取
# all_docs = os.listdir("data/docs")
# total    = len(all_docs)
# steps    = 10
# sizes    = [ max(1,int(total*i/steps)) for i in range(1,steps+1) ]
# REPEATS  = 5
#
# base = "encryption_vs_dataset.csv"
# if not os.path.exists(base):
#     out_csv = base
# else:
#     k=1
#     while True:
#         cand = f"encryption_vs_dataset_{k}.csv"
#         if not os.path.exists(cand):
#             out_csv=cand; break
#         k+=1
#
# print("→ Writing:", out_csv)
# with open(out_csv, "w", newline="") as f:
#     w = csv.writer(f)
#     w.writerow(["n_thousand", "encrypt_time_s"])
#
#     for n in sizes:
#         docs = all_docs[:n]
#         print(f"Encrypting ~{n} docs ...")
#         durations = []
#         for _ in range(REPEATS):
#             t0 = time.time()
#             for filename in docs:
#                 with open(os.path.join("data/docs",filename),"rb") as ff:
#                     plaintext = ff.read()
#                 encrypt(KEY, plaintext)
#             t1 = time.time()
#             durations.append(t1-t0)
#         avg = round(sum(durations)/len(durations),4)
#         w.writerow([round(n/1000,1), avg])
#
# print("Done.")
