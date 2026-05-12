"""
Data models for Student Grade Ledger
Defines Grade, Transaction, and Block structures
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import hashlib
import json


@dataclass
class Grade:
    """Individual grade entry"""
    student_id: str
    student_name: str
    course_code: str
    grade: str
    valid_time: str  # Semester (e.g., "Spring 2024")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'student_id': self.student_id,
            'student_name': self.student_name,
            'course_code': self.course_code,
            'grade': self.grade,
            'valid_time': self.valid_time
        }


@dataclass
class Transaction:
    """Transaction in the blockchain"""
    tx_id: str
    student_id: str
    student_name: str
    course_code: str
    grade: str
    valid_time: str
    transaction_time: str
    tx_hash: str
    block_id: Optional[int] = None
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'tx_id': self.tx_id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'course_code': self.course_code,
            'grade': self.grade,
            'valid_time': self.valid_time,
            'transaction_time': self.transaction_time,
            'tx_hash': self.tx_hash,
            'block_id': self.block_id
        }
    
    @staticmethod
    def create_hash(grade: Grade) -> str:
        """Create SHA256 hash for a grade transaction"""
        grade_str = json.dumps(grade.to_dict(), sort_keys=True)
        return hashlib.sha256(grade_str.encode()).hexdigest()


@dataclass
class Block:
    """Block in the blockchain"""
    block_id: int
    prev_hash: str
    merkle_root: str
    block_hash: str
    timestamp: str
    nonce: int
    transactions: List[Transaction] = field(default_factory=list)
    
    def to_dict(self):
        """Convert to dictionary (excluding transactions list for DB storage)"""
        return {
            'block_id': self.block_id,
            'prev_hash': self.prev_hash,
            'merkle_root': self.merkle_root,
            'block_hash': self.block_hash,
            'timestamp': self.timestamp,
            'nonce': self.nonce,
            'num_transactions': len(self.transactions)
        }


@dataclass
class BlockchainState:
    """Current state of blockchain"""
    total_blocks: int
    total_transactions: int
    pending_transactions: int
    is_valid: bool
    latest_block_hash: str
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'total_blocks': self.total_blocks,
            'total_transactions': self.total_transactions,
            'pending_transactions': self.pending_transactions,
            'is_valid': self.is_valid,
            'latest_block_hash': self.latest_block_hash
        }


class MerkleProof:
    """Merkle tree proof for transaction verification"""
    
    def __init__(self, tx_hash: str, proof_path: List[tuple], leaf_index: int):
        """
        proof_path: List of (hash, direction) tuples
        direction: 'left' or 'right' indicating which side the hash is
        """
        self.tx_hash = tx_hash
        self.proof_path = proof_path
        self.leaf_index = leaf_index
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'tx_hash': self.tx_hash,
            'proof_path': [(h, d) for h, d in self.proof_path],
            'leaf_index': self.leaf_index
        }
