"""
Blockchain engine - Core logic for block mining and chain validation
Implements proof-of-work and hash-chain validation
"""

import hashlib
import json
from datetime import datetime
from typing import List, Optional, Tuple
from .models import Block, Transaction, Grade, BlockchainState
from .merkle import MerkleTree
from .db import GradeLedgerDB


class BlockchainEngine:
    """Main blockchain engine for mining and verification"""
    
    def __init__(self, db: GradeLedgerDB, difficulty: int = 2):
        """
        Initialize blockchain engine
        difficulty: number of leading zeros required in block hash
        """
        self.db = db
        self.difficulty = difficulty
        self.difficulty_target = '0' * difficulty
    
    def mine_block(self) -> Optional[Block]:
        """
        Mine a new block from pending transactions
        Returns Block if successful, None if no pending transactions
        """
        # Get pending transactions
        pending = self.db.get_mempool()
        
        if not pending:
            return None
        
        # Take up to 10 transactions
        transactions_to_mine = pending[:10]
        
        # Create Merkle tree
        merkle_tree = MerkleTree(transactions_to_mine)
        merkle_root = merkle_tree.root
        
        # Get previous block
        latest_block = self.db.get_latest_block()
        prev_hash = latest_block.block_hash if latest_block else "0" * 64
        
        # Get next block ID
        total_blocks = self.db.get_total_blocks()
        block_id = total_blocks + 1
        
        # Mine block (find nonce)
        nonce = 0
        timestamp = datetime.now().isoformat()
        
        while True:
            block_data = {
                'block_id': block_id,
                'prev_hash': prev_hash,
                'merkle_root': merkle_root,
                'timestamp': timestamp,
                'nonce': nonce
            }
            
            block_json = json.dumps(block_data, sort_keys=True)
            block_hash = hashlib.sha256(block_json.encode()).hexdigest()
            
            if block_hash.startswith(self.difficulty_target):
                break
            
            nonce += 1
        
        # Create block object
        block = Block(
            block_id=block_id,
            prev_hash=prev_hash,
            merkle_root=merkle_root,
            block_hash=block_hash,
            timestamp=timestamp,
            nonce=nonce,
            transactions=transactions_to_mine
        )
        
        # Insert into database
        success = self.db.insert_block(block)
        
        return block if success else None
    
    def verify_chain(self) -> Tuple[bool, List[str]]:
        """
        Verify entire blockchain
        Returns: (is_valid, list of issues found)
        """
        issues = []
        blocks = self.db.get_blocks()
        
        if not blocks:
            return True, []
        
        # Check genesis block
        genesis = blocks[0]
        if genesis.block_id != 1:
            issues.append(f"Genesis block has wrong ID: {genesis.block_id}")
        
        if genesis.prev_hash != "0" * 64:
            issues.append(f"Genesis block has non-zero prev_hash: {genesis.prev_hash}")
        
        # Verify genesis block hash
        if not self._verify_block_hash(genesis):
            issues.append(f"Genesis block hash is invalid")
        
        # Check subsequent blocks
        for i in range(1, len(blocks)):
            prev_block = blocks[i - 1]
            current_block = blocks[i]
            
            # Check block linkage
            if current_block.prev_hash != prev_block.block_hash:
                issues.append(
                    f"Block {current_block.block_id} prev_hash mismatch. "
                    f"Expected {prev_block.block_hash}, got {current_block.prev_hash}"
                )
            
            # Verify block hash
            if not self._verify_block_hash(current_block):
                issues.append(f"Block {current_block.block_id} hash is invalid")
            
            # Verify Merkle root
            if not self._verify_merkle_root(current_block):
                issues.append(f"Block {current_block.block_id} Merkle root is invalid")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def _verify_block_hash(self, block: Block) -> bool:
        """Verify a single block's hash"""
        block_data = {
            'block_id': block.block_id,
            'prev_hash': block.prev_hash,
            'merkle_root': block.merkle_root,
            'timestamp': block.timestamp,
            'nonce': block.nonce
        }
        
        block_json = json.dumps(block_data, sort_keys=True)
        calculated_hash = hashlib.sha256(block_json.encode()).hexdigest()
        
        return calculated_hash == block.block_hash
    
    def _verify_merkle_root(self, block: Block) -> bool:
        """Verify Merkle root of a block"""
        if not block.transactions:
            return block.merkle_root == hashlib.sha256(b"").hexdigest()
        
        merkle_tree = MerkleTree(block.transactions)
        return merkle_tree.root == block.merkle_root
    
    def get_blockchain_state(self) -> BlockchainState:
        """Get current blockchain state"""
        total_blocks = self.db.get_total_blocks()
        total_transactions = self.db.get_total_transactions()
        pending_transactions = self.db.get_mempool_count()
        is_valid, _ = self.verify_chain()
        
        latest_block = self.db.get_latest_block()
        latest_block_hash = latest_block.block_hash if latest_block else "0" * 64
        
        return BlockchainState(
            total_blocks=total_blocks,
            total_transactions=total_transactions,
            pending_transactions=pending_transactions,
            is_valid=is_valid,
            latest_block_hash=latest_block_hash
        )
    
    def add_grade(self, grade: Grade) -> Tuple[bool, str]:
        """
        Add a grade to the system
        Returns: (success, message/hash)
        """
        success, result = self.db.add_to_mempool(grade)
        
        if success:
            # Check if we should auto-mine
            pending_count = self.db.get_mempool_count()
            if pending_count >= 10:
                block = self.mine_block()
                if block:
                    return True, f"Grade added. Auto-mined block {block.block_id} with 10 transactions"
                else:
                    return True, f"Grade added (Tx: {result[:16]}...)"
            else:
                return True, f"Grade added to mempool ({pending_count}/10 pending)"
        else:
            return False, result
    
    def get_merkle_proof_for_grade(self, student_id: str, course_code: str, valid_time: str) -> Optional[dict]:
        """
        Get Merkle proof for a specific grade
        Returns dict with proof and verification info, or None if not found
        """
        tx = self.db.get_transaction_by_student_course(student_id, course_code, valid_time)
        
        if not tx:
            return None
        
        # Get the block containing this transaction
        block = self.db.get_block_by_id(tx.block_id)
        
        if not block:
            return None
        
        # Generate Merkle proof
        merkle_tree = MerkleTree(block.transactions)
        proof = merkle_tree.get_proof(tx.tx_hash)
        
        if not proof:
            return None
        
        # Verify the proof
        is_valid = merkle_tree.verify_proof(tx.tx_hash, proof)
        
        return {
            'transaction': tx.to_dict(),
            'block_id': block.block_id,
            'merkle_root': block.merkle_root,
            'proof': proof.to_dict(),
            'is_valid': is_valid,
            'block_hash': block.block_hash
        }
    
    def export_chain_json(self) -> dict:
        """Export entire chain as JSON"""
        blocks = self.db.get_blocks()
        
        chain_data = {
            'total_blocks': len(blocks),
            'total_transactions': self.db.get_total_transactions(),
            'pending_transactions': self.db.get_mempool_count(),
            'blocks': [block.to_dict() for block in blocks]
        }
        
        return chain_data
