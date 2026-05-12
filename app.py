"""
Streamlit UI for Student Grade Ledger
Provides pages: Dashboard, Add Grade, Blockchain Explorer, Verify Grade, Tamper Demo, Consensus Demo
"""

import streamlit as st
from ledger import GradeLedgerDB, BlockchainEngine, Grade, ConsensusSimulator
from ledger.merkle import MerkleTree

st.set_page_config(page_title="Student Grade Ledger", layout="wide")

@st.cache_resource
def get_services():
    db = GradeLedgerDB("database/ledger.db")
    engine = BlockchainEngine(db)
    consensus = ConsensusSimulator()
    return db, engine, consensus

DB, ENGINE, CONSENSUS = get_services()

# Sidebar navigation
st.sidebar.title("Student Grade Ledger")
page = st.sidebar.radio("Navigate", ["Dashboard", "Add Grade", "Blockchain Explorer", "Verify Grade", "Tamper Demo", "Consensus Demo"]) 

if page == "Dashboard":
    st.title("Dashboard")
    state = ENGINE.get_blockchain_state()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Blocks", state.total_blocks)
    col2.metric("Total Transactions", state.total_transactions)
    col3.metric("Pending Transactions", state.pending_transactions)
    
    is_valid, issues = ENGINE.verify_chain()
    st.write("Chain Valid:", is_valid)
    if not is_valid:
        st.warning("Issues found:\n" + "\n".join(issues))

elif page == "Add Grade":
    st.title("Add Grade Transaction")
    with st.form("add_grade_form"):
        student_id = st.text_input("Student ID")
        student_name = st.text_input("Student Name")
        course_code = st.text_input("Course Code")
        grade = st.selectbox("Grade", ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "F"]) 
        semester = st.text_input("Semester (e.g., Spring 2024)")
        submitted = st.form_submit_button("Submit Grade")
        
        if submitted:
            if not (student_id and student_name and course_code and semester):
                st.error("All fields are required")
            else:
                grade_obj = Grade(student_id=student_id, student_name=student_name, course_code=course_code, grade=grade, valid_time=semester)
                success, msg = ENGINE.add_grade(grade_obj)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

elif page == "Blockchain Explorer":
    st.title("Blockchain Explorer")
    blocks = DB.get_blocks()
    for block in blocks:
        with st.expander(f"Block {block.block_id} - {block.block_hash[:12]}..."):
            st.write(block.to_dict())
            for tx in block.transactions:
                st.write(tx.to_dict())

elif page == "Verify Grade":
    st.title("Verify Grade")
    student_id = st.text_input("Student ID to verify")
    course_code = st.text_input("Course Code")
    semester = st.text_input("Semester")
    if st.button("Get Merkle Proof"):
        proof = ENGINE.get_merkle_proof_for_grade(student_id, course_code, semester)
        if not proof:
            st.error("Grade not found or not mined yet")
        else:
            st.write(proof)
            st.success("Merkle proof generated. Verification: {}".format(proof['is_valid']))

elif page == "Tamper Demo":
    st.title("Tamper Demonstration")
    st.write("This demo shows how tampering invalidates the chain. Modify a transaction directly to test.")
    if st.button("Run Chain Verification"):
        is_valid, issues = ENGINE.verify_chain()
        if is_valid:
            st.success("Chain is valid")
        else:
            st.error("Chain invalid. Issues:\n" + "\n".join(issues))

elif page == "Consensus Demo":
    st.title("Consensus Demo")
    st.write("Simulate node synchronization using longest-chain-wins rule")
    if st.button("Show Network State"):
        st.write(CONSENSUS.get_all_nodes_state())
    if st.button("Synchronize Nodes"):
        events = CONSENSUS.synchronize_all_nodes()
        st.write(events)
