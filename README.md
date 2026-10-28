# FoundersAgent — Startup Research Prototype

A Streamlit application exploring startup-idea research through LangGraph orchestration, a DeepSeek model, and optional search integrations.

## Why this project matters

An agent workflow can organize several research steps behind one interface. This prototype illustrates how model calls, external tools, state, and structured outputs can be connected.

## Technical focus

Python · Streamlit · LangGraph · LangChain · DeepSeek · external search tools

## Run locally

```bash
git clone https://github.com/Arjun1443/Hackathons.git
cd Hackathons
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Configure credentials in a local `.env` file:

```dotenv
DEEPSEEK_API_KEY=
SERPAPI_API_KEY=
TAVILY_API_KEY=
EXA_API_KEY=
```

The app stops when `DEEPSEEK_API_KEY` is missing. The other keys enable associated external tools; missing services can produce empty results or default values.

## Source guide

- `app.py`: Streamlit application and tool definitions
- `FoundersAgent.py`: additional agent implementation
- `prompts.yaml`: prompt material
- `requirements.txt`: dependencies

## Interpreting results

Startup scores are heuristics, not validated forecasts. In the inspected scoring function, innovation is assigned a fixed value and missing search data can lead to defaults. Inspect sources and tool errors before interpreting a score. This is a research prototype, not financial, legal, or business advice.
