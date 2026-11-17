# 🚀 FoundersAgent
### Your AI Co-Founder in a Box

FoundersAgent is a Python and Streamlit startup-assistance prototype that brings idea evaluation, market research, business planning, and operational tasks into one interface. Built for hackathon demonstrations and experimentation, it includes two independently runnable applications.

## Application versions

| Entry point | Purpose | Implementation | Report export |
| --- | --- | --- | --- |
| [app.py](app.py) | AI-assisted startup research with nine selectable agents | DeepSeek, LangGraph, LangChain, and optional search APIs | Plain text (`.txt`) |
| [FoundersAgent.py](FoundersAgent.py) | Broader demonstration with 24 agent options across nine categories | Python rules, calculations, templates, and simulated outputs | JSON (`.json`) |

**Start with `FoundersAgent.py` for a demonstration without model credentials. Use `app.py` for DeepSeek-generated responses and optional external research.**

The two files have separate interfaces and execution paths. Selecting an agent runs that agent; the current implementation does not automatically coordinate all agents in a shared workflow.

## What you can do

### AI-assisted application — `app.py`

| Agent | Current behavior |
| --- | --- |
| Idea Evaluation | Combines optional trend, competitor, and market-validation searches with a weighted score and model-generated interpretation |
| Market Research | Produces model-generated startup research |
| Domain Purchase | Suggests a name and returns a demonstration availability result |
| VC Funding | Calculates a revenue-multiple valuation and generates funding guidance |
| CA & Legal | Produces registration guidance from embedded country information and a model response |
| Tax Filing | Calculates a simplified tax estimate and explains it |
| Payslip Generator | Produces sample payroll data and an accompanying email draft |
| Astrology Support | Generates motivational astrology-themed content |
| CRM Integration | Returns a sample lead record and suggested next steps |

The interface provides agent selection cards, a startup description field, financial or location inputs where applicable, credential-status indicators, and downloadable text reports.

### Extended demonstration — `FoundersAgent.py`

| Category | Available agents |
| --- | --- |
| Idea & Validation | Idea Generator, Idea Scoring, Problem Validation, Business Model |
| Legal & Registration | Domain Purchase, Company Registration, Legal Compliance, Trademark |
| Finance & Accounting | Tax Filing, CFO Analysis, Invoice Generator |
| HR & People | Job Posting, Resume Screener, Payslip, Employee Onboarding |
| Sales & CRM | CRM, Sales Outreach |
| Marketing | Content Marketing, Social Media |
| Funding | VC Pitch, Valuation |
| Product & Dev | MVP Builder |
| Personal Assistant | Astrology, Productivity Coach |

This version includes category selection, task-specific forms, structured results, invoice and payslip HTML previews, JSON downloads, and an in-memory trace viewer.

**Implementation status:** many outputs use embedded examples, templates, or random values. For example, idea scores and TAM/SAM/SOM estimates in this version are simulated. Its `ArizeTracker` stores traces locally in memory; it does not send telemetry to Arize. Although the source labels mention Google Cloud Agent Builder and Arize MCP, this file does not implement those external integrations.

## Technology stack

| Component | Technology |
| --- | --- |
| User interface | Streamlit with custom CSS |
| Language | Python |
| AI workflow in `app.py` | LangGraph |
| Model integration in `app.py` | LangChain DeepSeek integration, model ID `deepseek-chat` |
| Optional trend research | SerpAPI Google Trends |
| Optional competitor search | Tavily |
| Optional market validation | Exa |
| Environment configuration | python-dotenv |
| Output formats | Text and JSON; HTML previews in the extended demo |

Model inference for `app.py` uses a hosted API. It does not require downloading model weights or running a local GPU.

## Quick start

### 1. Clone the repository

Install Python and Git, then run:

```bash
git clone https://github.com/Arjun1443/Hackathons.git
cd Hackathons
python -m venv .venv
```

Python 3.10 or newer is a reasonable starting point; the repository does not currently pin a tested Python or dependency version.

### 2. Activate the virtual environment

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows Command Prompt**

