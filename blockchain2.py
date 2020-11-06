import time
import hashlib

"""
Logic:
1. Create block 
    (1) Initilize index, nonce 
    (2) Insert previous hash
    (3) Extract existing transactions from transaction pool
2. Upload to blockchain
    (1) Create block
    (2) Find the suitable nonce. (PoW)
    (3) Clear transaction pool and upload to blockchain
    (4) Send to other nodes
"""


class Block(object):

    def __init__(self, index, nonce, previous_hash, transactions, timestamp=None):
        self.index = index
        self.nonce = nonce
        self.previous_hash = previous_hash
        self.timestamp = timestamp or time.time()
        self.transactions = transactions
        self.transactions_hash = self._calculate_merkle_tree_hash()


    def get_block_hash(self):
        block_string = "{}{}{}{}{}".format(self.index, self.nonce, self.previous_hash, self.transactions_hash, self.timestamp)
        return hashlib.sha256(block_string.encode()).hexdigest()


    def get_block_dict(self):
        block_dict = {
            "index": self.index,
            "nonce": self.nonce,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "transactions_hash": self.transactions_hash
        }
        return block_dict


    def __repr__(self):
        return "{} - {} - {} - {} - {}".format(self.index, self.nonce, self.previous_hash, self.transactions_hash, self.timestamp)


    def _calculate_merkle_tree_hash(self):
        if len(self.transactions) == 0:
            return 0
        else:
            hash_list = []
            for i in range(len(self.transactions)):
                ordered_transactions = sorted(self.transactions[i].items(), key=lambda d:d[0])
                hash_list.append(hashlib.sha256(str(ordered_transactions).encode()).hexdigest())
            while len(hash_list) != 1:
                temp_hash_list = []
                # simply add two hash, and then calculate the hash of the sum
                for j in range(0, len(hash_list), 2):
                    if j + 1 == len(hash_list):
                        temp_hash_list.append(hash_list[-1])
                    else:
                        temp_hash_list.append(hashlib.sha256(hash_list[j].encode() + hash_list[j+1].encode()).hexdigest())
                hash_list = temp_hash_list
            return hash_list[0]



class BlockChain(object):

    def __init__(self):
        self.chain = []
        self.transaction_pool = []
        self.nodes = set()
        self._create_genesis_block()

        # difficulty for PoW
        self._difficulty = b"00000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"


    ########## Property Functions ##########

    def get_serialized_chain(self):
        return [vars(block) for block in self.chain]


    def get_last_block(self):
        return self.chain[-1]


    def get_diffcuilty(self):
        return self._difficulty


    ########## Utility Functions ##########

    def _create_genesis_block(self):
        genesis_block = Block(
            index = 0,
            nonce = 0,
            previous_hash = 0,
            transactions = []
        )
        self.chain.append(genesis_block)


    def create_new_block(self, nonce, previous_hash, transactions = []):
        block = Block(
            index = self.chain[-1].index + 1,
            nonce = nonce,
            previous_hash = previous_hash,
            transactions = transactions + list(self.transaction_pool)
        )
        return block


    def create_new_transaction(self, sender, receiver, amount, timestamp = None):
        # generate transaction
        temp_timestamp = timestamp or time.time()
        new_transaction = {
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
            'timestamp': temp_timestamp
        }

        # add transaction in own transaction pool
        if new_transaction not in self.transaction_pool:
            self.transaction_pool.append(new_transaction)

        return new_transaction


    def find_nonce(self, new_block):
        # PoW
        mining_count = 0
        while True:
            if new_block.get_block_hash().encode() < self._difficulty:
                break
            else:
                new_block.nonce += 1
                mining_count += 1
        return mining_count


    def mine_block(self, miner_address):
        # generate a new block and add coinbase
        last_block = self.get_last_block()
        new_block = self.create_new_block(0, last_block.get_block_hash(), [{
            'sender': 0,
            'receiver': miner_address,
            'amount': 1,
            'timestamp': time.time()
        }])

        # PoW
        print("\nStart mining...")
        mining_count = self.find_nonce(new_block)
        print("Mining times: %d" % mining_count)
        print("Result hash value: " + new_block.get_block_hash())
        print("Finish mining\n")

        # clean transaction pool
        temp_transaction_pool = self.transaction_pool.copy()
        for a_transaction in temp_transaction_pool:
            if a_transaction in new_block.transactions:
                self.transaction_pool.remove(a_transaction)

        # upload to blockchain
        self.chain.append(new_block)

        return new_block


    def add_node(self, address):
        self.nodes.add(address)
        return self.nodes

    # @staticmethod
    # def is_valid_block(block, previous_block):
    #     if previous_block.index + 1 != block.index:
    #         return False

    #     elif previous_block.get_block_hash != block.previous_hash:
    #         return False

    #     elif not BlockChain.is_valid_proof(block.proof, previous_block.proof):
    #         return False

    #     elif block.timestamp <= previous_block.timestamp:
    #         return False

    #     return True


    # @staticmethod
    # def is_valid_transaction():
    #     # Not Implemented
    #     pass

    # @staticmethod
    # def create_proof_of_work(previous_proof):
    #     """
    #     Generate "Proof Of Work"

    #     A very simple `Proof of Work` Algorithm -
    #         - Find a number such that, sum of the number and previous POW number is divisible by 7
    #     """
    #     proof = previous_proof + 1
    #     while not BlockChain.is_valid_proof(proof, previous_proof):
    #         proof += 1

    #     return proof

    # @staticmethod
    # def is_valid_proof(proof, previous_proof):
    #     return (proof + previous_proof) % 7 == 0



    # def is_valid_chain(self):
    #     """
    #     Check if given blockchain is valid
    #     """
    #     previous_block = self.chain[0]
    #     current_index = 1

    #     while current_index < len(self.chain):

    #         block = self.chain[current_index]

    #         if not self.is_valid_block(block, previous_block):
    #             return False

    #         previous_block = block
    #         current_index += 1

    #     return True

    # @staticmethod
    # def get_block_object_from_block_data(block_data):
    #     return Block(
    #         block_data['index'],
    #         block_data['proof'],
    #         block_data['previous_hash'],
    #         block_data['transactions'],
    #         timestamp=block_data['timestamp']
    #     )

if __name__ == "__main__":

    chain = BlockChain()
    print(chain.chain)
    chain.create_new_transaction("A", "B", 12)
    print(chain.transaction_pool)
    chain.create_new_transaction("B", "A", 12)
    print(chain.transaction_pool)
    # chain.mine_block("C")
    print(chain.chain)
    print(chain.transaction_pool)
    