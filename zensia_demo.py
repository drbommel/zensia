# Zensia Demonstration Script

import secrets
import hashlib
import json
from typing import Dict, Any

# Import Zensia components
from zensia_core_implementation import Hash, Address
from zensia_privacy import StealthAddress, ConfidentialTransaction
from zensia_transactions import Transaction
from zensia_blockchain import Block, BlockchainState
from zensia_consensus import ValidatorState, Validator, BFTConsensus

def demo_zensia_blockchain() -> Dict[str, Any]:
    """Demonstrate the basic functionality of Zensia blockchain"""
    
    # Create some test addresses and keys
    print("Generating addresses and keys...")
    alice_private_key = secrets.token_bytes(32)
    alice_public_key = hashlib.sha256(alice_private_key).digest()
    alice_address = Address.from_public_key(alice_public_key)
    
    bob_private_key = secrets.token_bytes(32)
    bob_public_key = hashlib.sha256(bob_private_key).digest()
    bob_address = Address.from_public_key(bob_public_key)
    
    # Create validators
    print("Setting up validators...")
    validators = [
        Validator(alice_address, alice_public_key, stake=1000),
        Validator(bob_address, bob_public_key, stake=500)
    ]
    
    # Set validators as active
    for v in validators:
        v.state = ValidatorState.ACTIVE
    
    # Initialize blockchain state
    print("Initializing blockchain state...")
    state = BlockchainState()
    
    # Add initial funds to Alice's account
    alice_account = state.get_account(alice_address)
    alice_account.balance = 10000
    
    # Create consensus mechanism
    print("Creating consensus mechanism...")
    consensus = BFTConsensus(validators)
    
    # Create a normal transaction
    print("\nCreating a regular transaction...")
    tx = Transaction.create(alice_address, bob_address, 100, nonce=0)
    tx.sign(alice_private_key)
    print(f"Transaction created: {tx.tx_hash.to_hex()}")
    print(f"From: {tx.sender.to_hex()} To: {tx.recipient.to_hex()} Amount: {tx.amount}")
    
    # Create a confidential transaction
    print("\nCreating a confidential transaction...")
    # Generate stealth address for Bob
    bob_stealth, (bob_scan_priv, bob_spend_priv) = StealthAddress.generate()
    
    # Create a note as input (simulating existing commitment)
    input_note = secrets.token_bytes(32)
    input_value = 50
    input_blinding = secrets.token_bytes(32)
    
    # Create a confidential transaction
    conf_tx = ConfidentialTransaction()
    conf_tx.create(
        inputs=[(input_note, input_value, input_blinding)],
        outputs=[(bob_address, input_value)], 
        sender_private_key=alice_private_key
    )
    print(f"Confidential transaction created with {len(conf_tx.nullifiers)} inputs and {len(conf_tx.commitments)} outputs")
    
    # Create a block
    print("\nCreating a block...")
    block = Block.create(
        height=1,
        previous_hash=Hash.from_bytes(b'genesis'),
        transactions=[tx, conf_tx],
        validator=alice_address
    )
    
    # Propose and validate the block
    print("Proposing block to consensus...")
    consensus.propose_block(block, alice_address, alice_private_key)
    
    # Vote for the block
    print("Validators voting on block...")
    consensus.vote_for_block(alice_address, block.block_hash, alice_private_key)
    consensus.vote_for_block(bob_address, block.block_hash, bob_private_key)
    
    # Apply block to state
    print("Applying block to blockchain state...")
    try:
        state.apply_block(block)
        print(f"Block applied successfully! New height: {state.height}")
        
        # Check balances
        alice_balance = state.get_account(alice_address).balance
        bob_balance = state.get_account(bob_address).balance
        print(f"Alice's balance: {alice_balance}")
        print(f"Bob's balance: {bob_balance}")
        
    except ValueError as e:
        print(f"Error applying block: {e}")
    
    return {
        "block": block,
        "regular_tx": tx,
        "confidential_tx": conf_tx,
        "state": state,
        "consensus": consensus
    }

