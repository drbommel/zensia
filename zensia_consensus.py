# Zensia Consensus Implementation (PoS-BFT)

import time
from enum import Enum
from typing import Dict, List, Tuple, Optional
from zensia_core_implementation import Hash, Address
from zensia_blockchain import Block

class ValidatorState(Enum):
    ACTIVE = "active"
    WAITING = "waiting"
    JAILED = "jailed"

class Validator:
    """Represents a validator in the Zensia network"""
    
    def __init__(self, address: Address, public_key: bytes, stake: int = 0):
        self.address = address
        self.public_key = public_key
        self.stake = stake
        self.state = ValidatorState.WAITING
        self.last_proposed_height = 0
        self.uptime = 1.0  # 100% initially
        
    def update_stake(self, amount: int) -> None:
        """Update the validator's stake"""
        self.stake += amount
        
        # Change state based on stake
        if self.stake <= 0:
            self.state = ValidatorState.WAITING
        elif self.state == ValidatorState.WAITING and self.stake > 0:
            self.state = ValidatorState.ACTIVE

class Vote:
    """A vote for a block in the BFT consensus"""
    
    def __init__(self, validator: Address, block_hash: Hash, height: int, round_num: int):
        self.validator = validator
        self.block_hash = block_hash
        self.height = height
        self.round = round_num
        self.timestamp = int(time.time())
        self.signature = None
    
    def sign(self, private_key: bytes) -> None:
        """Sign the vote with the validator's private key"""
        import hashlib
        message = f"{self.validator}{self.block_hash}{self.height}{self.round}{self.timestamp}".encode('utf-8')
        self.signature = hashlib.sha256(message + private_key).digest()
    
    def verify(self, public_key: bytes) -> bool:
        """Verify the vote signature"""
        if not self.signature:
            return False
            
        import hashlib
        message = f"{self.validator}{self.block_hash}{self.height}{self.round}{self.timestamp}".encode('utf-8')
        expected_sig = hashlib.sha256(message + public_key).digest()
        return self.signature == expected_sig

class ConsensusRound:
    """Represents a round of BFT consensus"""
    
    def __init__(self, height: int, round_num: int, validators: List[Validator]):
        self.height = height
        self.round = round_num
        self.validators = validators
        self.total_stake = sum(v.stake for v in validators if v.state == ValidatorState.ACTIVE)
        self.threshold = (self.total_stake * 2) // 3 + 1  # 2/3 threshold
        
        self.proposed_block = None
        self.votes: Dict[str, Vote] = {}  # validator_address -> vote
        self.voted_stake = 0
    
    def add_vote(self, vote: Vote) -> bool:
        """Add a validator's vote to this round"""
        if vote.height != self.height or vote.round != self.round:
            return False
            
        validator_addr = vote.validator.to_hex()
        
        # Ensure validator hasn't already voted
        if validator_addr in self.votes:
            return False
            
        # Find the validator
        validator = next((v for v in self.validators if v.address == vote.validator), None)
        if not validator or validator.state != ValidatorState.ACTIVE:
            return False
            
        # Add the vote
        self.votes[validator_addr] = vote
        self.voted_stake += validator.stake
        
        return True
    
    def has_consensus(self) -> bool:
        """Check if we have enough votes for consensus"""
        return self.voted_stake >= self.threshold

class BFTConsensus:
    """Byzantine Fault Tolerance consensus implementation"""
    
    def __init__(self, validators: List[Validator]):
        self.validators = validators
        self.active_validators = [v for v in validators if v.state == ValidatorState.ACTIVE]
        self.current_height = 1  # Start at height 1 to match block height
        self.current_round = 0
        self.rounds: Dict[Tuple[int, int], ConsensusRound] = {}  # (height, round) -> round_state
        self.finalized_blocks: Dict[int, Block] = {}  # height -> block
        
        # Initialize the first consensus round
        self.rounds[(self.current_height, self.current_round)] = ConsensusRound(
            self.current_height,
            self.current_round,
            self.validators
        )
    
    def get_current_proposer(self) -> Optional[Validator]:
        """Get the current block proposer based on height and round"""
        if not self.active_validators:
            return None
            
        # Simple round-robin selection based on height + round
        idx = (self.current_height + self.current_round) % len(self.active_validators)
        return self.active_validators[idx]
    
    def start_new_round(self) -> None:
        """Initialize a new consensus round"""
        self.current_round += 1
        round_key = (self.current_height, self.current_round)
        self.rounds[round_key] = ConsensusRound(
            self.current_height,
            self.current_round,
            self.validators
        )
    
    def propose_block(self, block: Block, proposer: Address, private_key: bytes) -> bool:
        """Validator proposes a block for the current height/round"""
        # Check if the proposer is the expected one
        current_proposer = self.get_current_proposer()
        if not current_proposer or current_proposer.address != proposer:
            return False
            
        round_key = (self.current_height, self.current_round)
        if round_key not in self.rounds:
            self.start_new_round()
            round_key = (self.current_height, self.current_round)
            
        # Set the proposed block and sign it
        current_round = self.rounds[round_key]
        
        # Ensure block height matches current consensus height
        if block.height != self.current_height:
            return False
            
        # Sign the block
        block.sign(private_key)
        current_round.proposed_block = block
        
        return True
    
    def vote_for_block(self, validator: Address, block_hash: Hash, private_key: bytes) -> bool:
        """Validator votes for a proposed block"""
        round_key = (self.current_height, self.current_round)
        if round_key not in self.rounds:
            return False
            
        current_round = self.rounds[round_key]
        
        # Create and sign vote
        vote = Vote(validator, block_hash, self.current_height, self.current_round)
        vote.sign(private_key)
        
        # Add the vote to current round
        if not current_round.add_vote(vote):
            return False
            
        # Check if we have consensus
        if current_round.has_consensus() and current_round.proposed_block:
            self._finalize_block(current_round.proposed_block)
            
        return True
    
    def _finalize_block(self, block: Block) -> None:
        """Finalize a block with consensus"""
        self.finalized_blocks[block.height] = block
        self.current_height += 1
        self.current_round = 0
        
        # Start a new round for the next height
        round_key = (self.current_height, self.current_round)
        self.rounds[round_key] = ConsensusRound(
            self.current_height,
            self.current_round,
            self.validators
        )