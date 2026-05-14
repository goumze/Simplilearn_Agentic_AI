"""
Streamlit UI for Banking Customer Support AI Agent.
Interactive dashboard for agent routing, logs, tickets, and evaluation.
"""

import sys
import os

# Ensure src/ is on the path when running from project root
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from database import init_db, get_all_logs, get_all_tickets
from workflow import run_support_agent
from rag import get_all_rag_records

# Initialize DB on first run
init_db()

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Banking Support AI Agent",
    page_icon="🏦",
    layout="wide",
)

st.title("🏦 Banking Customer Support AI Agent")
st.caption("Multi-Agent System powered by LangGraph + OpenAI")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Configuration")
    customer_name = st.text_input("Customer Name", value="Valued Customer")
    st.markdown("---")
    st.markdown(
        "**Agent Flow**\n\n"
        "1. **RAG Retrieval** — fetch similar past conversations\n"
        "2. **Classifier Agent** — classifies message (RAG-enhanced)\n"
        "3. **Feedback Handler** — positive / negative (RAG-enhanced)\n"
        "4. **Query Handler** — ticket status lookup (RAG-enhanced)\n"
        "5. **Logger** — persists to SQLite\n"
        "6. **RAG Storage** — embeds & stores in LanceDB (FAISS)"
    )
    st.markdown("---")
    st.markdown("**Sample Messages**")
    samples = {
        "Positive Feedback": "Thanks for sorting out my net banking login issue.",
        "Negative Feedback": "My debit card replacement still hasn't arrived.",
        "Ticket Query": "Could you check the status of ticket 650932?",
    }
    for label, msg in samples.items():
        if st.button(label, width="stretch"):
            st.session_state["prefill"] = msg

# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------
tab_chat, tab_tickets, tab_logs, tab_rag, tab_eval = st.tabs(
    ["💬 Chat", "🎫 Tickets", "📋 Logs", "🧠 RAG Store", "📊 Evaluation"]
)

# ---- Chat tab ----
with tab_chat:
    st.subheader("Submit a Message")

    prefill = st.session_state.pop("prefill", "")
    user_message = st.text_area(
        "Your message",
        value=prefill,
        height=100,
        placeholder="Type your feedback or query here...",
    )

    if st.button("Send", type="primary", width="content"):
        if not user_message.strip():
            st.warning("Please enter a message.")
        elif not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your-openai-api-key-here":
            st.error("OPENAI_API_KEY is not set. Please update your .env file.")
        else:
            with st.spinner("Processing through agent pipeline..."):
                try:
                    result = run_support_agent(user_message.strip(), customer_name)

                    # --- RAG context expander ---
                    if result.get("rag_hits"):
                        with st.expander(f"🧠 RAG Context ({len(result['rag_hits'])} similar conversation(s) retrieved)"):
                            for i, hit in enumerate(result["rag_hits"], 1):
                                dist = hit.get("_distance")
                                sim_str = f" — similarity: {1 - float(dist):.2f}" if dist is not None else ""
                                st.markdown(f"**[{i}]{sim_str}**")
                                st.markdown(f"- **Prior message:** {hit['user_message']}")
                                st.markdown(f"- **Classification:** `{hit['classification']}`")
                                st.markdown(f"- **Response given:** {hit['response']}")
                                st.divider()
                    else:
                        st.info("No similar past conversations found in RAG store (store is empty or this is the first interaction).")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### Agent Pipeline Result")
                        badge_color = {
                            "positive_feedback": "green",
                            "negative_feedback": "red",
                            "query": "blue",
                        }.get(result["classification"], "gray")

                        st.markdown(
                            f"**Classification:** :{badge_color}[{result['classification'].replace('_', ' ').title()}]"
                        )
                        st.markdown(f"**Agent Used:** `{result['agent_used']}`")
                        if result.get("ticket_id"):
                            st.markdown(f"**Ticket ID:** `#{result['ticket_id']}`")

                    with col2:
                        st.markdown("#### Response to Customer")
                        st.success(result["response"])

                except Exception as e:
                    st.error(f"Error: {e}")

