# Zensia Blockchain Implementation

import time
import hashlib
import base64
from dataclasses import dataclass
from typing import Dict, List, Union, Optional, Set
from zensia_core_implementation import Hash, Address
from zensia_transactions import Transaction
from zensia_privacy import ConfidentialTransaction

@dataclass
class Block:
    """A block in the Zensia blockchain"""
    height: int
    previous_hash: Hash
    merkle_root: Hash
    timestamp: int
    validator: Address
    transactions: List[Union[Transaction, ConfidentialTransaction]]
    signature: Optional[bytes] = None
    
    @property
    def block_hash(self) -> Hash:
        """Calculate the hash of this block"""
        block_data = f"{self.height}{self.previous_hash}{self.merkle_root}{self.timestamp}{self.validator}".encode('utf-8')
        return Hash.from_bytes(block_data)
    
    @classmethod
    def create(cls, height: int, previous_hash: Hash, 
               transactions: List[Union[Transaction, ConfidentialTransaction]], 
               validator: Address) -> 'Block':
        """Create a new unsigned block"""
        # Calculate merkle root from transactions
        # Simplified for demonstration
        tx_hashes = []
        for tx in transactions:
            if isinstance(tx, Transaction):
                tx_hashes.append(tx.tx_hash)
            else:  # ConfidentialTransaction
                # Use first commitment as a proxy for transaction hash
                tx_hashes.append(Hash.from_bytes(tx.commitments[0] if tx.commitments else b''))
        
        # Simple merkle root calculation (not a proper Merkle tree)
        merkle_data = b''.join(tx_hashes)
        merkle_root = Hash.from_bytes(merkle_data)
        
        timestamp = int(time.time())
        
        return cls(
            height=height,
            previous_hash=previous_hash,
            merkle_root=merkle_root,
            timestamp=timestamp,
            validator=validator,
            transactions=transactions
        )
    
    def sign(self, validator_private_key: bytes) -> None:
        """Sign the block with the validator's private key"""
        # In a real implementation, this would use proper digital signatures
        block_hash = self.block_hash
        message = f"{block_hash}{self.validator}".encode('utf-8')
        self.signature = hashlib.sha256(message + validator_private_key).digest()
    
    def verify_signature(self, validator_public_key: bytes) -> bool:
        """Verify the block signature"""
        if not self.signature:
            return False
            
        block_hash = self.block_hash
        message = f"{block_hash}{self.validator}".encode('utf-8')
        expected_sig = hashlib.sha256(message + validator_public_key).digest()
        return self.signature == expected_sig
    
    def to_json(self) -> Dict:
        """Convert block to JSON-serializable dictionary"""
        return {
            "height": self.height,
            "previous_hash": self.previous_hash.to_hex(),
            "merkle_root": self.merkle_root.to_hex(),
            "timestamp": self.timestamp,
            "validator": self.validator.to_hex(),
            "transactions": [
                tx.to_json() if isinstance(tx, Transaction) 
                else {"type": "confidential", "nullifiers": [n.hex() for n in tx.nullifiers],
                      "commitments": [c.hex() for c in tx.commitments]}
                for tx in self.transactions
            ],
            "signature": base64.b64encode(self.signature).decode('utf-8') if self.signature else None
        }

class AccountState:
    """Represents the state of an account"""
    
    def __init__(self, address: Address, balance: int = 0, nonce: int = 0):
        self.address = address
        self.balance = balance
        self.nonce = nonce
    
    def apply_transaction(self, tx: Transaction) -> None:
        """Apply a transaction to this account"""
        if tx.sender == self.address:
            self.balance -= tx.amount
            self.nonce += 1
        
        if tx.recipient == self.address:
            self.balance += tx.amount

class BlockchainState:
    """Manages the overall state of the blockchain"""
    
    def __init__(self):
        self.accounts: Dict[str, AccountState] = {}  # address -> state
        self.height: int = 0
        self.last_block_hash: Optional[Hash] = None
        
        # For confidential transactions
        self.nullifier_set: Set[bytes] = set()  # Set of spent nullifiers
        self.commitment_set: Set[bytes] = set()  # Set of existing commitments
    
    def get_account(self, address: Address) -> AccountState:
        """Get account state for an address, create if not exists"""
        addr_str = address.to_hex()
        if addr_str not in self.accounts:
            self.accounts[addr_str] = AccountState(address)
        return self.accounts[addr_str]
    
    def validate_transaction(self, tx: Union[Transaction, ConfidentialTransaction]) -> bool:
        """Validate if a transaction is valid according to current state"""
        if isinstance(tx, Transaction):
            # Regular transaction validation
            sender = self.get_account(tx.sender)
            
            # Check balance and nonce
            if sender.balance < tx.amount:
                return False  # Insufficient funds
                
            if sender.nonce != tx.nonce:
                return False  # Invalid nonce
                
            return True
        else:
            # Confidential transaction validation
            
            # Check for double spends
            for nullifier in tx.nullifiers:
                if nullifier in self.nullifier_set:
                    return False  # Nullifier already spent
            
            # Verify zk proof
            return tx.verify()
    
    def apply_transaction(self, tx: Union[Transaction, ConfidentialTransaction]) -> None:
        """Apply a transaction to the state"""
        if isinstance(tx, Transaction):
            # Regular transaction
            sender = self.get_account(tx.sender)
            recipient = self.get_account(tx.recipient)
            
            sender.apply_transaction(tx)
            recipient.apply_transaction(tx)
        else:
            # Confidential transaction
            # Mark nullifiers as spent
            for nullifier in tx.nullifiers:
                self.nullifier_set.add(nullifier)
            
            # Add new commitments
            for commitment in tx.commitments:
                self.commitment_set.add(commitment)
    
    def apply_block(self, block: Block) -> None:
        """Apply a block to the state"""
        # Validate block height and previous hash
        if block.height != self.height + 1:
            raise ValueError(f"Invalid block height: expected {self.height + 1}, got {block.height}")
        
        if self.last_block_hash and block.previous_hash != self.last_block_hash:
            raise ValueError("Block's previous hash doesn't match current last hash")
        
        # Apply all transactions
        for tx in block.transactions:
            if not self.validate_transaction(tx):
                raise ValueError(f"Block contains invalid transaction")
            self.apply_transaction(tx)
        
        # Update blockchain state
        self.height = block.height
        self.last_block_hash = block.block_hash