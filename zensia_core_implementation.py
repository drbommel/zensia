# Zensia Core Implementation
# Basic implementation of Zensia's core functionality

import os
from typing import Dict, List, Optional, Union, Tuple, Set
import hashlib
import time
from dataclasses import dataclass
import json
import secrets
import base64
from enum import Enum

# Define basic types and utilities for Zensia
class Hash(bytes):
    """A 32-byte hash value"""
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'Hash':
        """Create a hash from raw data using SHA-256"""
        return cls(hashlib.sha256(data).digest())
        
    @classmethod
    def from_strings(cls, *args: str) -> 'Hash':
        """Create a hash from string arguments"""
        return cls.from_bytes(''.join(args).encode('utf-8'))
    
    def to_hex(self) -> str:
        """Convert hash to hexadecimal representation"""
        return self.hex()
    
    def __str__(self) -> str:
        return self.to_hex()

class Address(bytes):
    """An address in the Zensia network"""
    
    @classmethod
    def from_public_key(cls, public_key: bytes) -> 'Address':
        """Derive an address from a public key"""
        return cls(hashlib.sha256(public_key).digest()[:20])  # 20 bytes address
    
    @classmethod
    def from_string(cls, addr_str: str) -> 'Address':
        """Create an address from a hex string"""
        return cls.fromhex(addr_str)
    
    def to_hex(self) -> str:
        """Convert address to hexadecimal representation"""
        return self.hex()
    
    def __str__(self) -> str:
        return self.to_hex()