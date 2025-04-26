from flask import Flask, request, jsonify, jsonify
import json
from utils.crypto_utils import decrypt
from utils.data_structures import MerkleTree

app = Flask(__name__)

# 加载服务器数据
with open('server/params.json') as f:
    params = json.load(f)
with open('server/index.json') as f:
    enc_index = json.load(f)
with open('server/keywords.json') as f:
    vocab = json.load(f)
with open('server/merkle_root.txt') as f:
    merkle_root = f.read().strip()
mt = MerkleTree.load('server/merkle_tree.pkl')
# tag到leaf index映射
tag_list = sorted(enc_index.keys())
tag2idx = {tag: i for i, tag in enumerate(tag_list)}

@app.route('/vocabulary', methods=['GET'])
def get_vocab():
    return jsonify(vocab)
@app.route('/params', methods=['GET'])
def get_params():
    # 演示用：把 key、m、k、d 等参数返回给客户端
    return jsonify(params)

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    trapdoor = data.get('trapdoor', [])
    k = data.get('k', 10)
    counts = {}
    proofs = {}

    # 解密并统计
    for tag in trapdoor:
        if tag in enc_index:
            blob = bytes.fromhex(enc_index[tag])
            docs = json.loads(decrypt(bytes.fromhex(params['key']), blob).decode())
            for d in docs:
                counts[d] = counts.get(d, 0) + 1
            # 生成 Merkle 证明
            idx = tag2idx[tag]
            proofs[tag] = [h.hex() for h in mt.get_proof(idx)]

    # Top-k
    results = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:k]
    resp = []
    for doc_id, score in results:
        resp.append({'doc_id': doc_id, 'score': score})

    return jsonify({
        'merkle_root': merkle_root,
        'results': resp,
        'proofs': proofs
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
