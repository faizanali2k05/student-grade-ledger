import hashlib
from ledger.merkle import MerkleTree
from ledger.models import Transaction


def make_tx(i: int) -> Transaction:
    payload = f"tx-{i}-payload"
    tx_hash = hashlib.sha256(payload.encode()).hexdigest()
    return Transaction(
        tx_id=tx_hash[:16],
        student_id=f"S{i}",
        student_name=f"Student {i}",
        course_code=f"CSE{i}",
        grade="A",
        valid_time="Spring 2024",
        transaction_time="2024-01-01T00:00:00",
        tx_hash=tx_hash
    )


def test_merkle_root_and_proof():
    txs = [make_tx(i) for i in range(4)]
    tree = MerkleTree(txs)
    assert tree.root is not None and len(tree.root) == 64

    # pick a transaction and verify proof
    tx = txs[2]
    proof = tree.get_proof(tx.tx_hash)
    assert proof is not None
    assert tree.verify_proof(tx.tx_hash, proof) is True
