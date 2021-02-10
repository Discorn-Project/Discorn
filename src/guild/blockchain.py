import pycryptonight
import ecdsa
from Crypto.Hash import RIPEMD160
import hashlib
from log import Logger
import base58
import os
import time
import string
from merklelib import MerkleTree


def fast_hash(b):
    return pycryptonight.cn_fast_hash(b).hex()


class Block(Logger):
    """Block and header definition."""

    NONCE_SIZE = 4

    def __init__(self,
                 blockchain=None,
                 name='block',
                 height=0,
                 version=0,
                 coinbase=None,
                 corners=None,
                 timestamp=0,
                 previous_hash=pycryptonight.cn_slow_hash(b''),
                 nonce=(0).to_bytes(NONCE_SIZE, 'big')):
        super().__init__(f"{name} - {height} :")
        self.blockchain = blockchain
        self.version = version
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.coinbase = coinbase
        self._corners = [] if corners is None else corners
        self.merkle_tree = MerkleTree(self.corners, fast_hash)
        self.header = self.encode_header()
        self.hash = self.get_hash()

    @property
    def corners(self):
        return [self.coinbase] + self._corners

    def compute_tree(self, new_data=None):
        if new_data is None:
            self.merkle_tree = MerkleTree(self.corners, fast_hash)
        else:
            self.merkle_tree.extend(new_data)

    def encode_header(self):
        res = self.version.to_bytes(2, 'big')
        res += self.timestamp.to_bytes(8, 'big')
        res += len(self.corners).to_bytes(3, 'big')
        res += bytes.fromhex(self.merkle_tree.merkle_root)
        res += self.previous_hash
        res += self.nonce
        self.header = res
        return res

    def random_nonce(self):
        self.timestamp = time.time_ns()
        self.nonce = os.urandom(self.NONCE_SIZE)

    def mine(self, difficulty=4):
        while int.from_bytes(self.get_hash(), 'big') >= (1 << (256 - difficulty)):
            self.log(f"new hash : {self.hash.hex()}")
            self.random_nonce()
            self.encode_header()
        self.log(f"Mined !! : {self.hash.hex()}")

    def get_hash(self):
        self.hash = pycryptonight.cn_slow_hash(self.header, 4)
        return self.hash


class BlockChain(Logger):
    """BlockChain data model."""

    def __init__(self, name='Main'):
        super().__init__(name)
        self.block_hashes = []
        self.blocks = {}
        self.corners = {}
        self.unconfirmed_corners = {}

    def new_head(self, block):
        self.block_hashes.append(block.hash)
        self.blocks.update({block.hash: block})
        self.log(f"New head : [{len(self.blocks)}] - {block.hash.hex()}")

    def get_block_template(self):
        block = Block(self,
                      corners=[corner for corner in self.unconfirmed_corners.items()],
                      timestamp=time.time_ns(),
                      previous_hash=self.block_hashes[-1])


if __name__ == '__main__':
    chain = BlockChain()
    genesis = Block(chain, name='Main')
    genesis.random_nonce()
    genesis.encode_header()
    genesis.get_hash()
    chain.new_head(genesis)
