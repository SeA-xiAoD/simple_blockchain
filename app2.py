from uuid import uuid4

import requests
from flask import Flask, jsonify, url_for, request, render_template

from blockchain2 import BlockChain
from  blockchain2 import Block


app = Flask(__name__)

blockchain = BlockChain()
node_address = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/receive-registration', methods=['POST'])
def register_node():
    """
    Receive other node's registration.
    register:
    {
        'address': node_address
    }
    """
    node_data = request.get_json()

    # add to current nodes
    current_nodes = blockchain.add_node(node_data.get('address'))

    response = {
        'message': 'New node has been added',
        'current_nodes': list(current_nodes),
    }
    return jsonify(response)


@app.route("/registration", methods=['GET'])
def registration():
    
    # register for fisrt node and get the exsiting node list 
    first_node = "127.0.0.1:5000"
    resp = requests.post('http://' + first_node + '/receive-registration', json={'address': node_address}).json()

    # add all nodes into current node set
    for address in resp["current_nodes"]:
        blockchain.add_node(address)

    # synchronize blockchain
    resp = requests.get('http://' + first_node + '/chain').json()
    blockchain.chain = []
    for a_json_block in resp["chain"]:
        # bulid new block and validate hash value
        temp_new_block = Block(
            a_json_block["index"],
            a_json_block["nonce"],
            a_json_block["previous_hash"],
            a_json_block["transactions"],
            a_json_block["timestamp"],
        )
        if temp_new_block.index == 0:
            blockchain.chain.append(temp_new_block)
        else:
            if temp_new_block.get_block_hash().encode() < blockchain.get_diffcuilty():
                blockchain.chain.append(temp_new_block)
    
    # broadcast the registration to existing nodes
    for address in blockchain.nodes:
        if address != first_node and address != node_address:
            _ = requests.post('http://' + address + '/receive-registration', json={'address': node_address}).json()

    response = {
        'message': 'Success registration',
    }
    return jsonify(response)


@app.route('/receive-transaction', methods=['POST'])
def receive_transaction():
    """
    transaction:
    {
        "sender": "address_1"
        "receiver": "address_2",
        "amount": amount
        "timestamp": timestamp
    }
    """
    transaction_data = request.get_json()
    new_transaction = blockchain.create_new_transaction(**transaction_data)

    response = {
        'message': 'Transaction has been received successfully',
        'transaction': new_transaction
    }
    return jsonify(response)


@app.route('/transaction', methods=['POST'])
def create_transaction():
    # create new transaction
    transaction_data = request.get_json()
    new_transaction = blockchain.create_new_transaction(**transaction_data)
    
    # broadcast transaction
    for address in blockchain.nodes:
        if address != node_address:
            _ = requests.post('http://' + address + '/receive-transaction', json=new_transaction).json()

    response = {
        'message': 'Transaction has been created successfully',
        'transaction': new_transaction
    }
    return jsonify(response)


@app.route('/receive-block', methods=['POST'])
def receive_block():
    # receive block
    new_block_data = request.get_json()["block"]
    new_block = Block(
        new_block_data["index"],
        new_block_data["nonce"],
        new_block_data["previous_hash"],
        new_block_data["transactions"],
        new_block_data["timestamp"],
    )
    
    # validate hash value
    if new_block.get_block_hash().encode() < blockchain.get_diffcuilty():
        # clean transaction pool
        temp_transaction_pool = blockchain.transaction_pool.copy()
        for a_transaction in temp_transaction_pool:
            if a_transaction in new_block.transactions:
                blockchain.transaction_pool.remove(a_transaction)

        # upload to blockchain
        blockchain.chain.append(new_block)
    
        response = {
            'message': 'Successfully received the new Block'
        }
    else:
        response = {
            'message': 'Illegal Block'
        }
    return jsonify(response)


@app.route('/mine', methods=['GET'])
def mine():
    # mining
    block = blockchain.mine_block(node_address)

    # broadcast
    block_dict = block.get_block_dict()
    block_data = {
        'block': block_dict
    }
    for address in blockchain.nodes:
        if address != node_address:
            _ = requests.post('http://' + address + '/receive-block', json=block_data).json()
    
    response = {
        'message': 'Successfully mined the new Block',
        'block_data': block_dict
    }
    return jsonify(response)


@app.route('/chain', methods=['GET'])
def get_full_chain():
    response = {
        'chain': blockchain.get_serialized_chain()
    }
    return jsonify(response)


@app.route('/transaction-pool', methods=['GET'])
def get_transaction_pool():
    response = {
        'transaction_pool': blockchain.transaction_pool
    }
    return jsonify(response)


@app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {
        'nodes': list(blockchain.nodes)
    }
    return jsonify(response)


@app.route('/current-address', methods=['GET'])
def get_current_address():
    response = {
        'current_address': node_address
    }
    return jsonify(response)


# @app.route('/sync-chain', methods=['GET'])
# def consensus():

#     def get_neighbour_chains():
#         neighbour_chains = []
#         for node_address in blockchain.nodes:
#             resp = requests.get(node_address + url_for('get_full_chain')).json()
#             chain = resp['chain']
#             neighbour_chains.append(chain)
#         return neighbour_chains

#     neighbour_chains = get_neighbour_chains()
#     if not neighbour_chains:
#         return jsonify({'message': 'No neighbour chain is available'})

#     longest_chain = max(neighbour_chains, key=len)  # Get the longest chain

#     if len(blockchain.chain) >= len(longest_chain):  # If our chain is longest, then do nothing
#         response = {
#             'message': 'Chain is already up to date',
#             'chain': blockchain.get_serialized_chain
#         }
#     else:  # If our chain isn't longest, then we store the longest chain
#         blockchain.chain = [blockchain.get_block_object_from_block_data(block) for block in longest_chain]
#         response = {
#             'message': 'Chain was replaced',
#             'chain': blockchain.get_serialized_chain
#         }

#     return jsonify(response)


if __name__ == '__main__':

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-host', default='127.0.0.1')
    parser.add_argument('-port', default=5000, type=int)
    args = parser.parse_args()

    node_address = args.host + ":" + str(args.port)
    blockchain.add_node(node_address)
    app.run(host=args.host, port=args.port, debug=True)
