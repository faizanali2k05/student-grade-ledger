"""
Consensus simulation - Multi-node blockchain synchronization
Implements longest-chain-wins consensus rule
"""

import shutil
import os
from typing import List, Tuple
from .db import GradeLedgerDB
from .blockchain import BlockchainEngine
from .models import Block


class BlockchainNode:
    """Represents a single node in the distributed blockchain network"""
    
    def __init__(self, node_id: int, db_path: str = None):
        """
        Initialize a blockchain node
        node_id: 1, 2, or 3
        db_path: path to node's database (default: nodes/nodeX.db)
        """
        self.node_id = node_id
        
        if db_path is None:
            os.makedirs("nodes", exist_ok=True)
            db_path = f"nodes/node{node_id}.db"
        
        self.db_path = db_path
        self.db = GradeLedgerDB(db_path)
        self.engine = BlockchainEngine(self.db)
    
    def get_chain_length(self) -> int:
        """Get number of blocks in this node's chain"""
        return self.db.get_total_blocks()
    
    def get_chain_hash(self) -> str:
        """Get hash of latest block for comparison"""
        latest = self.db.get_latest_block()
        return latest.block_hash if latest else "0" * 64
    
    def export_chain(self) -> List[Block]:
        """Export entire chain"""
        return self.db.get_blocks()
    
    def sync_with_node(self, other_node: 'BlockchainNode') -> Tuple[bool, str]:
        """
        Synchronize with another node using longest-chain-wins rule
        If other node has longer valid chain, adopt it
        Returns: (was_updated, message)
        """
        my_length = self.get_chain_length()
        other_length = other_node.get_chain_length()
        
        if other_length > my_length:
            # Verify other chain is valid
            is_valid, issues = other_node.engine.verify_chain()
            
            if is_valid:
                # Copy other node's database to this node
                shutil.copy(other_node.db_path, self.db_path)
                
                # Reload database connection
                self.db = GradeLedgerDB(self.db_path)
                self.engine = BlockchainEngine(self.db)
                
                return True, f"Adopted chain from Node {other_node.node_id} ({other_length} blocks)"
            else:
                return False, f"Node {other_node.node_id} chain invalid: {issues[0] if issues else 'Unknown error'}"
        
        elif my_length > other_length:
            return False, f"Node {self.node_id} already has longer chain ({my_length} blocks)"
        
        else:
            return False, f"Chains equal length ({my_length} blocks)"
    
    def get_state_info(self) -> dict:
        """Get node state information"""
        state = self.engine.get_blockchain_state()
        return {
            'node_id': self.node_id,
            'total_blocks': state.total_blocks,
            'total_transactions': state.total_transactions,
            'pending_transactions': state.pending_transactions,
            'is_valid': state.is_valid,
            'latest_block_hash': state.latest_block_hash
        }


class ConsensusSimulator:
    """Simulates consensus mechanism across multiple nodes"""
    
    def __init__(self):
        """Initialize consensus simulator with 3 nodes"""
        self.nodes: List[BlockchainNode] = []
        self._init_nodes()
    
    def _init_nodes(self):
        """Initialize 3 blockchain nodes"""
        for i in range(1, 4):
            node = BlockchainNode(i)
            self.nodes.append(node)
    
    def reset_nodes(self):
        """Reset all nodes to empty state"""
        for node in self.nodes:
            # Delete database files
            if os.path.exists(node.db_path):
                os.remove(node.db_path)
            # Reinitialize
            node.db = GradeLedgerDB(node.db_path)
            node.engine = BlockchainEngine(node.db)
    
    def get_node(self, node_id: int) -> BlockchainNode:
        """Get a specific node (1-3)"""
        return self.nodes[node_id - 1]
    
    def broadcast_block(self, from_node_id: int) -> List[Tuple[int, bool, str]]:
        """
        Broadcast blocks from one node to all others
        Returns list of (node_id, success, message)
        """
        source_node = self.get_node(from_node_id)
        results = []
        
        for node in self.nodes:
            if node.node_id != from_node_id:
                was_updated, message = node.sync_with_node(source_node)
                results.append((node.node_id, was_updated, message))
        
        return results
    
    def synchronize_all_nodes(self) -> List[dict]:
        """
        Run consensus protocol - all nodes sync to longest chain
        Returns: list of synchronization events
        """
        events = []
        
        # Get chain lengths
        chain_info = [
            {
                'node_id': node.node_id,
                'length': node.get_chain_length(),
                'hash': node.get_chain_hash()
            }
            for node in self.nodes
        ]
        
        events.append({
            'step': 'initial_state',
            'chain_lengths': chain_info
        })
        
        # Find longest chain
        max_length = max(info['length'] for info in chain_info)
        longest_node_id = next(
            info['node_id'] for info in chain_info 
            if info['length'] == max_length
        )
        
        # All other nodes sync to longest
        synced_count = 0
        for node in self.nodes:
            if node.node_id != longest_node_id:
                was_updated, message = node.sync_with_node(
                    self.get_node(longest_node_id)
                )
                
                if was_updated:
                    synced_count += 1
                
                events.append({
                    'step': f'sync_node_{node.node_id}',
                    'from_node': longest_node_id,
                    'to_node': node.node_id,
                    'updated': was_updated,
                    'message': message
                })
        
        # Final state
        final_chain_info = [
            {
                'node_id': node.node_id,
                'length': node.get_chain_length(),
                'hash': node.get_chain_hash(),
                'is_valid': node.engine.verify_chain()[0]
            }
            for node in self.nodes
        ]
        
        events.append({
            'step': 'final_state',
            'chain_lengths': final_chain_info,
            'nodes_synchronized': synced_count == 2,
            'all_valid': all(info['is_valid'] for info in final_chain_info)
        })
        
        return events
    
    def get_all_nodes_state(self) -> List[dict]:
        """Get state of all nodes"""
        return [node.get_state_info() for node in self.nodes]
    
    def demonstrate_attack(self) -> dict:
        """
        Demonstrate that forked chains are detected
        - Create different chains on nodes
        - Show they don't synchronize if one is invalid
        """
        # This is a simulation showing tamper detection
        result = {
            'scenario': 'Node tamper attempt',
            'steps': [],
            'conclusion': ''
        }
        
        node1 = self.get_node(1)
        node2 = self.get_node(2)
        
        # Get chain length
        length1 = node1.get_chain_length()
        
        result['steps'].append({
            'action': 'Node 1 chain state',
            'blocks': length1,
            'is_valid': node1.engine.verify_chain()[0]
        })
        
        # Try to sync
        was_updated, message = node2.sync_with_node(node1)
        
        result['steps'].append({
            'action': 'Node 2 synchronization attempt',
            'result': was_updated,
            'message': message
        })
        
        result['conclusion'] = 'If Node 2 has longer chain and it passes validation, synchronization succeeds. Otherwise, rejected.'
        
        return result
    
    def export_network_state(self) -> dict:
        """Export entire network state"""
        return {
            'total_nodes': len(self.nodes),
            'nodes': self.get_all_nodes_state(),
            'chain_lengths': [node.get_chain_length() for node in self.nodes],
            'all_synchronized': len(set(node.get_chain_length() for node in self.nodes)) == 1
        }
