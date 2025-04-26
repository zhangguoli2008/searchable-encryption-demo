import json
import argparse
import requests
from utils.crypto_utils import prf
from utils.data_structures import BloomFilter
import re

# 简单分词
WORD_RE = re.compile(r"[a-zA-Z]+")

def fuzzy_expand(word, vocab, d):
    # 演示：使用 difflib 近似匹配
    from difflib import get_close_matches
    return get_close_matches(word, vocab, n=50, cutoff=0.8)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
     # parser.add_argument('--server', required=True, help='搜索服务器地址, e.g. http://127.0.0.1:5000')
    parser.add_argument(
        '--server',
        default='http://192.168.228.141:5000',
        help='搜索服务器地址 (默认: 192.168.228.141:5000)'
    )
    parser.add_argument('--query',  required=True, help='查询关键词')
    parser.add_argument('--d', type=int, default=1, help='编辑距离阈值')
    parser.add_argument('--k', type=int, default=5, help='Top-k 文档数')
    args = parser.parse_args()

    # 加载本地参数和词表
    # with open('server/params.json') as f:
    #     params = json.load(f)
    # 从服务端拉取加密参数，而非读本地文件
    params = requests.get(f"{args.server}/params").json()
    SK = bytes.fromhex(params['key'])
    m, k_hash, d = params['m'], params['k'], params['d']

    vocab = requests.get(f"{args.server}/vocabulary").json()

    # 1. 生成陷门
    q = args.query.lower()
    Wq = fuzzy_expand(q, vocab, args.d) + [q]
    bf = BloomFilter(m, k_hash)
    for w in Wq:
        bf.add(w)
    trapdoor = [prf(SK, str(i)).hex() for i in bf.bit_positions()]

    # 2. 发送查询
    resp = requests.post(f"{args.server}/search", json={'trapdoor': trapdoor, 'k': args.k}).json()
    print("Merkle Root:", resp['merkle_root'])
    print("Results:")
    for r in resp['results']:
        print(f"- {r['doc_id']}: score={r['score']}")