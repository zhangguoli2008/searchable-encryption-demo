import os
import json
import glob
from utils.crypto_utils import prf, encrypt
from utils.data_structures import BloomFilter, MerkleTree

# 简单分词
import re
WORD_RE = re.compile(r"[a-zA-Z]+")

# 演示用模糊扩展 (d=1): identity only，真实可用 difflib.get_close_matches()
def fuzzy_expand(words, vocab, d=1):
    # TODO: LSH-based 扩展，这里只返回原词
    return set(words)

if __name__ == '__main__':
    os.makedirs('server', exist_ok=True)
    # 1. 加载参数
    with open('server/params.json') as f:
        params = json.load(f)
    SK = bytes.fromhex(params['key'])
    m, k, d = params['m'], params['k'], params['d']

    # 2. 读取文档
    files = glob.glob('data/docs/*.txt')
    tag_map = {}    # tag(hex)-> list of doc_ids
    keywords = set()

    for path in files:
        doc_id = os.path.basename(path)
        text = open(path).read()
        words = [w.lower() for w in WORD_RE.findall(text)]
        words = list(set(words))
        keywords.update(words)

        # 索引构建：BloomFilter
        bf = BloomFilter(m, k)
        W_hat = fuzzy_expand(words, keywords, d)
        for w in W_hat:
            bf.add(w)
        for i in bf.bit_positions():
            tag = prf(SK, str(i)).hex()
            tag_map.setdefault(tag, []).append(doc_id)

    # 3. 加密索引
    enc_index = {}
    for tag, docs in tag_map.items():
        blob = encrypt(SK, json.dumps(docs).encode())
        enc_index[tag] = blob.hex()

    # 4. 保存索引和关键词
    with open('server/index.json', 'w') as f:
        json.dump(enc_index, f)
    with open('server/keywords.json', 'w') as f:
        json.dump(sorted(keywords), f)

    # 5. 构建 Merkle 树
    leaves = []
    tag_list = sorted(enc_index.keys())
    for tag in tag_list:
        leaf = bytes.fromhex(tag) + bytes.fromhex(enc_index[tag])
        leaves.append(leaf)
    mt = MerkleTree(leaves)
    root = mt.root().hex()

    # 保存 Merkle
    with open('server/merkle_root.txt', 'w') as f:
        f.write(root)
    mt.save('server/merkle_tree.pkl')
    print('[*] 索引构建完成：server/index.json, keywords.json, merkle_root.txt')