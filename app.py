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

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_votes = []
        self.difficulty = '00'  # Proof-of-work difficulty
        self.max_votes = 5
          # Number of votes to propose a block

        self.create_genesis_block()
        self.proposed_block = None  # To hold the proposed block
    
    
    def create_genesis_block(self):
        """Create the genesis block with proper proof-of-work."""
        genesis_votes = []  # No votes for the genesis block
        genesis_timestamp = time()  # Timestamp for the genesis block
        previous_hash = '0' * 64  # Placeholder previous hash for the genesis block

        # Perform proof-of-work for the genesis block
        nonce, current_hash = self.proof_of_work(previous_hash, genesis_votes, genesis_timestamp)

        # Create the genesis block with the computed hash
        genesis_block = {
            'index': 1,
            'votes': genesis_votes,
            'nonce': nonce,
            'previous_hash': previous_hash,
            'timestamp': genesis_timestamp,
            'current_hash': current_hash,
        }

        self.chain.append(genesis_block) 

    def create_block(self, nonce, previous_hash, block_timestamp):
        """Create a new block with the provided timestamp."""

        # Create the block with the provided timestamp
        block = {
            'index': len(self.chain) + 1,
            'votes': self.current_votes,
            'nonce': nonce,
            'previous_hash': previous_hash,
            'timestamp': block_timestamp,  # Use the fixed block timestamp
            'current_hash': self.hash_block(nonce, previous_hash, self.current_votes, block_timestamp),
        }

        # Assign the same timestamp to all votes in this block
        for vote in self.current_votes:
            vote['timestamp'] = block_timestamp

        self.current_votes = []  # Clear the current votes
        self.chain.append(block)  # Append the block to the chain
        return block

    
    
    def hash_block(self, nonce, previous_hash, votes, block_timestamp):
        """Create a SHA-256 hash of a block."""
        block_string = json.dumps({
            'nonce': nonce,
            'previous_hash': previous_hash,
            'votes': votes,
            'timestamp': block_timestamp,  # Use the fixed timestamp
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


    
    
    
    def proof_of_work(self, previous_hash, votes, block_timestamp):
        """Simple proof-of-work algorithm."""
        nonce = 0
        while True:
            # Hash the block with the fixed block timestamp
            hash_value = self.hash_block(nonce, previous_hash, votes, block_timestamp)
            if hash_value[:len(self.difficulty)] == self.difficulty:
                return nonce, hash_value
            nonce += 1

    
    
    def add_vote(self, voter_id, candidate, voter_name):
        """
        Add a vote to the current_votes list.
        :param voter_id: Unique ID of the voter.
        :param candidate: Candidate chosen by the voter (Ethereum or Bitcoin).
        :param voter_name: Name of the voter.
        :return: Response indicating success or failure.
        """
        # Check if the candidate is valid
        if candidate not in ['Ethereum', 'Bitcoin']:
            return jsonify({'error': 'Invalid candidate'}), 400

        # Check if the voter has already voted by iterating through the entire blockchain
        for block in self.chain:
            for vote in block['votes']:
                if vote['voter_id'] == voter_id:
                    return jsonify({'error': 'Voter has already voted'}), 400

        # If the voter has not voted, add the vote to the current transaction list
        vote = {
            'voter_id': voter_id,
            'candidate': candidate,
            'voter_name': voter_name,  # Include voter name
            'timestamp': time()
        }
        self.current_votes.append(vote)

        # Once we have the max number of votes, propose a block
        if len(self.current_votes) >= self.max_votes:
            self.propose_block()

        return True

    def propose_block(self):
        """Propose a new block after collecting enough votes."""
        last_block = self.last_block
        previous_hash = last_block['current_hash']

        # Set the block timestamp ONCE here
        block_timestamp = time()

        # Perform proof-of-work for the proposed block
        nonce, current_hash = self.proof_of_work(previous_hash, self.current_votes, block_timestamp)

        # Create the proposed block with the timestamp
        self.create_block(nonce, previous_hash, block_timestamp)



# WTF IS THIS BRO 
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
    """
    Retrieve and display detailed information for a specific block by index.
    """
    # Find the block with the matching index
    block = next((block for block in blockchain.chain if block['index'] == block_index), None)

    if block is None:
        # If the block is not found, return a JSON error response
        return jsonify({'error': 'Block not found'}), 404

    # Pass block details to the block_detail.html template
    return render_template('block_detail.html', block=block)




@app.route('/voters', methods=['GET'])
def voters():
    return render_template('voters.html')  # Render the voter input page



@app.route('/vote', methods=['POST'])
def new_vote():
    data = request.get_json()
    voter_id = data.get('voter_id')
    candidate = data.get('candidate')
    voter_name = data.get('voter_name')  # Get voter_name from the request

    if not voter_id or not candidate or not voter_name:
        return jsonify({'error': 'Missing voter_id, candidate, or voter_name'}), 400

    # Add the vote and check if a block needs to be proposed
    result = blockchain.add_vote(voter_id, candidate, voter_name)
    if isinstance(result, tuple):
        return result

    return jsonify({'message': f"Vote added successfully for {voter_name}!"}), 201




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




@app.route('/results', methods=['GET'])
def results():
    # Initialize a dictionary to count votes for each candidate
    vote_count = {'Ethereum': 0, 'Bitcoin': 0}

    # Iterate through all blocks in the blockchain and count the votes
    for block in blockchain.chain:
        for vote in block['votes']:
            if vote['candidate'] in vote_count:
                vote_count[vote['candidate']] += 1

    # Calculate the total number of votes
    total_votes = vote_count['Ethereum'] + vote_count['Bitcoin']

    # Calculate the percentage of votes for each candidate
    if total_votes > 0:
        ethereum_percentage = (vote_count['Ethereum'] / total_votes) * 100
        bitcoin_percentage = (vote_count['Bitcoin'] / total_votes) * 100
    else:
        ethereum_percentage = bitcoin_percentage = 0  # Handle case where there are no votes

    # Render the results page with vote counts and percentages
    return render_template('results.html', 
                           vote_count=vote_count,
                           ethereum_percentage=ethereum_percentage,
                           bitcoin_percentage=bitcoin_percentage)



# Start the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
