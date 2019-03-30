# Module 2 - Create a Cryptocurrency

# To be installed:
# Flask==0.12.2: pip install Flask==0.12.2
# Postman HTTP Client: https://www.getpostman.com/
# requests==2.18.4 pip install requests==2.18.4

# Importing the libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from urllib.parse import urlparse
from uuid import uuid4

# Part 1 - Building a Blockchain

class Blockchain:

    def __init__(self):
        self.chain = []
        self.hash_value = '0'
        self.transactions = []
        self.create_genesis_block(previous_hash='0')
        #self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
    
    
    def create_genesis_block(self,previous_hash):
        proof = self.proof_of_work(0)
        block = {'index':len(self.chain)+1,
                 'timestamp':str(datetime.datetime.now()),
                 'proof':proof,
                 'previous_hash':previous_hash,
                 'current_hash':self.hash_value,
                 'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block

    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'current_hash':self.hash_value,
                 'transactions': self.transactions}
        
        #Make the list empty after adding it into block
        self.transactions = []
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        hash_operation = '1'
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            #print(hash_operation + " --" + new_proof)
            if hash_operation[:4] == "0000":
                check_proof = True
            else:
                new_proof += 1
        self.hash_value = hash_operation
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            #if block['previous_hash'] != self.hash(previous_block):
            #    return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    #Crypto Create a transaction format, it will be dictionary
    def add_transaction(self,sender, receiver, amount):
        transaction_component = {'sender':sender,
                                  'receiver': receiver,
                                  'amount': amount}
        self.transactions.append(transaction_component)
        
        network = self.nodes
        for node in network:
            requests.post(url=f'http://{node}/add_transaction',data = jsonify(transaction_component))
        
        #return index of next block ==> last block + 1
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
        
    #Crypto
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    #Crypto
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
                
        #Check if it is not None
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
                    
                    

# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)

# Creating a Blockchain
blockchain = Blockchain()

#Crypto - Create address for port 5000
node_address = str(uuid4()).replace('-','')

# Mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    #Crypto
    blockchain.add_transaction(node_address,"User1",1) 
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions':block['transactions']}
    return jsonify(response), 200


#Crypto
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ["sender","receiver","amount"]
    
    if not all (key in json for key in transaction_keys):
        return "some elements of transaction are missing",400
    
    index = blockchain.add_transaction(json["sender"],json["receiver"],json["amount"])
    response = {"message": f"transaction will be added to block {index}"}
    return jsonify(response), 201


#Crypto Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "Empty node list", 400
    for node in nodes:
        blockchain.add_node(node)
    
    response = {"message": "All nodes added to blockchain network",
                "total_nodes":  list(blockchain.nodes) }
    return jsonify(response),201

#Crypto
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    
    if is_chain_replaced:
        response = {"message": "Chain is replaced by longer chain",
                    "replaced chain":blockchain.chain}
    else:
        response = {"message":"All good, Chain was not replaced, because it was up to date",
                   "actual chain":blockchain.chain}
    return jsonify(response),200

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200

@app.route('/test', methods = ['GET'])
def testthis():
    json = request.get_json()
    message = {"sender":"sender",
               "receiver":"rec",
               "amount":1}
    return jsonify(message)

# Running the app
app.run(host = '0.0.0.0', port = 5002)