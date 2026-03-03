# 📊 ChartTalk

Chat with your CSV data in plain English. Ask questions, get instant answers, and generate charts — no SQL or coding required.

Built with **Streamlit**, **LangChain**, and **Groq (Llama 3.3 70B)**.

---

## ✨ Features

- Upload any CSV file and start chatting instantly
- Ask data questions in plain English — get real answers
- Generate histograms, bar charts, and more on demand
- Dataset summary and suggested questions auto-generated on upload

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/charttalk.git
cd charttalk
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your API key
Create a `.env` file in the root folder:
```
GROQ_API_KEY=your_groq_api_key_here
```
Get your free API key at [console.groq.com](https://console.groq.com)

### 4. Run the app
```bash
streamlit run app.py
```

---

## 🛠 Tech Stack

| Layer | Tool |
|---|---|
| Frontend | Streamlit |
| Agent Framework | LangChain |
| LLM | Llama 3.3 70B via Groq |
| Data | Pandas |
| Charts | Matplotlib, Seaborn |

---

## 📁 Project Structure

```
charttalk/
├── app.py            # Streamlit UI
├── agent.py          # LangChain agent + chart capture logic
├── utils.py          # Dataset summary + question suggestions
├── requirements.txt
└── .env              # Your API key (never committed)
```