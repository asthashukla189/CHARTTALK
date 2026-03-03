import io
import re
import base64

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from langchain_groq import ChatGroq
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_experimental.tools import PythonAstREPLTool
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Custom REPL tool that captures any matplotlib figures produced by the agent
# ---------------------------------------------------------------------------

class ChartCapturingREPL(PythonAstREPLTool):
    captured_figures: list = []

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str) -> str:
        plt.close("all")
        result = super()._run(query)
        self._harvest_figures()
        return result

    async def _arun(self, query: str) -> str:
        plt.close("all")
        result = await super()._arun(query)
        self._harvest_figures()
        return result

    def _harvest_figures(self):
        for num in plt.get_fignums():
            fig = plt.figure(num)
            if fig not in self.captured_figures:
                self.captured_figures.append(fig)

    def pop_figures_as_base64(self) -> list[str]:
        images = []
        for fig in self.captured_figures:
            buf = io.BytesIO()
            try:
                fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
                buf.seek(0)
                images.append(base64.b64encode(buf.read()).decode("utf-8"))
            except Exception as e:
                print(f"[ChartTalker] Could not encode figure: {e}")
            finally:
                plt.close(fig)
        self.captured_figures.clear()
        return images


# ---------------------------------------------------------------------------
# Agent prompt
# ---------------------------------------------------------------------------

AGENT_PREFIX = """
You are a data analysis assistant. You have access to a pandas DataFrame called `df`.

CRITICAL RULES:
- ALWAYS call the python_repl_ast tool immediately to compute the answer.
- NEVER say "I will need to..." — just run the code and return the result.
- For any question about the data (column count, shape, statistics, etc.), run Python code NOW.
- You MUST end every response with:
  Final Answer: <your answer here>

CHART RULES (whenever the user asks for any chart, plot, or visualisation):
1. First run: print(df.columns.tolist()) to confirm exact column names.
2. Use ONLY column names that exist in df.
3. Create the figure like this:

   fig, ax = plt.subplots(figsize=(10, 6))
   # ... your plot code using ax ...
   plt.tight_layout()

4. Do NOT call plt.show() or plt.savefig() — the system captures fig automatically.
5. `df`, `plt`, `pd`, and `sns` are already available — do NOT import them.
6. After creating the chart, end with:
   Final Answer: Here is the chart you requested.
"""

# ---------------------------------------------------------------------------
# Llama output fix — extract answer from malformed "I now know" responses
# ---------------------------------------------------------------------------

def _rescue_llama_output(text: str) -> str:
    """
    Llama sometimes outputs 'I now know the final answer\n<actual answer>'
    instead of 'Final Answer: <actual answer>'.
    This extracts the real content so it isn't swallowed by the parser.
    """
    patterns = [
        r"I now know the final answer[.\n]*(.+)",
        r"Final Answer\s*:\s*(.+)",
        r"The answer is[:\s]+(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return text  # fallback: return as-is


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_agent(df: pd.DataFrame):
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
    )

    repl_tool = ChartCapturingREPL(
        locals={
            "df":  df,
            "pd":  pd,
            "plt": plt,
            "sns": sns,
        }
    )

    agent = create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        agent_type="zero-shot-react-description",
        extra_tools=[repl_tool],
        verbose=True,
        allow_dangerous_code=True,
        prefix=AGENT_PREFIX,
        handle_parsing_errors=True,
        max_iterations=15,
        early_stopping_method="generate",
    )
    return agent, repl_tool


def run_query(agent, question: str, repl_tool: ChartCapturingREPL = None) -> dict:
    try:
        response = agent.invoke({"input": question})
        output = response.get("output", str(response))

        # ✅ Rescue Llama's non-standard "I now know the final answer" phrasing
        if "now know the final answer" in output.lower() or output.strip().startswith("`"):
            output = _rescue_llama_output(output)

        charts = []
        if repl_tool is not None:
            charts = repl_tool.pop_figures_as_base64()

        return {"success": True, "output": output, "charts": charts}

    except Exception as e:
        error_text = str(e)

        # ✅ LangChain wraps parsing failures in the exception message —
        #    try to pull the real answer out of it before giving up.
        rescued = _rescue_llama_output(error_text)
        charts = []
        if repl_tool is not None:
            charts = repl_tool.pop_figures_as_base64()

        if rescued != error_text:
            # We successfully extracted something useful
            return {"success": True, "output": rescued, "charts": charts}

        return {"success": False, "output": f"Error: {error_text}", "charts": charts}