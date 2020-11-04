from uuid import uuid4

import requests
from flask import Flask, jsonify, url_for, request, render_template

from blockchain2 import BlockChain


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


@app.route('/receive-transaction', methods=['POST'])
def create_transaction():
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
    transaction_time = blockchain.create_new_transaction(**transaction_data)

    response = {
        'message': 'Transaction has been submitted successfully',
        'transaction_time': transaction_time
    }
    return jsonify(response)


@app.route("/registration", methods=['GET'])
def registration():
    first_node = "127.0.0.1:5000"
    resp = requests.post(first_node + '/receive-registration', json={'address': node_address}).json()
    return message


@app.route('/mine', methods=['GET'])
def mine():
    block = blockchain.mine_block(node_address)
    response = {
        'message': 'Successfully Mined the new Block',
        'block_data': block.get_block_dict()
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
    app.run(host=args.host, port=args.port, debug=True)
