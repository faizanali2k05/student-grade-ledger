# Student Grade Ledger: A Tamper-Evident Blockchain Database using Merkle Trees

**Semester Project | Advanced Database Management Systems (ADBMS)**

## 📋 Project Overview

Student Grade Ledger is a blockchain-inspired, immutable grade storage system that demonstrates advanced database concepts including:

- **Immutable Database Design** - Append-only architecture with no UPDATE/DELETE after mining
- **Merkle Tree Verification** - O(log n) proof complexity for efficient verification
- **Distributed Consensus** - Multi-node ledger synchronization with longest-chain-wins rule
- **Cryptographic Hashing** - SHA256-based hash chains for tamper detection
- **Temporal Database Concepts** - Valid time (semester) and transaction time tracking
- **Transaction Management** - Atomic block insertion with 10 transactions per block
- **Auditability** - Complete grade provenance verification

## 🏛️ Why This is Advanced DBMS

Unlike traditional CRUD applications, this project implements:

1. **Immutable Storage** - Grades cannot be modified or deleted after block mining
2. **Blockchain Architecture** - Hash-linked blocks forming an immutable chain
3. **Merkle Trees** - Efficient logarithmic verification of transaction existence
4. **Distributed Nodes** - Multi-node consensus simulation demonstrating distributed databases
5. **Audit Trail** - Complete history preservation for compliance
6. **Tamper Detection** - Automatic detection and propagation of unauthorized changes

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.11+ | Fast dev, crypto libraries, DB support |
| **Database** | SQLite | Lightweight relational DB for blocks + transactions |
| **Frontend** | Streamlit | Interactive dashboard for demo |
| **Cryptography** | hashlib (SHA256) | Native Python secure hashing |
| **Visualization** | Graphviz | Visual Merkle Tree rendering |
| **ORM** | SQLAlchemy | Cleaner DB abstraction |
| **Data Handling** | Pandas | Table operations |
| **Graph Viz** | NetworkX, Matplotlib | Blockchain visualization |

## 📁 Project Structure

```
student-grade-ledger/
│
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
│
├── database/
│   └── ledger.db                  # Main blockchain database
│
├── ledger/
│   ├── __init__.py
│   ├── models.py                  # Data models (Grade, Block, Transaction)
│   ├── db.py                      # Database operations
│   ├── blockchain.py              # Blockchain engine
│   ├── merkle.py                  # Merkle Tree implementation
│   └── consensus.py               # Consensus simulation
│
├── nodes/
│   ├── node1.db                   # Node 1 ledger
│   ├── node2.db                   # Node 2 ledger
│   └── node3.db                   # Node 3 ledger
│
├── assets/
│   └── diagrams/                  # Graphviz output diagrams
│
└── tests/
    └── test_blockchain.py         # Unit tests
```

## 📊 Database Schema

### blocks table
| Field | Type | Description |
|-------|------|-------------|
| block_id | INTEGER | Primary key |
| prev_hash | TEXT | Hash of previous block |
| merkle_root | TEXT | Root hash of all transactions |
| block_hash | TEXT | SHA256 hash of entire block |
| timestamp | TEXT | Block mining timestamp |
| nonce | INTEGER | Proof-of-work counter |
| transactions | INTEGER | Number of transactions in block |

### transactions table
| Field | Type | Description |
|-------|------|-------------|
| tx_id | TEXT | Primary key (SHA256 hash) |
| block_id | INTEGER | Reference to block (FK) |
| student_id | TEXT | Student identifier |
| student_name | TEXT | Student full name |
| course_code | TEXT | Course identifier |
| grade | TEXT | Letter grade (A+, A, B+, etc.) |
| valid_time | TEXT | Semester validity |
| transaction_time | TEXT | Insertion timestamp |
| tx_hash | TEXT | Transaction hash |
| UNIQUE(student_id, course_code, valid_time) | - | Prevent duplicate entries |

## 🔧 Functional Requirements

### FR-1: Add Grade
- Accept student grade transaction
- Generate SHA256 hash
- Store in mempool
- Display confirmation

### FR-2: Auto-Mine Block
- When pending transactions reach 10:
  - Create new block
  - Calculate Merkle Root
  - Link previous block hash
  - Insert block into DB

### FR-3: Verify Grade
- Search by student/course
- Return:
  - Block number
  - Merkle proof
  - Verification result

### FR-4: Verify Blockchain
- Validate all block hashes
- Validate prev_hash links
- Validate Merkle roots
- Detect any tampering

### FR-5: Tamper Detection
- If any grade changes:
  - Affected block invalidates
  - All subsequent blocks fail verification
  - Alert displayed

