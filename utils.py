import pandas as pd
import io

def get_dataset_summary(df: pd.DataFrame) -> str:
    summary = f"""
**Shape:** {df.shape[0]} rows × {df.shape[1]} columns

**Columns & Types:**
{df.dtypes.to_string()}

**Missing Values:**
{df.isnull().sum()[df.isnull().sum() > 0].to_string() or "None "}

**Numeric Summary:**
{df.describe().round(2).to_string()}
"""
    return summary


def get_suggested_questions(df: pd.DataFrame) -> list[str]:
    questions = []
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include="object").columns.tolist()

    if len(num_cols) >= 2:
        questions.append(f"What is the correlation between {num_cols[0]} and {num_cols[1]}?")
        questions.append(f"Show the distribution of {num_cols[0]} as a histogram")
    if num_cols:
        questions.append(f"Are there any outliers in {num_cols[0]}?")
    if cat_cols and num_cols:
        questions.append(f"What is the average {num_cols[0]} grouped by {cat_cols[0]}?")
    if cat_cols:
        questions.append(f"What are the top 5 values in {cat_cols[0]}?")

    questions.append("Give me a quick summary of this dataset")
    return questions