# ---- Tickets tab ----
with tab_tickets:
    st.subheader("Support Tickets Database")
    if st.button("🔄 Refresh", key="refresh_tickets"):
        st.rerun()

    tickets = get_all_tickets()
    if tickets:
        df = pd.DataFrame(tickets)
        # Colour-code status
        def highlight_status(val):
            colors = {"Resolved": "background-color: #d4edda", "Unresolved": "background-color: #f8d7da", "In Progress": "background-color: #fff3cd"}
            return colors.get(val, "")

        styled = df.style.map(highlight_status, subset=["status"])
        st.dataframe(styled, width="stretch")
    else:
        st.info("No tickets found.")

# ---- Logs tab ----
with tab_logs:
    st.subheader("Agent Interaction Logs")
    if st.button("🔄 Refresh", key="refresh_logs"):
        st.rerun()

    logs = get_all_logs()
    if logs:
        df = pd.DataFrame(logs)
        df["success"] = df["success"].map({1: "✅ Yes", 0: "❌ No"})
        st.dataframe(df, width="stretch")

        # Summary metrics
        st.markdown("---")
        total = len(logs)
        success_count = sum(1 for log in logs if log["success"] in (1, "✅ Yes"))
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Interactions", total)
        col2.metric("Successful", success_count)
        col3.metric("Success Rate", f"{success_count / total * 100:.1f}%" if total else "N/A")
    else:
        st.info("No logs found yet. Submit a message in the Chat tab.")

# ---- RAG Store tab ----
with tab_rag:
    st.subheader("RAG Vector Store — LanceDB + FAISS")
    st.markdown(
        "All completed conversations are embedded using **OpenAI text-embedding-3-small** "
        "and stored in **LanceDB** with a **FAISS IVF-PQ** index. "
        f"The index is built automatically after {50} records.  "
        "Incoming messages are matched against this store to retrieve relevant past "
        "interactions that are injected into every agent's system prompt."
    )

    if st.button("🔄 Refresh", key="refresh_rag"):
        st.rerun()

    records = get_all_rag_records()
    if records:
        # Drop the vector field for display
        df = pd.DataFrame(records).drop(columns=["vector"], errors="ignore")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Embeddings", len(records))
        breakdown = df["classification"].value_counts().to_dict() if "classification" in df.columns else {}
        col2.metric("Positive Feedback", breakdown.get("positive_feedback", 0))
        col3.metric("Negative Feedback / Query",
                    breakdown.get("negative_feedback", 0) + breakdown.get("query", 0))
        st.markdown("---")
        st.dataframe(df, width="stretch")
    else:
        st.info(
            "The RAG store is empty. Submit messages in the Chat tab to populate it. "
            "Embeddings are created after each interaction."
        )

# ---- Evaluation tab ----
with tab_eval:
    st.subheader("Model Evaluation")
    st.markdown(
        "Run the built-in test suite to evaluate classification accuracy, "
        "response quality, and agent routing success rate."
    )

    if st.button("▶ Run Evaluation", type="primary"):
        if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your-openai-api-key-here":
            st.error("OPENAI_API_KEY is not set. Please update your .env file.")
        else:
            from evaluation import run_evaluation
            with st.spinner("Running evaluation test cases..."):
                summary = run_evaluation()

            st.markdown("### Results")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Cases", summary["total_cases"])
            col2.metric("Routing Success Rate", f"{summary['routing_success_rate'] * 100:.1f}%")
            col3.metric("Avg Response Score", f"{summary['average_response_score']:.2f}")

            st.markdown("#### Per-Class Accuracy")
            acc_data = [
                {"Classification": cls.replace("_", " ").title(), "Accuracy": f"{acc * 100:.1f}%"}
                for cls, acc in summary["classification_accuracy"].items()
            ]
            st.table(pd.DataFrame(acc_data))

            st.markdown("#### Detailed Results")
            rows = []
            for r in summary["results"]:
                rows.append(
                    {
                        "Description": r.test_case.description,
                        "Expected": r.test_case.expected_classification,
                        "Actual": r.actual_classification,
                        "Routing Correct": "✅" if r.routing_correct else "❌",
                        "Score": r.score,
                        "Response (truncated)": r.response[:80] + "..." if len(r.response) > 80 else r.response,
                    }
                )
            st.dataframe(pd.DataFrame(rows), width="stretch")
