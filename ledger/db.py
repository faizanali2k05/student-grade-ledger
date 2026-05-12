"""
Database operations for Student Grade Ledger
Handles SQLite database operations for blocks and transactions
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Tuple
from .models import Transaction, Block, Grade


class GradeLedgerDB:
    """Database manager for grade ledger"""
    
    def __init__(self, db_path: str = "database/ledger.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self._ensure_directory()
        self.connection = None
        self.init_db()
    
    def _ensure_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create blocks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                block_id INTEGER PRIMARY KEY AUTOINCREMENT,
                prev_hash TEXT NOT NULL,
                merkle_root TEXT NOT NULL,
                block_hash TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                nonce INTEGER NOT NULL,
                num_transactions INTEGER NOT NULL,
                UNIQUE(block_id)
            )
        ''')
        
        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                tx_id TEXT PRIMARY KEY,
                block_id INTEGER,
                student_id TEXT NOT NULL,
                student_name TEXT NOT NULL,
                course_code TEXT NOT NULL,
                grade TEXT NOT NULL,
                valid_time TEXT NOT NULL,
                transaction_time TEXT NOT NULL,
                tx_hash TEXT UNIQUE NOT NULL,
                FOREIGN KEY(block_id) REFERENCES blocks(block_id),
                UNIQUE(student_id, course_code, valid_time)
            )
        ''')
        
        # Create mempool table (pending transactions)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mempool (
                tx_id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                student_name TEXT NOT NULL,
                course_code TEXT NOT NULL,
                grade TEXT NOT NULL,
                valid_time TEXT NOT NULL,
                transaction_time TEXT NOT NULL,
                tx_hash TEXT UNIQUE NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def connect(self):
        """Create connection to database"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    def insert_block(self, block: Block) -> bool:
        """Insert block into database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO blocks
                (block_id, prev_hash, merkle_root, block_hash, timestamp, nonce, num_transactions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                block.block_id,
                block.prev_hash,
                block.merkle_root,
                block.block_hash,
                block.timestamp,
                block.nonce,
                len(block.transactions)
            ))
            
            # Insert transactions
            for tx in block.transactions:
                cursor.execute('''
                    INSERT INTO transactions
                    (tx_id, block_id, student_id, student_name, course_code, grade, valid_time, transaction_time, tx_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tx.tx_id,
                    block.block_id,
                    tx.student_id,
                    tx.student_name,
                    tx.course_code,
                    tx.grade,
                    tx.valid_time,
                    tx.transaction_time,
                    tx.tx_hash
                ))
                
                # Remove from mempool
                cursor.execute('DELETE FROM mempool WHERE tx_id = ?', (tx.tx_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error inserting block: {e}")
            return False
    
    def add_to_mempool(self, grade: Grade) -> Tuple[bool, str]:
        """Add grade to mempool (pending transactions)"""
        try:
            tx_hash = Transaction.create_hash(grade)
            tx_id = tx_hash[:16]
            transaction_time = datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO mempool
                (tx_id, student_id, student_name, course_code, grade, valid_time, transaction_time, tx_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tx_id,
                grade.student_id,
                grade.student_name,
                grade.course_code,
                grade.grade,
                grade.valid_time,
                transaction_time,
                tx_hash
            ))
            
            conn.commit()
            conn.close()
            return True, tx_hash
        except sqlite3.IntegrityError as e:
            return False, f"Duplicate entry or constraint violation: {str(e)}"
        except Exception as e:
            return False, str(e)
    
    def get_mempool(self) -> List[Transaction]:
        """Get all pending transactions from mempool"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM mempool ORDER BY transaction_time ASC')
        rows = cursor.fetchall()
        
        transactions = []
        for row in rows:
            tx = Transaction(
                tx_id=row['tx_id'],
                student_id=row['student_id'],
                student_name=row['student_name'],
                course_code=row['course_code'],
                grade=row['grade'],
                valid_time=row['valid_time'],
                transaction_time=row['transaction_time'],
                tx_hash=row['tx_hash']
            )
            transactions.append(tx)
        
        conn.close()
        return transactions
    
    def get_mempool_count(self) -> int:
        """Get number of pending transactions"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM mempool')
        count = cursor.fetchone()['count']
        conn.close()
        return count
    
    def clear_mempool(self):
        """Clear mempool (call after block mining)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('DELETE FROM mempool')
        conn.commit()
        conn.close()
    
    def get_blocks(self, limit: Optional[int] = None) -> List[Block]:
        """Get all blocks or limited number"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if limit:
            cursor.execute('SELECT * FROM blocks ORDER BY block_id DESC LIMIT ?', (limit,))
        else:
            cursor.execute('SELECT * FROM blocks ORDER BY block_id ASC')
        
        rows = cursor.fetchall()
        blocks = []
        
        for row in rows:
            block = Block(
                block_id=row['block_id'],
                prev_hash=row['prev_hash'],
                merkle_root=row['merkle_root'],
                block_hash=row['block_hash'],
                timestamp=row['timestamp'],
                nonce=row['nonce']
            )
            
            # Get transactions for this block
            cursor.execute(
                'SELECT * FROM transactions WHERE block_id = ? ORDER BY transaction_time ASC',
                (row['block_id'],)
            )
            tx_rows = cursor.fetchall()
            
            for tx_row in tx_rows:
                tx = Transaction(
                    tx_id=tx_row['tx_id'],
                    student_id=tx_row['student_id'],
                    student_name=tx_row['student_name'],
                    course_code=tx_row['course_code'],
                    grade=tx_row['grade'],
                    valid_time=tx_row['valid_time'],
                    transaction_time=tx_row['transaction_time'],
                    tx_hash=tx_row['tx_hash'],
                    block_id=tx_row['block_id']
                )
                block.transactions.append(tx)
            
            blocks.append(block)
        
        conn.close()
        return blocks
    
    def get_block_by_id(self, block_id: int) -> Optional[Block]:
        """Get specific block by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM blocks WHERE block_id = ?', (block_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        block = Block(
            block_id=row['block_id'],
            prev_hash=row['prev_hash'],
            merkle_root=row['merkle_root'],
            block_hash=row['block_hash'],
            timestamp=row['timestamp'],
            nonce=row['nonce']
        )
        
        cursor.execute('SELECT * FROM transactions WHERE block_id = ?', (block_id,))
        tx_rows = cursor.fetchall()
        
        for tx_row in tx_rows:
            tx = Transaction(
                tx_id=tx_row['tx_id'],
                student_id=tx_row['student_id'],
                student_name=tx_row['student_name'],
                course_code=tx_row['course_code'],
                grade=tx_row['grade'],
                valid_time=tx_row['valid_time'],
                transaction_time=tx_row['transaction_time'],
                tx_hash=tx_row['tx_hash'],
                block_id=tx_row['block_id']
            )
            block.transactions.append(tx)
        
        conn.close()
        return block
    
    def get_latest_block(self) -> Optional[Block]:
        """Get the most recent block"""
        blocks = self.get_blocks(limit=1)
        if blocks:
            return blocks[0] if len(blocks) == 1 else max(blocks, key=lambda b: b.block_id)
        return None
    
    def get_transaction_by_student_course(self, student_id: str, course_code: str, valid_time: str) -> Optional[Transaction]:
        """Search for a specific transaction"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE student_id = ? AND course_code = ? AND valid_time = ?
        ''', (student_id, course_code, valid_time))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Transaction(
            tx_id=row['tx_id'],
            student_id=row['student_id'],
            student_name=row['student_name'],
            course_code=row['course_code'],
            grade=row['grade'],
            valid_time=row['valid_time'],
            transaction_time=row['transaction_time'],
            tx_hash=row['tx_hash'],
            block_id=row['block_id']
        )
    
    def get_total_transactions(self) -> int:
        """Get total number of confirmed transactions"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM transactions')
        count = cursor.fetchone()['count']
        conn.close()
        return count
    
    def get_total_blocks(self) -> int:
        """Get total number of blocks"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM blocks')
        count = cursor.fetchone()['count']
        conn.close()
        return count
    
    def get_block_hashes(self) -> List[str]:
        """Get all block hashes for verification"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT block_hash, prev_hash FROM blocks ORDER BY block_id ASC')
        rows = cursor.fetchall()
        conn.close()
        return rows
