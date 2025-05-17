import pickle
import hashlib
from bitarray import bitarray
import mmh3

class BloomFilter:
    def __init__(self, m: int, k: int):
        self.m = m
        self.k = k
        self.bits = bitarray(m)
        self.bits.setall(False)

    def add(self, item: str):
        for seed in range(self.k):
            idx = mmh3.hash(item, seed) % self.m
            self.bits[idx] = True

    def bit_positions(self):
        return [i for i, b in enumerate(self.bits) if b]

    def __contains__(self, item: str) -> bool:
        for seed in range(self.k):
            if not self.bits[mmh3.hash(item, seed) % self.m]:
                return False
        return True

class MerkleTree:
    def __init__(self, leaves: list):
        # leaves: list of bytes
        self.levels = []
        self.build(leaves)

    def build(self, leaves: list):
        lvl = [hashlib.sha256(leaf).digest() for leaf in leaves]
        self.levels.append(lvl)
        while len(lvl) > 1:
            nxt = []
            for i in range(0, len(lvl), 2):
                left = lvl[i]
                right = lvl[i+1] if i+1 < len(lvl) else lvl[i]
                nxt.append(hashlib.sha256(left + right).digest())
            lvl = nxt
            self.levels.append(lvl)

    def root(self) -> bytes:
        return self.levels[-1][0] if self.levels else b''

    def get_proof(self, index: int) -> list:
        proof = []
        for lvl in self.levels[:-1]:
            sibling_idx = index^1
            sibling = lvl[sibling_idx] if sibling_idx < len(lvl) else lvl[index]
            proof.append(sibling)
            index //= 2
        return proof

    def save(self, path: str):
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path: str):
        with open(path, 'rb') as f:
            return pickle.load(f)