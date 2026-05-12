"""
Merkle Tree implementation for efficient transaction verification
Provides O(log n) proof complexity for transaction existence
"""

import hashlib
from typing import List, Optional, Tuple
from .models import Transaction, MerkleProof


class MerkleTree:
    """Merkle Tree for transaction verification"""
    
    def __init__(self, transactions: List[Transaction]):
        """Initialize Merkle tree with transactions"""
        self.transactions = transactions
        self.tree = []
        self.root = None
        self._build_tree()
    
    @staticmethod
    def hash_pair(hash1: str, hash2: str) -> str:
        """Hash two hashes together"""
        combined = (hash1 + hash2).encode()
        return hashlib.sha256(combined).hexdigest()
    
    def _build_tree(self):
        """Build Merkle tree from transactions"""
        if not self.transactions:
            self.root = hashlib.sha256(b"").hexdigest()
            return
        
        # Level 0: Transaction hashes (leaf level)
        current_level = [tx.tx_hash for tx in self.transactions]
        self.tree.append(current_level.copy())
        
        # If odd number of hashes, duplicate the last one
        if len(current_level) % 2 != 0:
            current_level.append(current_level[-1])
        
        # Build tree upwards
        while len(current_level) > 1:
            # If odd number of hashes at this level, duplicate the last one
            if len(current_level) % 2 != 0:
                current_level.append(current_level[-1])

            next_level = []
            for i in range(0, len(current_level), 2):
                combined_hash = self.hash_pair(current_level[i], current_level[i + 1])
                next_level.append(combined_hash)

            self.tree.append(next_level.copy())
            current_level = next_level
        
        self.root = current_level[0] if current_level else ""
    
    def get_proof(self, tx_hash: str) -> Optional[MerkleProof]:
        """Generate Merkle proof for a transaction"""
        if not self.transactions:
            return None
        
        # Find transaction index
        leaf_index = -1
        for i, tx in enumerate(self.transactions):
            if tx.tx_hash == tx_hash:
                leaf_index = i
                break
        
        if leaf_index == -1:
            return None
        
        # Build proof path
        proof_path = []
        current_index = leaf_index
        
        for level in self.tree:
            if len(level) <= 1:
                break
            
            # Determine if current is left or right
            is_left = current_index % 2 == 0
            
            # Get sibling
            sibling_index = current_index + 1 if is_left else current_index - 1
            
            if sibling_index < len(level):
                sibling_hash = level[sibling_index]
                direction = 'right' if is_left else 'left'
                proof_path.append((sibling_hash, direction))
            
            # Move to parent
            current_index = current_index // 2
        
        return MerkleProof(tx_hash, proof_path, leaf_index)
    
    def verify_proof(self, tx_hash: str, proof: MerkleProof) -> bool:
        """Verify a Merkle proof"""
        if proof.tx_hash != tx_hash:
            return False
        
        current_hash = tx_hash
        
        for sibling_hash, direction in proof.proof_path:
            if direction == 'right':
                current_hash = self.hash_pair(current_hash, sibling_hash)
            else:
                current_hash = self.hash_pair(sibling_hash, current_hash)
        
        return current_hash == self.root
    
    def to_dict(self) -> dict:
        """Convert tree structure to dictionary for visualization"""
        return {
            'root': self.root,
            'levels': self.tree,
            'leaf_count': len(self.transactions)
        }
    
    @staticmethod
    def visualize_tree(transactions: List[Transaction]) -> str:
        """Generate Graphviz DOT notation for tree visualization"""
        tree = MerkleTree(transactions)
        
        dot_lines = ["digraph MerkleTree {"]
        dot_lines.append('    node [shape=box];')
        dot_lines.append('    rankdir=BT;')
        
        node_counter = [0]
        level_nodes = [[]]
        
        # Add leaf nodes (transactions)
        for i, tx in enumerate(transactions):
            node_id = f"leaf_{i}"
            label = f"Tx {i}\n{tx.tx_hash[:8]}..."
            dot_lines.append(f'    {node_id} [label="{label}", fillcolor=lightblue, style=filled];')
            level_nodes[0].append(node_id)
        
        # Add parent nodes
        node_counter = len(transactions)
        hash_levels = tree.tree[1:] if len(tree.tree) > 1 else []
        
        for level_idx, level_hashes in enumerate(hash_levels):
            level_nodes.append([])
            for hash_idx, h in enumerate(level_hashes):
                node_id = f"node_{level_idx}_{hash_idx}"
                label = f"{h[:8]}..."
                dot_lines.append(f'    {node_id} [label="{label}", fillcolor=lightyellow, style=filled];')
                level_nodes[level_idx + 1].append(node_id)
        
        # Add edges
        for level_idx in range(len(level_nodes) - 1):
            current_level = level_nodes[level_idx]
            parent_level = level_nodes[level_idx + 1]
            
            for parent_idx, parent_node in enumerate(parent_level):
                child1_idx = parent_idx * 2
                child2_idx = parent_idx * 2 + 1
                
                if child1_idx < len(current_level):
                    dot_lines.append(f'    {current_level[child1_idx]} -> {parent_node};')
                if child2_idx < len(current_level):
                    dot_lines.append(f'    {current_level[child2_idx]} -> {parent_node};')
        
        # Highlight root
        if level_nodes and level_nodes[-1]:
            root_node = level_nodes[-1][0]
            dot_lines.append(f'    {root_node} [fillcolor=lightgreen, style=filled];')
        
        dot_lines.append('}')
        
        return '\n'.join(dot_lines)
