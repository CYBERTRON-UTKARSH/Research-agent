# 🚀 AI Research Pipeline: Multi-Agent System

An advanced, production-grade multi-agent research assistant powered by **Modern LangChain**, **LangGraph**, **Flask**, **Groq (Qwen)**, and **Tavily Search**. This system autonomously searches the web, scrapes authoritative sources, drafts comprehensive academic-style reports, critically evaluates them, and refines them into polished markdown deliverables with real-time Server-Sent Events (SSE) streaming updates.

---

## 🏗️ System Architecture

The application follows a modular, decoupled architecture separating the backend orchestration, agent definitions, web tooling, and frontend presentation:

```
┌────────────────────────────────────────────────────────┐
│                        Flask App                       │
│                     (app.py / SSE)                     │
└───────────┬────────────────────────────────┬───────────┘
            │                                │
            ▼                                ▼
┌───────────────────────┐        ┌───────────────────────┐
│   ResearchPipeline    │◄───────┤    Agents & Chains    │
│    (pipeline.py)      │        │     (agents.py)       │
└───────────┬───────────┘        └───────────┬───────────┘
            │                                │
            ▼                                ▼
┌────────────────────────────────────────────────────────┐
│                      Tools Module                      │
│                  (tools.py / Tavily/BS4)               │
└────────────────────────────────────────────────────────┘
```

### Core Components:
1. **Flask Backend (`app.py`)**: Handles HTTP requests, SSE streaming progress logs, report downloads (`.md`), and JSON exports.
2. **Pipeline Orchestrator (`pipeline.py`)**: Manages the 5-stage sequential workflow and state management.
3. **Agent & Chain Definitions (`agents.py`)**: Initializes the Groq LLM (`qwen/qwen3.8-27b`), search agent, reader agent, writer chain, critic chain, and refiner chain using modern LangChain patterns.
4. **Tools Module (`tools.py`)**: Custom `@tool` decorated functions for web search (`tavily-python`) and robust webpage scraping (`BeautifulSoup`).

---

## 🔄 Processing Flow & Workflow

The research pipeline executes a structured 5-step autonomous agentic workflow:

```
[User Input: Topic]
       │
       ▼
 1. 🔍 Search Agent ────► Searches web via Tavily API for top URLs & snippets
       │
       ▼
 2. 📖 Reader Agent ────► Scrapes & extracts clean content from key URLs via BeautifulSoup
       │
       ▼
 3. ✍️ Writer Chain ────► Synthesizes search & scraped data into a 1500-2000 word report
       │
       ▼
 4. 🔍 Critic Chain ────► Evaluates quality, strengths, missing elements & assigns a score
       │
       ▼
 5. 🔧 Refiner Chain ───► Polishes and improves the report based on critic feedback
       │
       ▼
[Final Refined Report & Markdown Export]
```

- **Step 1 (Search Agent)**: Queries Tavily for recent, reliable, and detailed web information.
- **Step 2 (Reader Agent)**: Analyzes search results, picks top resources, and extracts clean main-body text while stripping navigation, footers, and ads.
- **Step 3 (Writer Chain)**: Composes an in-depth academic-style report structured with an Introduction, Key Findings, Analysis, Conclusion, and Sources.
- **Step 4 (Critic Chain)**: Performs rigorous peer review, assigning a score out of 10, highlighting strengths, identifying missing elements, and providing actionable recommendations.
- **Step 5 (Refiner Chain)**: Automatically integrates critic feedback to produce the final, publication-ready research report.

---

## 📂 Project Structure

```text
multi-agent-system/
│
├── app.py              # Flask backend with SSE streaming & REST endpoints
├── pipeline.py         # 5-stage research pipeline orchestrator
├── agents.py           # LangChain/LangGraph agent & chain definitions (Groq/Qwen)
├── tools.py            # Tavily web search & BeautifulSoup scraping tools
├── requirements.txt    # Project dependencies
├── .env                # API keys configuration
├── templates/          # HTML templates for web UI
└── static/             # CSS / JavaScript assets
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.10 or higher
- Groq API Key (`GROQ_API_KEY`)
- Tavily API Key (`TAVILY_API_KEY`)

### 2. Clone and Navigate
```powershell
cd "path/to/multi agent system"
```

### 3. Create & Activate Virtual Environment
```powershell
python -m venv .venv
Set-ExecutionPolicy Bypass -Scope Process; .\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create or update your `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

---

## 🚀 Running the Application

### Web UI Mode (Flask)
Start the server:
```powershell
python app.py
```
Open your browser and navigate to:
```
http://localhost:5000
```
Enter any research topic in the UI to watch the multi-agent pipeline execute live with streaming progress updates, then download your final report as a Markdown file.

### Command Line (CLI) Mode
You can also run the pipeline directly via terminal:
```powershell
python pipeline.py
```
