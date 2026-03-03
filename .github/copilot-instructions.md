# ChartTalk – Copilot Instructions

## Project Overview

ChartTalk is a Streamlit chat app that lets users upload a CSV and ask natural-language questions about their data (including chart generation). It uses a LangChain pandas-dataframe agent backed by Groq's Llama 3 70B model.

## Architecture (3 files)

- **`app.py`** – Streamlit UI: sidebar CSV upload, chat message loop, chart rendering. Orchestrates the other modules.
- **`agent.py`** – Builds the LangChain `create_pandas_dataframe_agent` with `ChatGroq` LLM and a custom `CHART_SUFFIX` prompt. Exposes `create_agent(df)` and `run_query(agent, question)`.
- **`utils.py`** – Pure helper functions (`get_dataset_summary`, `get_suggested_questions`) that inspect DataFrame metadata to generate markdown summaries and starter questions.

### Data Flow

1. User uploads CSV → `pd.read_csv` → stored in `st.session_state.df`
2. `create_agent(df)` builds a LangChain agent → stored in `st.session_state.agent`
3. User sends a chat message → `run_query(agent, question)` → returns `{"success": bool, "output": str}`
4. `app.py` checks output for chart markers via regex, executes chart code with `exec()`, renders with `st.pyplot()`

## Chart Generation Convention

The LLM is prompted (via `CHART_SUFFIX` in `agent.py`) to wrap matplotlib code in marker comments:

```python
# CHART_START
<matplotlib code here, store figure as `fig`>
# CHART_END
```

`app.py` extracts this block with `re.search(r"# CHART_START(.*?)# CHART_END", ...)`, runs it via `exec()` with `df`, `plt`, `pd`, and `sns` pre-injected in scope (do **not** import them inside the block), then renders `fig`. **Never call `plt.show()`** in generated chart code—Streamlit handles display. The `CHART_SUFFIX` prompt also instructs the LLM to run `df.columns.tolist()` before writing chart code to avoid hallucinated column names.

## Key Conventions

- **Streamlit session state keys**: `messages` (chat history list), `agent` (LangChain agent), `df` (pandas DataFrame). Always use these exact keys.
- **LLM provider**: Groq via `langchain_groq.ChatGroq`, model `llama-3.3-70b-versatile`, temperature `0`. API key loaded from `.env` as `GROQ_API_KEY`.
- **Agent type**: string `"openai-functions"` passed to `agent_type=` (LangChain 0.2+ removed the `AgentType` enum; do **not** import `AgentType` from `langchain.agents`), with `allow_dangerous_code=True` and `handle_parsing_errors=True`.
- **Matplotlib backend**: Set to `"Agg"` (non-interactive) in `app.py` — required for Streamlit.
- **Error handling pattern**: `run_query` catches all exceptions and returns a `success`/`output` dict; `app.py` shows errors via `st.error()`.

## Running the App

```
# Activate venv, then:
streamlit run app.py
```

Requires a `.env` file with `GROQ_API_KEY=<your-key>`.

## Known Issues

- No `requirements.txt` or `pyproject.toml` exists. Core deps: `streamlit`, `pandas`, `matplotlib`, `langchain`, `langchain-groq`, `langchain-experimental`, `python-dotenv`.
