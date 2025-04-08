# Zensia Transactions Implementation

import time
import hashlib
import base64
from dataclasses import dataclass
from typing import Dict, Optional
from zensia_core_implementation import Hash, Address

@dataclass
class Transaction:
    """Base transaction structure"""
    tx_hash: Hash
    sender: Address
    recipient: Address
    amount: int  # in smallest unit
    nonce: int
    timestamp: int
    signature: Optional[bytes] = None
    
    @classmethod
    def create(cls, sender: Address, recipient: Address, amount: int, nonce: int) -> 'Transaction':
        """Create a new unsigned transaction"""
        timestamp = int(time.time())
        # Calculate transaction hash
        tx_data = f"{sender}{recipient}{amount}{nonce}{timestamp}".encode('utf-8')
        tx_hash = Hash.from_bytes(tx_data)
        
        return cls(
            tx_hash=tx_hash,
            sender=sender,
            recipient=recipient,
            amount=amount,
            nonce=nonce,
            timestamp=timestamp
        )
    
    def sign(self, private_key: bytes) -> None:
        """Sign the transaction with the sender's private key"""
        # In a real implementation, this would use proper digital signatures
        # For simplicity, we'll just simulate a signature
        message = f"{self.tx_hash}{self.sender}{self.recipient}{self.amount}{self.nonce}{self.timestamp}".encode('utf-8')
        self.signature = hashlib.sha256(message + private_key).digest()
    
    def verify_signature(self, public_key: bytes) -> bool:
        """Verify the transaction signature"""
        if not self.signature:
            return False
            
        message = f"{self.tx_hash}{self.sender}{self.recipient}{self.amount}{self.nonce}{self.timestamp}".encode('utf-8')
        expected_sig = hashlib.sha256(message + public_key).digest()
        return self.signature == expected_sig
    
    def to_json(self) -> Dict:
        """Convert transaction to JSON-serializable dictionary"""
        return {
            "tx_hash": self.tx_hash.to_hex(),
            "sender": self.sender.to_hex(),
            "recipient": self.recipient.to_hex(),
            "amount": self.amount,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "signature": base64.b64encode(self.signature).decode('utf-8') if self.signature else None
        }