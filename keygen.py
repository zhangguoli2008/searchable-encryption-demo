import os
import json
from utils.crypto_utils import generate_key

# 参数设置
PARAMS = {
    'm': 1000,    # Bloom filter 长度
    'k': 4,       # 哈希函数个数
    'd': 1        # 编辑距离阈值 (演示用)
}

if __name__ == '__main__':
    key = generate_key()
    data = {
        'key': key.hex(),
        'm': PARAMS['m'],
        'k': PARAMS['k'],
        'd': PARAMS['d']
    }
    os.makedirs('server', exist_ok=True)
    with open('server/params.json', 'w') as f:
        json.dump(data, f, indent=2)
    print('[*] 生成密钥和参数：server/params.json')