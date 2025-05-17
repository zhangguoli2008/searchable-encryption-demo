import os
import json
import glob
import re
import sqlite3
from utils.crypto_utils import prf, encrypt
from utils.data_structures import BloomFilter, MerkleTree

# 分词正则
WORD_RE = re.compile(r"[a-zA-Z]+")

# 实现模糊匹配
def fuzzy_expand(words, vocab, d=1):
    # TODO: 实现真正的模糊匹配
    return set(words)

if __name__ == '__main__':
    os.makedirs('server', exist_ok=True)

    # 1. 加载参数
    with open('server/params.json', 'r') as f:
        params = json.load(f)
    SK = bytes.fromhex(params['key'])
    m, k, d = params['m'], params['k'], params['d']

    # 2. 初始化 SQLite 存储 tag_map
    db_path = 'server/tag_map.db'
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE IF NOT EXISTS tag_map(tag TEXT, doc_id TEXT)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_tag ON tag_map(tag)')
    conn.commit()

    # 3. 处理文档并写入数据库
    files = glob.glob('data/docs/*.txt')
    print(f"[*] 总共 {len(files)} 个文档，开始构建索引...")
    keywords = set()

    for idx, path in enumerate(files, 1):
        doc_id = os.path.basename(path)
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        words = {w.lower() for w in WORD_RE.findall(text)}
        keywords.update(words)

        bf = BloomFilter(m, k)
        for w in fuzzy_expand(words, keywords, d):
            bf.add(w)

        for i in bf.bit_positions():
            tag = prf(SK, str(i)).hex()
            conn.execute(
                'INSERT INTO tag_map(tag, doc_id) VALUES (?, ?)',
                (tag, doc_id)
            )

        if idx % 5000 == 0:
            conn.commit()
            print(f"[*] 已处理 {idx} / {len(files)} 文档...")
    conn.commit()

    # 4. 加密并流式写入 index.json
    print("[*] 开始加密并写入 index.json...")
    out_path = 'server/index.json'
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write('{')
        first = True
        for (tag,) in conn.execute('SELECT DISTINCT tag FROM tag_map'):
            docs = [r[0] for r in conn.execute(
                'SELECT doc_id FROM tag_map WHERE tag=?', (tag,)
            )]
            blob = encrypt(SK, json.dumps(docs).encode()).hex()
            if not first:
                out.write(',')
            out.write(json.dumps(tag) + ':' + json.dumps(blob))
            first = False
        out.write('}')

    # 5. 保存关键词列表
    print("[*] 保存 keywords.json...")
    with open('server/keywords.json', 'w', encoding='utf-8') as f:
        json.dump(sorted(keywords), f)

    # 6. 构建 Merkle 树
    print("[*] 构建 Merkle 树...")
    # 从 index.json 读取所有加密 blob
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
    print("""[*] 索引构建完成，可直接使用！
  - server/index.json
  - server/keywords.json
  - server/merkle_root.txt
  - server/merkle_tree.pkl""")
