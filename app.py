import io
import base64
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

from agent import create_agent, run_query
from utils import get_dataset_summary, get_suggested_questions

matplotlib.use("Agg")

# ─── Page Config ────────────────────────────────────────────────
st.set_page_config(
    page_title="ChartTalk",
    page_icon="📊",
    layout="wide"
)

st.title("📊 ChartTalk")
st.caption("Upload any CSV and chat with your data in plain English")

# ─── Session State ───────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = None
if "repl_tool" not in st.session_state:
    st.session_state.repl_tool = None
if "df" not in st.session_state:
    st.session_state.df = None
if "loaded_filename" not in st.session_state:   # ✅ track which file is currently loaded
    st.session_state.loaded_filename = None

# ─── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.header("📁 Your Dataset")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    # ✅ Only re-initialise when a NEW file is uploaded, not on every rerun
    if uploaded_file and uploaded_file.name != st.session_state.loaded_filename:
        df = pd.read_csv(uploaded_file)
        st.session_state.df = df
        st.session_state.loaded_filename = uploaded_file.name

        agent, repl_tool = create_agent(df)
        st.session_state.agent = agent
        st.session_state.repl_tool = repl_tool

        st.session_state.messages = []           # reset ONLY when a new file is loaded
        st.success(f"Loaded! {df.shape[0]} rows × {df.shape[1]} cols")

    # Always show summary/suggestions if any file is loaded
    if st.session_state.df is not None:
        st.success(
            f"Loaded! {st.session_state.df.shape[0]} rows "
            f"× {st.session_state.df.shape[1]} cols"
        )

        with st.expander("📋 Dataset Summary", expanded=False):
            st.markdown(get_dataset_summary(st.session_state.df))

        with st.expander("💡 Try asking...", expanded=True):
            suggestions = get_suggested_questions(st.session_state.df)
            for q in suggestions:
                if st.button(q, use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": q})
                    st.rerun()

# ─── Main Chat Area ──────────────────────────────────────────────
if st.session_state.df is None:
    st.info("👈 Upload a CSV from the sidebar to get started!")
else:
    # Replay full chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("type") == "chart":
                for b64 in msg.get("charts", []):
                    img_bytes = base64.b64decode(b64)
                    st.image(img_bytes, use_column_width=True)
                if msg.get("explanation"):
                    st.markdown(msg["explanation"])
            else:
                st.markdown(msg["content"])

    if prompt := st.chat_input("Ask anything about your data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = run_query(
                    st.session_state.agent,
                    prompt,
                    repl_tool=st.session_state.repl_tool
                )

            if not result["success"]:
                st.error(result["output"])
                st.session_state.messages.append({
                    "role": "assistant", "content": result["output"]
                })
            else:
                output = result["output"]
                charts = result.get("charts", [])

                if charts:
                    for b64 in charts:
                        img_bytes = base64.b64decode(b64)
                        st.image(img_bytes, use_column_width=True)
                    if output:
                        st.markdown(output)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "type": "chart",
                        "charts": charts,
                        "explanation": output
                    })
                else:
                    st.markdown(output)
                    st.session_state.messages.append({
                        "role": "assistant", "content": output
                    })