```bat
.venv\Scripts\activate.bat
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The current `requirements.txt` contains only `streamlit` and `python-dotenv`. These cover the extended demo's third-party imports.

**For the DeepSeek application, install its additional dependencies:**

```bash
python -m pip install langgraph langchain-deepseek langchain-core
```

**For optional external research tools:**

```bash
python -m pip install google-search-results tavily-python exa-py
```

The `google-search-results` package supplies the `serpapi.GoogleSearch` import used in this project. Dependency versions are unpinned, so provider SDK changes may require code adjustments.

### 4. Choose an application

**Extended demo — no API keys required**

```bash
python -m streamlit run FoundersAgent.py
```

**DeepSeek application**

Create a file named `.env` in the repository root:

```dotenv
DEEPSEEK_API_KEY=your_deepseek_api_key
SERPAPI_API_KEY=your_serpapi_api_key
TAVILY_API_KEY=your_tavily_api_key
EXA_API_KEY=your_exa_api_key
```

Replace the placeholders with your own credentials. Optional keys can be omitted.

```bash
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually [http://localhost:8501](http://localhost:8501).

## API configuration

| Variable | Required for | Behavior when missing |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | All of `app.py` | The application stops with a configuration message |
| `SERPAPI_API_KEY` | Google Trends tool in `app.py` | Returns a default trend score of 50 with an error indicator |
| `TAVILY_API_KEY` | Competitor search in `app.py` | Returns an empty competitor list with an error indicator |
| `EXA_API_KEY` | Market validation in `app.py` | Returns an empty product list with an error indicator |

`FoundersAgent.py` also reads `ARIZE_API_KEY` and `ARIZE_SPACE_KEY`, but its current tracker does not use them to connect to a remote service.

Use your own provider accounts and check their usage limits and charges. Keep credentials out of Git commits, screenshots, and shared reports. Inputs sent through `app.py` may be transmitted to DeepSeek and the configured search providers.

## How to use

### Research a startup idea

1. Launch `app.py` and select **Idea Evaluation**.
2. Enter a specific startup idea, such as:
   > An AI learning assistant for engineering students that answers questions from course materials and helps trainers identify learning gaps.
3. Click **Analyze Now**.
4. Review the generated analysis, score, and any available research results.
5. Use **Download Report** to save the text output.

For **VC Funding** or **Tax Filing**, supply the financial inputs shown in the form. For **CA & Legal**, select a country and enter a city.

Each run starts with a new workflow state. Running Idea Evaluation first does not automatically pass its score into another agent.

### Explore the extended demo

1. Launch `FoundersAgent.py`.
2. Choose a category and an agent.
3. Complete the displayed inputs.
4. Click **Execute**.
5. Review the result and trace details, then download the JSON report.

Treat example market figures, screening results, and generated scores as demonstration data.

## Idea scoring in `app.py`

The Idea Evaluation tool calculates:

```text
Final score = (trend score × 0.30)
            + (competition score × 0.25)
            + (market-validation score × 0.25)
            + (innovation score × 0.20)
```

| Component | Weight | Current basis |
| --- | --- | --- |
| Market trend | 30% | Trend-tool output, with a default of 50 when unavailable |
| Competition | 25% | Rule-based score from the number of competitor search results |
| Market validation | 25% | Rule-based score from the number of similar-product results |
| Innovation | 20% | Fixed value of 65 |

A score can still be produced when research services are missing or fail. Search-result counts are rough proxies, and the innovation component is fixed. These scores are exploratory heuristics rather than validated predictions of startup success.

## Repository structure

| File | Purpose |
| --- | --- |
| [app.py](app.py) | Nine-agent DeepSeek application, tool definitions, workflow state, and Streamlit interface |
| [FoundersAgent.py](FoundersAgent.py) | Independent 24-option demonstration application and local trace tracker |
| [prompts.yaml](prompts.yaml) | Additional code-agent prompt templates; neither application currently loads this file |
| [requirements.txt](requirements.txt) | Minimal dependencies for the extended demo |

## Current limitations

- **External actions are demonstrations:** domain availability is not checked against a live registrar in `app.py`, CRM records are returned without a persistent CRM connection, and tax calculations do not submit filings.
- **Sample payroll inputs:** `app.py` uses a hardcoded employee and salary in its payslip agent, even though the interface displays financial inputs.
- **Simplified finance and legal logic:** registration information and tax rules are embedded in the source and may become outdated. The tax agent in `app.py` currently uses the USA jurisdiction.
- **No persistent workspace:** there is no database-backed chat history, user account system, or shared cross-agent memory. The extended demo's trace list is created in memory and can reset on Streamlit reruns.
- **No guaranteed research accuracy:** model responses can contain unsupported claims, and optional search tools may return empty or default results.
- **No automated MVP delivery:** the MVP Builder option provides planning output rather than deploying a complete application.
- **No benchmark claims:** the repository does not establish measured accuracy, latency, or production reliability.

Verify business research against original sources and review generated financial and legal material with qualified professionals before using it for decisions. Astrology content is for entertainment.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `ModuleNotFoundError: langgraph`, `langchain_deepseek`, or `langchain_core` | Activate the virtual environment and install the additional AI dependencies above |
| Missing DeepSeek key message | Place `.env` beside `app.py`, set `DEEPSEEK_API_KEY`, and restart Streamlit |
| Empty competitor or market results | Check the relevant optional key, SDK installation, provider quota, and returned error details |
| A score appears without configured search providers | Default values are being used; the score does not establish that live research succeeded |
| Provider authentication or quota error | Check account access, key validity, usage limits, and billing with that provider |
| Port 8501 is occupied | Run with `--server.port 8502` and open the URL Streamlit prints |
| Different results in the extended demo | Some results intentionally use random values |
| Trace history disappears after interaction | The current tracker is recreated during script execution and has no persistent backend |

## Development roadmap

Potential improvements for future development:

- Pin and complete dependency requirements.
- Replace simulated outputs with verified data sources.
- Add persistent storage for reports, trace history, and shared agent state.
- Connect real registrar, CRM, payroll, and observability services.
- Introduce coordinated workflows with explicit handoffs between agents.
- Validate structured model outputs and add provider retries and clearer failure handling.
- Add meaningful tests for scoring, financial calculations, and workflow behavior.
- Support additional document export formats.

These are proposed improvements, not features already implemented.

## Contributing

Open an issue describing the problem or proposed improvement before making substantial changes. For a pull request, explain the behavior changed, include setup or configuration updates where needed, and describe how you verified it. Never include API credentials or private customer data.

## License

No license file is currently included in the repository root. Add an explicit license before distributing the project under open-source terms.
