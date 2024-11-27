import hashlib
import json
from time import time
from flask import Flask, render_template, request, jsonify
from uuid import uuid4
from datetime import datetime
import random
import time as sleep_time

# Initialize Flask app
app = Flask(__name__)

# Validator classes
class Validator:
    def __init__(self, name):
        self.name = name
        self.valid = False

    def validate(self, proposed_block):
        # Simulate validation logic (random success/failure)
        self.valid = random.choice([True, False])
        return self.valid


class ValidatorA(Validator):
    def __init__(self):
        super().__init__("Validator A")


class ValidatorB(Validator):
    def __init__(self):
        super().__init__("Validator B")


class ValidatorC(Validator):
    def __init__(self):
        super().__init__("Validator C")


class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_votes = []
        self.difficulty = '00'  # Proof-of-work difficulty
        self.max_votes = 1
          # Number of votes to propose a block

        # Create the genesis block
        self.create_block(previous_hash='0' * 64, nonce=1)
        self.proposed_block = None  # To hold the proposed block

        # Create validator instances
        self.validators = [ValidatorA(), ValidatorB(), ValidatorC()]

    def create_block(self, nonce, previous_hash):
        # Compute the Merkle Root of the voter list
        voter_list = [vote['voter_id'] for vote in self.current_votes]
        voter_merkle_root = self.merkle_tree(voter_list)

        # Create a new block without timestamp
        block = {
            'index': len(self.chain) + 1,
            'votes': self.current_votes,
            'voter_merkle_root': voter_merkle_root,  # Add the Merkle Root
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
        # Add a vote to the current transaction list
        if candidate not in ['Ethereum', 'Bitcoin']:
            return jsonify({'error': 'Invalid candidate'}), 400

        vote = {'voter_id': voter_id, 'candidate': candidate, 'timestamp': time()}
        self.current_votes.append(vote)

        # Once we have 10 votes, propose a block
        if len(self.current_votes) >= self.max_votes:
            self.propose_block()

        return True

    def propose_block(self):
        """Propose a new block after collecting 10 votes"""
        last_block = self.last_block
        previous_hash = last_block['current_hash']

        # Perform proof-of-work for the proposed block
        nonce, current_hash = self.proof_of_work(previous_hash, self.current_votes)

        # Create the proposed block
        self.proposed_block = self.create_block(nonce, previous_hash)

    def validate_block(self):
        """Simulate the validation process with all validators"""
        validation_results = []
        for validator in self.validators:
            # Simulate the validation process with a 1-second delay
            sleep_time.sleep(1)
            result = validator.validate(self.proposed_block)
            validation_results.append(result)

        # Check if at least 51% of validators agree
        if validation_results.count(True) >= 2:
            # Block is valid, add to the chain
            self.chain.append(self.proposed_block)
            self.proposed_block = None  # Reset proposed block
            return True
        else:
            # Block is invalid, discard
            self.proposed_block = None
            return False

    def get_validators_status(self):
        """Get the validation status of all validators"""
        status = {}
        for validator in self.validators:
            status[validator.name] = 'Valid' if validator.valid else 'Invalid'
        return status

    def get_blocks_by_page(self, page_number, blocks_per_page=1):
        """Retrieve blocks for the current page"""
        start = (page_number - 1) * blocks_per_page
        end = start + blocks_per_page
        return self.chain[start:end]

    @property
    def last_block(self):
        # Return the last block in the chain
        return self.chain[-1]

    def merkle_tree(self, data_list):
        """Computes the Merkle Root of a list of data entries."""
        if not data_list:
            return None

        # Hash each entry in the data list
        hashed_list = [self.hash_data(entry) for entry in data_list]

        # Iteratively calculate parent hashes until one root hash is left
        while len(hashed_list) > 1:
            temp_list = []
            for i in range(0, len(hashed_list), 2):
                # Combine pairs of hashes
                if i + 1 < len(hashed_list):
                    combined = hashed_list[i] + hashed_list[i + 1]
                else:
                    combined = hashed_list[i]  # Handle odd number of elements
                temp_list.append(self.hash_data(combined))
            hashed_list = temp_list

        return hashed_list[0]  # The Merkle Root

    def hash_data(self, data):
        """Returns the SHA-256 hash of the input data."""
        return hashlib.sha256(data.encode()).hexdigest()

# Instantiate blockchain object
blockchain = Blockchain()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/blockchain', methods=['GET'])
def display_blockchain():
    # Get the page number from the query parameters (default is page 1)
    page_number = int(request.args.get('page', 1))  # Default to page 1 if no page is provided
    blocks_per_page = 10  # Number of blocks per page
    blocks = blockchain.get_blocks_by_page(page_number, blocks_per_page)  # Get blocks for the current page
    total_blocks = len(blockchain.chain)  # Total number of blocks
    total_pages = (total_blocks // blocks_per_page) + (1 if total_blocks % blocks_per_page > 0 else 0)

    # Render the blockchain page with the blocks and pagination info
    return render_template('blockchain.html', chain=blocks, total_pages=total_pages, current_page=page_number)

@app.route('/block/<int:block_index>', methods=['GET'])
def block_detail(block_index):
    # Retrieve the block details based on its index
    block = next((block for block in blockchain.chain if block['index'] == block_index), None)
    
    if block is None:
        # If block is not found, return an error message
        return jsonify({'error': 'Block not found'}), 404
    
    # Return the block details to the block_detail.html template
    return render_template('block_detail.html', block=block)

@app.route('/voters', methods=['GET'])
def voters():
    return render_template('voters.html')  # Render the voter input page

@app.route('/vote', methods=['POST'])
def new_vote():
    data = request.get_json()
    voter_id = data.get('voter_id')
    candidate = data.get('candidate')

    if not voter_id or not candidate:
        return jsonify({'error': 'Missing voter_id or candidate'}), 400

    # Add the vote and check if a block needs to be proposed
    blockchain.add_vote(voter_id, candidate)
    return jsonify({'message': 'Vote added successfully'}), 201

@app.route('/mine', methods=['POST'])
def mine():
    last_block = blockchain.last_block
    previous_hash = last_block['current_hash']

    # Perform proof-of-work to find the nonce
    nonce, current_hash = blockchain.proof_of_work(previous_hash, blockchain.current_votes)

    # Create a new block with the mined data
    block = blockchain.create_block(nonce, previous_hash)

    return jsonify({
        'message': 'Block mined successfully',
        'block': block
    }), 200

@app.route('/validate_block', methods=['GET'])
def validate_block():
    # Validate the proposed block
    if blockchain.validate_block():
        return jsonify({'message': 'Block validated and added to the blockchain!'}), 200
    else:
        return jsonify({'message': 'Block validation failed!'}), 400

@app.template_filter('to_datetime')
def to_datetime_filter(block_timestamp):
    """Format timestamp to human-readable date and time."""
    return datetime.fromtimestamp(block_timestamp).strftime('%Y-%m-%d %H:%M:%S')

# Start the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
