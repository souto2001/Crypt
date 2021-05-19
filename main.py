# xCode ^0.0.0;
# Zaaf: https://github.com/souto2001

# This code is still in BETA

import datetime
import hashlib
import json
from flask import Flask, json, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

node = 'http://127.0.0.1:5000'

# Blockchain
class BlockChain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.created_block(proof = 1, previous_hash = '0')
        self.nodes = set()
    
    def create_block(self, proof, previous_hash):
        block = {
            'index': len (self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previus_hash': previous_hash,
            'transaction': self.transactions
        }
        self.transactions = []
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest() 
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
            return new_proof

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len (chain):
            block = chain(block_index)
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return False
    
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, adress):
        parsed_url = urlparse(adress)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = request.get(f'http://{node}/get_chain')  # http:127.0.0.1:5000/get_chain
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return False
        return True

# Creating adress for node on port 5000
node_adress = str(uuid4().replace('-', ''))

# Creating a BlockChain
blockchain = BlockChain()

# Flask (webapp)
app = Flask(__name__)

"""
"@app"
"""
# Mining new block
@app.route('/mine_block', methods=['GET'])

def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_adress, receiver = '', amount = 10)
    block = blockchain.create_block(proof, previous_hash)
    response = {
        'message': 'Congratulations, you mine a block:',
        'index': block['index'],
        'timestamp':block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'transactions': block['transactions']
    }
    return jsonify(response), 200 # OK

# Getting the full blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200 # OK

# Check if blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'The block Chain is valid.'}
    else:
        response = {'message': 'The block Chain is not valid.'}
    return jsonify(response), 200 # OK

# Adding a new transaction
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400 # BAD REQUEST
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'This transaction will be add to the block {index}'}
    return jsonify(response), 201 # Created

# Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('node')
    if  nodes is None:
        return 'No node', 400 # Error
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All nodes connect',
                'Total nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201 # OK

# Replace for longest chain IF NECESSARY
@app.route('/replace', methods = ['GET'])
def replace_chain():
    chain_replace = blockchain.get_chain_replace()
    if chain_replace:
        response = {'message': 'The node had a different chains so the chains was replace',
                    'new_chain': blockchain.chain
        }
    else:
        response = {'message': 'All good',
                    'chain': blockchain.chain
        }
    return jsonify(response), 200 # OK

"""
if __name__ == '__main__':
    app.run()
"""
