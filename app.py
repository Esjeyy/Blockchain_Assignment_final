import hashlib
import json
from time import time
from flask import Flask, render_template, request, jsonify
from uuid import uuid4
from datetime import datetime

# Blockchain implementation
class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_votes = []
        self.difficulty = '00'  # Proof-of-work difficulty

        # Create the genesis block
        self.create_block(previous_hash='0' * 64, nonce=1)

    def create_block(self, nonce, previous_hash):
        # Create a new block
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'votes': self.current_votes,
            'nonce': nonce,
            'previous_hash': previous_hash,
            'current_hash': self.hash_block(nonce, previous_hash, self.current_votes),
        }
        self.current_votes = []  # Clear the current votes
        self.chain.append(block)  # Append the block to the chain
        return block

    def hash_block(self, nonce, previous_hash, votes):
        # Create a SHA-256 hash of a block
        block_string = json.dumps({
            'nonce': nonce,
            'previous_hash': previous_hash,
            'votes': votes,
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, previous_hash, votes):
        # Simple proof-of-work algorithm
        nonce = 0
        while True:
            hash_value = self.hash_block(nonce, previous_hash, votes)
            if hash_value[:len(self.difficulty)] == self.difficulty:
                return nonce, hash_value
            nonce += 1

    def add_vote(self, voter_id, candidate):
        # Add a vote to the current transactions
        vote = {'voter_id': voter_id, 'candidate': candidate, 'timestamp': time()}
        self.current_votes.append(vote)
        return True

    @property
    def last_block(self):
        # Return the last block in the chain
        return self.chain[-1]

# Flask app setup
app = Flask(__name__)
blockchain = Blockchain()
node_identifier = str(uuid4()).replace('-', '')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/blockchain', methods=['GET'])
def display_blockchain():
    return render_template('blockchain.html', chain=blockchain.chain)

@app.route('/vote', methods=['POST'])
def new_vote():
    data = request.get_json()
    voter_id = data.get('voter_id')
    candidate = data.get('candidate')

    if not voter_id or not candidate:
        return jsonify({'error': 'Missing voter_id or candidate'}), 400

    blockchain.add_vote(voter_id, candidate)
    return jsonify({'message': 'Vote added successfully'}), 201

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    previous_hash = last_block['current_hash']

    # Perform proof-of-work
    nonce, current_hash = blockchain.proof_of_work(previous_hash, blockchain.current_votes)

    # Create the new block
    block = blockchain.create_block(nonce, previous_hash)

    return jsonify({
        'message': 'Block mined successfully',
        'block': block
    }), 200



@app.template_filter('to_datetime')
def to_datetime_filter(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
