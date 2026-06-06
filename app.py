"""
Streamlit UI for Student Grade Ledger
A blockchain-backed, tamper-evident academic record system.

Pages:
  Dashboard · Add Grade · Blockchain Explorer · Verify Grade ·
  Student Transcript · Tamper Demo · Consensus Demo · Tools & Export
"""

import json
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

from ledger import GradeLedgerDB, BlockchainEngine, Grade, ConsensusSimulator
from ledger.merkle import MerkleTree

# --------------------------------------------------------------------------- #
# Configuration & constants
# --------------------------------------------------------------------------- #
DB_PATH = "database/ledger.db"

GRADE_OPTIONS = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"]

# Standard 4.0 grade-point mapping used for GPA computation.
GRADE_POINTS = {
    "A+": 4.0, "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0, "F": 0.0,
}

st.set_page_config(
    page_title="Student Grade Ledger",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------- #
# Services (cached for the session)
# --------------------------------------------------------------------------- #
@st.cache_resource
def get_services():
    db = GradeLedgerDB(DB_PATH)
    engine = BlockchainEngine(db)
    consensus = ConsensusSimulator()
    return db, engine, consensus


DB, ENGINE, CONSENSUS = get_services()


# --------------------------------------------------------------------------- #
# Styling
# --------------------------------------------------------------------------- #
def inject_css():
    st.markdown(
        """
        <style>
        /* Hash chips */
        .hash-chip {
            font-family: 'SFMono-Regular', Consolas, monospace;
            background: rgba(99, 102, 241, 0.12);
            color: #6366f1;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 0.82rem;
            word-break: break-all;
        }
        /* Status badges */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 999px;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .badge-ok   { background: rgba(34,197,94,.15);  color: #16a34a; }
        .badge-bad  { background: rgba(239,68,68,.15);  color: #dc2626; }
        .badge-warn { background: rgba(234,179,8,.18);  color: #ca8a04; }
        /* Cards */
        .card {
            border: 1px solid rgba(148,163,184,.25);
            border-radius: 12px;
            padding: 16px 18px;
            background: rgba(148,163,184,.05);
            margin-bottom: 10px;
        }
        .grade-pill {
            display:inline-block; min-width:34px; text-align:center;
            padding:2px 10px; border-radius:8px; font-weight:700;
            background:rgba(99,102,241,.15); color:#6366f1;
        }
        .muted { color:#94a3b8; font-size:.85rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def chip(text: str) -> str:
    return f"<span class='hash-chip'>{text}</span>"


def short(h: str, n: int = 12) -> str:
    if not h:
        return "—"
    return h if len(h) <= n + 3 else f"{h[:n]}…"


def all_confirmed_transactions():
    """Flatten every confirmed transaction across all blocks."""
    rows = []
    for block in DB.get_blocks():
        for tx in block.transactions:
            d = tx.to_dict()
            d["block_id"] = block.block_id
            rows.append(d)
    return rows


def compute_gpa(grades):
    """grades: iterable of grade-letter strings -> (gpa, counted)."""
    pts, counted = 0.0, 0
    for g in grades:
        if g in GRADE_POINTS:
            pts += GRADE_POINTS[g]
            counted += 1
    return (round(pts / counted, 2) if counted else 0.0), counted


def chain_status_badge(is_valid: bool) -> str:
    if is_valid:
        return "<span class='badge badge-ok'>✓ Chain Valid</span>"
    return "<span class='badge badge-bad'>✗ Chain Compromised</span>"


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
st.sidebar.title("🎓 Grade Ledger")
st.sidebar.caption("Blockchain-backed academic records")

PAGES = {
    "Dashboard": "📊",
    "Add Grade": "➕",
    "Blockchain Explorer": "🔗",
    "Verify Grade": "✅",
    "Student Transcript": "📜",
    "Tamper Demo": "🛡️",
    "Consensus Demo": "🌐",
    "Tools & Export": "⚙️",
}

page = st.sidebar.radio(
    "Navigate",
    list(PAGES.keys()),
    format_func=lambda p: f"{PAGES[p]}  {p}",
)

# Live mini-status in the sidebar
_state = ENGINE.get_blockchain_state()
st.sidebar.divider()
st.sidebar.markdown(chain_status_badge(_state.is_valid), unsafe_allow_html=True)
sc1, sc2 = st.sidebar.columns(2)
sc1.metric("Blocks", _state.total_blocks)
sc2.metric("Grades", _state.total_transactions)
if _state.pending_transactions:
    st.sidebar.progress(
        min(_state.pending_transactions / 10, 1.0),
        text=f"Mempool {_state.pending_transactions}/10",
    )
st.sidebar.caption(f"Latest: {short(_state.latest_block_hash, 16)}")


# =========================================================================== #
# DASHBOARD
# =========================================================================== #
if page == "Dashboard":
    st.title("📊 Dashboard")
    state = ENGINE.get_blockchain_state()
    is_valid, issues = ENGINE.verify_chain()

    st.markdown(chain_status_badge(is_valid), unsafe_allow_html=True)
    if not is_valid:
        with st.expander("⚠️ Integrity issues detected", expanded=True):
            for i in issues:
                st.error(i)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Blocks", state.total_blocks)
    c2.metric("Confirmed Grades", state.total_transactions)
    c3.metric("Pending (mempool)", state.pending_transactions)
    avg_tx = round(state.total_transactions / state.total_blocks, 1) if state.total_blocks else 0
    c4.metric("Avg Tx / Block", avg_tx)

    st.divider()
    txs = all_confirmed_transactions()

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Grade distribution")
        if txs:
            df = pd.DataFrame(txs)
            dist = (
                df["grade"].value_counts()
                .reindex(GRADE_OPTIONS)
                .dropna()
                .astype(int)
            )
            st.bar_chart(dist)
        else:
            st.info("No confirmed grades yet. Add some on the **Add Grade** page.")

    with right:
        st.subheader("Mempool")
        pending = DB.get_mempool()
        st.progress(min(len(pending) / 10, 1.0), text=f"{len(pending)}/10 until auto-mine")
        if pending:
            st.dataframe(
                pd.DataFrame([t.to_dict() for t in pending])[
                    ["student_id", "course_code", "grade"]
                ],
                hide_index=True,
                use_container_width=True,
            )
            if st.button("⛏️ Mine block now", type="primary"):
                block = ENGINE.mine_block()
                if block:
                    st.success(f"Mined block {block.block_id} (nonce {block.nonce}).")
                    st.rerun()
        else:
            st.caption("Empty — all grades confirmed.")

    if txs:
        st.divider()
        st.subheader("Recent activity")
        recent = pd.DataFrame(txs).sort_values("transaction_time", ascending=False).head(8)
        st.dataframe(
            recent[["block_id", "student_name", "course_code", "grade", "valid_time"]],
            hide_index=True,
            use_container_width=True,
        )


# =========================================================================== #
# ADD GRADE
# =========================================================================== #
elif page == "Add Grade":
    st.title("➕ Add Grade Transaction")
    st.caption("New grades enter the mempool and are auto-mined into a block every 10 entries.")

    with st.form("add_grade_form"):
        a, b = st.columns(2)
        student_id = a.text_input("Student ID", placeholder="e.g. S1024")
        student_name = b.text_input("Student Name", placeholder="e.g. Ayesha Khan")
        c, d, e = st.columns(3)
        course_code = c.text_input("Course Code", placeholder="e.g. CS101")
        grade = d.selectbox("Grade", GRADE_OPTIONS)
        semester = e.text_input("Semester", placeholder="e.g. Spring 2024")
        submitted = st.form_submit_button("Submit Grade", type="primary")

        if submitted:
            if not (student_id and student_name and course_code and semester):
                st.error("All fields are required.")
            else:
                grade_obj = Grade(
                    student_id=student_id.strip(),
                    student_name=student_name.strip(),
                    course_code=course_code.strip().upper(),
                    grade=grade,
                    valid_time=semester.strip(),
                )
                success, msg = ENGINE.add_grade(grade_obj)
                if success:
                    st.success(msg)
                    st.balloons()
                else:
                    st.error(msg)

    st.divider()
    pending = DB.get_mempool()
    st.subheader(f"Mempool — {len(pending)} pending")
    st.progress(min(len(pending) / 10, 1.0))
    if pending:
        st.dataframe(
            pd.DataFrame([t.to_dict() for t in pending])[
                ["tx_id", "student_id", "student_name", "course_code", "grade", "valid_time"]
            ],
            hide_index=True,
            use_container_width=True,
        )
        if st.button("⛏️ Mine block now", type="primary"):
            block = ENGINE.mine_block()
            if block:
                st.success(f"Mined block {block.block_id} with {len(block.transactions)} tx (nonce {block.nonce}).")
                st.rerun()
            else:
                st.warning("Nothing to mine.")
    else:
        st.caption("Mempool is empty.")


# =========================================================================== #
# BLOCKCHAIN EXPLORER
# =========================================================================== #
elif page == "Blockchain Explorer":
    st.title("🔗 Blockchain Explorer")
    blocks = DB.get_blocks()

    if not blocks:
        st.info("No blocks mined yet.")
    else:
        q = st.text_input("🔍 Filter by student, course, grade or hash", "").strip().lower()

        # Visual chain overview via graphviz
        with st.expander("Chain overview diagram"):
            dot = ["digraph chain { rankdir=LR; node [shape=box, style=filled, fillcolor=\"#e0e7ff\"];"]
            for blk in blocks:
                dot.append(
                    f'b{blk.block_id} [label="Block {blk.block_id}\\n{blk.block_hash[:8]}…\\n{len(blk.transactions)} tx"];'
                )
            for i in range(1, len(blocks)):
                dot.append(f"b{blocks[i-1].block_id} -> b{blocks[i].block_id};")
            dot.append("}")
            st.graphviz_chart("\n".join(dot))

        for block in reversed(blocks):  # newest first
            # Filter logic
            if q:
                hay = (block.block_hash + block.merkle_root).lower()
                hay += " ".join(
                    f"{t.student_id}{t.student_name}{t.course_code}{t.grade}".lower()
                    for t in block.transactions
                )
                if q not in hay:
                    continue

            title = f"🧱 Block {block.block_id}  ·  {len(block.transactions)} tx  ·  {short(block.block_hash, 14)}"
            with st.expander(title):
                m1, m2, m3 = st.columns(3)
                m1.markdown(f"**Block hash**<br>{chip(block.block_hash)}", unsafe_allow_html=True)
                m2.markdown(f"**Prev hash**<br>{chip(block.prev_hash)}", unsafe_allow_html=True)
                m3.markdown(f"**Merkle root**<br>{chip(block.merkle_root)}", unsafe_allow_html=True)
                st.markdown(
                    f"<span class='muted'>Nonce: {block.nonce} · Timestamp: {block.timestamp}</span>",
                    unsafe_allow_html=True,
                )
                if block.transactions:
                    st.dataframe(
                        pd.DataFrame([t.to_dict() for t in block.transactions])[
                            ["student_id", "student_name", "course_code", "grade", "valid_time", "tx_hash"]
                        ],
                        hide_index=True,
                        use_container_width=True,
                    )


# =========================================================================== #
# VERIFY GRADE
# =========================================================================== #
elif page == "Verify Grade":
    st.title("✅ Verify Grade")
    st.caption("Generate a Merkle proof showing a grade is included in the chain — without revealing the whole block.")

    a, b, c = st.columns(3)
    student_id = a.text_input("Student ID")
    course_code = b.text_input("Course Code")
    semester = c.text_input("Semester")

    if st.button("Get Merkle Proof", type="primary"):
        proof = ENGINE.get_merkle_proof_for_grade(
            student_id.strip(), course_code.strip().upper(), semester.strip()
        )
        if not proof:
            st.error("Grade not found or not yet mined into a block.")
        else:
            if proof["is_valid"]:
                st.markdown(
                    "<span class='badge badge-ok'>✓ Proof verified — grade is authentic</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<span class='badge badge-bad'>✗ Proof failed</span>",
                    unsafe_allow_html=True,
                )

            tx = proof["transaction"]
            st.subheader("Grade record")
            g1, g2, g3, g4 = st.columns(4)
            g1.metric("Student", tx["student_id"])
            g2.metric("Course", tx["course_code"])
            g3.markdown(f"**Grade**<br><span class='grade-pill'>{tx['grade']}</span>", unsafe_allow_html=True)
            g4.metric("In block", proof["block_id"])

            st.markdown(f"**Transaction hash:** {chip(tx['tx_hash'])}", unsafe_allow_html=True)
            st.markdown(f"**Merkle root:** {chip(proof['merkle_root'])}", unsafe_allow_html=True)

            st.subheader("Proof path (sibling hashes)")
            path = proof["proof"]["proof_path"]
            if path:
                st.dataframe(
                    pd.DataFrame(
                        [{"step": i + 1, "direction": d, "sibling_hash": h} for i, (h, d) in enumerate(path)]
                    ),
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.caption("Single-transaction block — the leaf is the root.")

            # Merkle tree visualization
            block = DB.get_block_by_id(proof["block_id"])
            if block and block.transactions:
                st.subheader("Merkle tree")
                st.graphviz_chart(MerkleTree.visualize_tree(block.transactions))


# =========================================================================== #
# STUDENT TRANSCRIPT  (new)
# =========================================================================== #
elif page == "Student Transcript":
    st.title("📜 Student Transcript")
    st.caption("Aggregate every confirmed grade for a student and compute GPA.")

    txs = all_confirmed_transactions()
    if not txs:
        st.info("No confirmed grades in the ledger yet.")
    else:
        df = pd.DataFrame(txs)
        students = sorted(df["student_id"].unique())
        sid = st.selectbox("Select Student ID", students)
        sub = df[df["student_id"] == sid].copy()
        name = sub["student_name"].iloc[0]

        gpa, counted = compute_gpa(sub["grade"])
        st.subheader(f"{name}  ·  {sid}")
        k1, k2, k3 = st.columns(3)
        k1.metric("Cumulative GPA", gpa)
        k2.metric("Courses", len(sub))
        k3.metric("Semesters", sub["valid_time"].nunique())

        sub["points"] = sub["grade"].map(GRADE_POINTS)
        st.dataframe(
            sub[["valid_time", "course_code", "grade", "points", "block_id"]]
            .sort_values("valid_time"),
            hide_index=True,
            use_container_width=True,
        )

        # Per-semester GPA breakdown
        st.subheader("GPA by semester")
        sem_rows = []
        for sem, grp in sub.groupby("valid_time"):
            sem_gpa, _ = compute_gpa(grp["grade"])
            sem_rows.append({"semester": sem, "gpa": sem_gpa, "courses": len(grp)})
        sem_df = pd.DataFrame(sem_rows).set_index("semester")
        st.bar_chart(sem_df["gpa"])

        st.download_button(
            "⬇️ Download transcript (CSV)",
            sub[["valid_time", "course_code", "grade", "points"]].to_csv(index=False),
            file_name=f"transcript_{sid}.csv",
            mime="text/csv",
        )


# =========================================================================== #
# TAMPER DEMO  (interactive)
# =========================================================================== #
elif page == "Tamper Demo":
    st.title("🛡️ Tamper Demonstration")
    st.caption(
        "Edit a confirmed grade directly in the database, then re-verify the chain. "
        "Because each block commits to a Merkle root, any change breaks verification."
    )

    is_valid, issues = ENGINE.verify_chain()
    st.markdown(chain_status_badge(is_valid), unsafe_allow_html=True)
    if not is_valid:
        with st.expander("Current issues", expanded=True):
            for i in issues:
                st.error(i)

    txs = all_confirmed_transactions()
    if not txs:
        st.info("Mine at least one block first to run the tamper demo.")
    else:
        df = pd.DataFrame(txs)
        st.divider()
        st.subheader("1 · Pick a grade to tamper with")
        labels = {
            f"{r.student_id} · {r.course_code} · {r.grade} (block {r.block_id})": r.tx_id
            for r in df.itertuples()
        }
        choice = st.selectbox("Confirmed transaction", list(labels.keys()))
        new_grade = st.selectbox("Change grade to", GRADE_OPTIONS)

        col1, col2 = st.columns(2)
        if col1.button("💣 Tamper now", type="primary"):
            tx_id = labels[choice]
            conn = sqlite3.connect(DB_PATH)
            conn.execute("UPDATE transactions SET grade = ? WHERE tx_id = ?", (new_grade, tx_id))
            conn.commit()
            conn.close()
            ok, probs = ENGINE.verify_chain()
            if ok:
                st.warning("Chain still validates (grade may have been unchanged).")
            else:
                st.error("Tamper detected! Chain verification now FAILS:")
                for p in probs:
                    st.code(p)

        if col2.button("🔁 Re-run verification"):
            ok, probs = ENGINE.verify_chain()
            if ok:
                st.success("Chain is valid.")
            else:
                st.error("Chain invalid:")
                for p in probs:
                    st.code(p)

        st.caption(
            "💡 Tampering changes the data but not the stored Merkle root, so the recomputed "
            "root no longer matches — exactly how real blockchains stay tamper-evident."
        )


# =========================================================================== #
# CONSENSUS DEMO
# =========================================================================== #
elif page == "Consensus Demo":
    st.title("🌐 Consensus Demo")
    st.caption("Three independent nodes reconcile to the longest valid chain.")

    states = CONSENSUS.get_all_nodes_state()
    cols = st.columns(len(states))
    for col, s in zip(cols, states):
        with col:
            badge = chain_status_badge(s["is_valid"])
            st.markdown(f"### 🖥️ Node {s['node_id']}")
            st.markdown(badge, unsafe_allow_html=True)
            st.metric("Blocks", s["total_blocks"])
            st.metric("Grades", s["total_transactions"])
            st.markdown(f"<span class='muted'>{short(s['latest_block_hash'], 16)}</span>", unsafe_allow_html=True)

    lengths = [s["total_blocks"] for s in states]
    synced = len(set(lengths)) == 1
    st.markdown(
        f"**Network status:** "
        + (
            "<span class='badge badge-ok'>All nodes synchronized</span>"
            if synced
            else "<span class='badge badge-warn'>Nodes diverged</span>"
        ),
        unsafe_allow_html=True,
    )

    st.divider()
    a, b, c = st.columns(3)
    mine_on = a.selectbox("Mine a block on node", [s["node_id"] for s in states])
    if a.button("⛏️ Mine on node"):
        node = CONSENSUS.get_node(mine_on)
        block = node.engine.mine_block()
        if block:
            st.success(f"Node {mine_on} mined block {block.block_id}.")
        else:
            st.warning(f"Node {mine_on} has no pending grades to mine.")
        st.rerun()

    if b.button("🔄 Synchronize all nodes", type="primary"):
        events = CONSENSUS.synchronize_all_nodes()
        for ev in events:
            if ev["step"] == "initial_state":
                st.write("**Initial chain lengths:**", {f"Node {x['node_id']}": x["length"] for x in ev["chain_lengths"]})
            elif ev["step"] == "final_state":
                st.success(
                    f"Final: nodes_synchronized={ev['nodes_synchronized']}, all_valid={ev['all_valid']}"
                )
            else:
                icon = "✅" if ev.get("updated") else "➖"
                st.write(f"{icon} {ev['message']}")
        st.rerun()

    if c.button("♻️ Reset nodes"):
        CONSENSUS.reset_nodes()
        st.info("All node databases reset to empty.")
        st.rerun()

    with st.expander("Raw network state"):
        st.json(CONSENSUS.export_network_state())


# =========================================================================== #
# TOOLS & EXPORT  (new)
# =========================================================================== #
elif page == "Tools & Export":
    st.title("⚙️ Tools & Export")

    state = ENGINE.get_blockchain_state()
    txs = all_confirmed_transactions()

    st.subheader("Ledger analytics")
    if txs:
        df = pd.DataFrame(txs)
        a, b, c = st.columns(3)
        a.metric("Unique students", df["student_id"].nunique())
        b.metric("Unique courses", df["course_code"].nunique())
        gpa, _ = compute_gpa(df["grade"])
        c.metric("Mean grade point", gpa)

        st.markdown("**Grades per course**")
        st.bar_chart(df["course_code"].value_counts())
    else:
        st.info("No data to analyze yet.")

    st.divider()
    st.subheader("Export full chain")
    chain = ENGINE.export_chain_json()
    st.json({k: v for k, v in chain.items() if k != "blocks"})
    st.download_button(
        "⬇️ Download chain as JSON",
        json.dumps(chain, indent=2),
        file_name=f"grade_ledger_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json",
    )

    st.divider()
    st.subheader("Integrity check")
    if st.button("Run full verification"):
        ok, issues = ENGINE.verify_chain()
        if ok:
            st.success("✓ Entire chain verified — no tampering detected.")
        else:
            st.error("✗ Verification failed:")
            for i in issues:
                st.code(i)
