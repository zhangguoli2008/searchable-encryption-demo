import os
import json
import glob
import re
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # 进度条神器
from utils.crypto_utils import prf, encrypt
from utils.data_structures import BloomFilter, MerkleTree

# 分词正则
WORD_RE = re.compile(r"[a-zA-Z]+")
LOCK = threading.Lock()


def fuzzy_expand(words, vocab, d=1):
    return set(words)


def process_document(path, SK, m, k, d):
    """处理单个文档，提取关键词并生成 BloomFilter tags"""
    doc_id = os.path.basename(path)
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    words = {w.lower() for w in WORD_RE.findall(text)}
    bf = BloomFilter(m, k)
    for w in fuzzy_expand(words, words, d):
        bf.add(w)
    tags = []
    for i in bf.bit_positions():
        tag = prf(SK, str(i)).hex()
        tags.append((tag, doc_id))
    return words, tags


if __name__ == '__main__':
    os.makedirs('server', exist_ok=True)

    # 1. 加载系统参数
    with open('server/params.json', 'r') as f:
        params = json.load(f)
    SK = bytes.fromhex(params['key'])
    m, k, d = params['m'], params['k'], params['d']

    # 2. 初始化 SQLite
    db_path = 'server/tag_map.db'
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS tag_map(tag TEXT, doc_id TEXT)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tag ON tag_map(tag)')
    conn.commit()

    # 3. 获取文档列表
    files = glob.glob('data/docs/*.txt')
    total_files = len(files)
    print(f"[*] 总共 {total_files} 个文档，开始并行构建索引...")

    all_keywords = set()
    insert_buffer = []
    processed = 0

    with ThreadPoolExecutor(max_workers=os.cpu_count() * 3) as executor:
        futures = {executor.submit(process_document, path, SK, m, k, d): path for path in files}

        # 加入进度条
        for future in tqdm(as_completed(futures), total=total_files, desc="构建索引中", ncols=80):
            try:
                words, tags = future.result()
                with LOCK:
                    all_keywords.update(words)
                    insert_buffer.extend(tags)
                    processed += 1
                    if len(insert_buffer) >= 1000:
                        cursor.executemany('INSERT INTO tag_map(tag, doc_id) VALUES (?, ?)', insert_buffer)
                        conn.commit()
                        insert_buffer.clear()
            except Exception as e:
                print(f"[!] 处理文件出错 {futures[future]}: {e}")

    # 插入剩余未提交的
    if insert_buffer:
        cursor.executemany('INSERT INTO tag_map(tag, doc_id) VALUES (?, ?)', insert_buffer)
        conn.commit()

    # 4. 加密生成 index.json
    print("[*] 开始加密并生成 index.json...")
    out_path = 'server/index.json'
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write('{')
        first = True
        for (tag,) in tqdm(cursor.execute('SELECT DISTINCT tag FROM tag_map'), desc="加密索引中", ncols=80):
            docs = [r[0] for r in cursor.execute('SELECT doc_id FROM tag_map WHERE tag=?', (tag,))]
            blob = encrypt(SK, json.dumps(docs).encode()).hex()
            if not first:
                out.write(',')
            out.write(json.dumps(tag) + ':' + json.dumps(blob))
            first = False
        out.write('}')

    # 5. 保存关键词列表
    print("[*] 保存关键词列表 keywords.json...")
    with open('server/keywords.json', 'w', encoding='utf-8') as f:
        json.dump(sorted(all_keywords), f)

    # 6. 构建 Merkle 树
    print("[*] 构建 Merkle 树...")
    with open(out_path, 'r', encoding='utf-8') as f:
        enc_index = json.load(f)
    leaves = []
    for tag in sorted(enc_index.keys()):
        blob_hex = enc_index[tag]
        leaves.append(bytes.fromhex(tag) + bytes.fromhex(blob_hex))

    mt = MerkleTree(leaves)
    root = mt.root().hex()
    with open('server/merkle_root.txt', 'w', encoding='utf-8') as f:
        f.write(root)
    mt.save('server/merkle_tree.pkl')

    conn.close()

    print("""[*] ✅ 索引构建完成！
  - server/index.json
  - server/keywords.json
  - server/merkle_root.txt
  - server/merkle_tree.pkl
""")