def create_multi_block_chain():
    """Create a blockchain with multiple blocks for demonstration"""
    # Create some test addresses and keys
    print("\n=== Creating Multi-Block Chain ===\n")
    alice_private_key = secrets.token_bytes(32)
    alice_public_key = hashlib.sha256(alice_private_key).digest()
    alice_address = Address.from_public_key(alice_public_key)
    
    bob_private_key = secrets.token_bytes(32)
    bob_public_key = hashlib.sha256(bob_private_key).digest()
    bob_address = Address.from_public_key(bob_public_key)
    
    charlie_private_key = secrets.token_bytes(32)
    charlie_public_key = hashlib.sha256(charlie_private_key).digest()
    charlie_address = Address.from_public_key(charlie_public_key)
    
    # Create validators
    validators = [
        Validator(alice_address, alice_public_key, stake=1000),
        Validator(bob_address, bob_public_key, stake=800),
        Validator(charlie_address, charlie_public_key, stake=500)
    ]
    
    # Set validators as active
    for v in validators:
        v.state = ValidatorState.ACTIVE
    
    # Initialize blockchain state
    state = BlockchainState()
    
    # Add initial funds
    alice_account = state.get_account(alice_address)
    alice_account.balance = 10000
    bob_account = state.get_account(bob_address)
    bob_account.balance = 5000
    
    # Create consensus mechanism
    consensus = BFTConsensus(validators)
    
    # Initialize the previous hash
    previous_hash = Hash.from_bytes(b'genesis')
    
    # Create and apply 3 blocks
    for block_height in range(1, 4):
        print(f"\nCreating block {block_height}...")
        
        # Create transactions for this block
        transactions = []
        
        # Regular transaction: Alice -> Bob
        if block_height == 1:
            tx = Transaction.create(alice_address, bob_address, 200, nonce=0)
            tx.sign(alice_private_key)
            transactions.append(tx)
            print(f"Added transaction: Alice -> Bob (200 coins)")
        
        # Regular transaction: Bob -> Charlie
        elif block_height == 2:
            tx = Transaction.create(bob_address, charlie_address, 50, nonce=0)
            tx.sign(bob_private_key)
            transactions.append(tx)
            print(f"Added transaction: Bob -> Charlie (50 coins)")
            
        # Regular transaction: Alice -> Charlie and Confidential transaction
        elif block_height == 3:
            tx1 = Transaction.create(alice_address, charlie_address, 300, nonce=1)
            tx1.sign(alice_private_key)
            transactions.append(tx1)
            print(f"Added transaction: Alice -> Charlie (300 coins)")
            
            # Add a confidential transaction
            input_note = secrets.token_bytes(32)
            input_value = 100
            input_blinding = secrets.token_bytes(32)
            
            conf_tx = ConfidentialTransaction()
            conf_tx.create(
                inputs=[(input_note, input_value, input_blinding)],
                outputs=[(bob_address, input_value)],
                sender_private_key=alice_private_key
            )
            transactions.append(conf_tx)
            print(f"Added confidential transaction with {len(conf_tx.nullifiers)} inputs and {len(conf_tx.commitments)} outputs")
        
        # Determine the current proposer based on block height
        proposer_idx = (block_height - 1) % len(validators)
        proposer = validators[proposer_idx]
        proposer_address = proposer.address
        
        if proposer_address == alice_address:
            proposer_private_key = alice_private_key
            print(f"Block proposer: Alice")
        elif proposer_address == bob_address:
            proposer_private_key = bob_private_key
            print(f"Block proposer: Bob")
        else:
            proposer_private_key = charlie_private_key
            print(f"Block proposer: Charlie")
        
        # Create the block
        block = Block.create(
            height=block_height,
            previous_hash=previous_hash,
            transactions=transactions,
            validator=proposer_address
        )
        
        # Propose the block to consensus
        consensus.propose_block(block, proposer_address, proposer_private_key)
        
        # All validators vote for the block
        consensus.vote_for_block(alice_address, block.block_hash, alice_private_key)
        consensus.vote_for_block(bob_address, block.block_hash, bob_private_key)
        consensus.vote_for_block(charlie_address, block.block_hash, charlie_private_key)
        
        # Apply block to state
        try:
            state.apply_block(block)
            print(f"Block {block_height} applied successfully!")
            previous_hash = block.block_hash
        except ValueError as e:
            print(f"Error applying block {block_height}: {e}")
            break
    
    # Show final state
    print("\nFinal blockchain state:")
    print(f"Blockchain height: {state.height}")
    print(f"Alice's balance: {state.get_account(alice_address).balance}")
    print(f"Bob's balance: {state.get_account(bob_address).balance}")
    print(f"Charlie's balance: {state.get_account(charlie_address).balance}")
    
    return {
        "state": state,
        "consensus": consensus,
        "last_block_hash": previous_hash
    }

if __name__ == "__main__":
    print("=== Zensia Blockchain Demo ===")
    
    # Run simple demo
    demo_result = demo_zensia_blockchain()
    
    # Run multi-block chain demo
    multi_block_result = create_multi_block_chain()
    
    print("\nDemo completed successfully!")