### FR-6: Consensus Simulation
- Three independent nodes maintain separate chains
- Synchronize using longest-chain-wins rule
- Show synchronization process

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- VS Code
- Graphviz (system binary) - [Download](https://graphviz.org/download/)

### Installation

1. **Clone/Create Project**
   ```bash
   cd c:\Users\Faizan\Desktop\student-grade-ledger
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Graphviz Installation**
   ```bash
   dot -V
   ```

5. **Run Application**
   ```bash
   streamlit run app.py
   ```

Browser will open to `http://localhost:8501`

## 📖 Usage Guide

### Dashboard
- View total blocks and transactions
- Check blockchain validity status
- Monitor pending transactions

### Add Grade
1. Enter student ID and name
2. Select course code
3. Choose grade
4. Select semester/valid time
5. Submit transaction
6. System auto-mines when 10 transactions accumulated

### Blockchain Explorer
- View all blocks in chain
- Inspect block hashes and merkle roots
- View transaction details
- Verify block integrity

### Verify Grade
- Search by student/course
- Generate Merkle proof
- Verify authenticity
- View transaction timestamp

### Tamper Demonstration
- Modify a grade in database directly
- Run verification - automatic detection
- Show chain invalidation cascade

### Consensus Demo
- Initialize 3 nodes with same chain
- Add grades to Node 1
- Mine block on Node 1
- Synchronize all nodes
- Show longest-chain-wins consensus

## 🔐 Security Features

1. **SHA256 Hashing** - Cryptographic hashing for all transactions and blocks
2. **Hash Chaining** - Each block linked to previous via prev_hash
3. **Merkle Trees** - Efficient verification with O(log n) complexity
4. **Immutability** - No UPDATE/DELETE after mining
5. **Tamper Detection** - Hash mismatch immediately detected
6. **Audit Trail** - Complete history preserved

## 📈 Key Algorithms

### SHA256 Hashing
```
Used for:
- Transaction hashing (tx_hash)
- Block hashing (block_hash)
- Chain linking (prev_hash)
```

### Merkle Tree
```
Combines transaction hashes:
             merkle_root
              /        \
           H1-2        H3-4
          /    \      /    \
        H1    H2    H3    H4
        |      |     |     |
      Tx1   Tx2   Tx3   Tx4
```

### Consensus Algorithm
```
Longest-Chain-Wins Rule:
- Each node maintains own chain
- On synchronization: node_chain vs received_chain
- If received_chain longer: adopt it
- Prevents dishonest nodes
```

## ✅ Success Criteria

Project succeeds if:

- ✅ Tampering is detected correctly
- ✅ Merkle proofs verify transactions
- ✅ Consensus synchronizes 3 nodes
- ✅ UI demonstrates blockchain flow clearly
- ✅ Grade immutability enforced
- ✅ Audit trail complete
- ✅ Hash chains valid

## 🎯 Viva Explanation

**"Why is this Advanced DBMS?"**

> This project implements advanced database concepts beyond traditional CRUD systems. It demonstrates:
>
> - **Immutable storage architecture** - Preventing unauthorized modifications
> - **Distributed consensus** - Multi-node synchronization with proof-of-longest-chain
> - **Cryptographic indexing** - SHA256-based hash chains and Merkle tree verification
> - **Temporal data management** - Valid time (semester) vs transaction time tracking
> - **Append-only transaction model** - All operations are inserts, never updates
> - **Tamper-evident design** - Cascading hash validation detects any changes
>
> Unlike conventional relational databases with UPDATE/DELETE capabilities, this system guarantees grade integrity and provides cryptographic proof of authenticity. It combines blockchain principles with database theory.

## 📚 ADBMS Concepts Demonstrated

1. **Immutable Database Design** - Append-only, no modifications after mining
2. **Distributed Databases** - Multi-node ledger, consensus mechanisms
3. **Transaction Management** - Atomic block insertion, ACID properties
4. **Merkle Trees** - Log-linear verification complexity
5. **Hash Chains** - Cryptographic linking and tamper propagation
6. **Temporal Databases** - Valid time and transaction time concepts
7. **Auditability** - Complete provenance preservation
8. **Data Integrity Constraints** - Uniqueness constraints on student-course-semester

## 🧪 Testing

Run tests with:
```bash
python -m pytest tests/
```

## 📝 Development Notes

- **Phase 1**: Database schema + core models
- **Phase 2**: Blockchain engine + Merkle tree
- **Phase 3**: Consensus simulation
- **Phase 4**: Streamlit UI
- **Phase 5**: Testing + documentation

## 🤝 Contributing

This is a semester project. Maintain code quality and documentation throughout development.

## 📄 License

Academic Use Only

---

**Last Updated**: May 2026  
**Project Duration**: 1-2 weeks  
**Lines of Code**: ~600-800  
**Complexity**: Advanced DBMS level
