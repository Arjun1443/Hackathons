# 🚀 FoundersAgent
### Your AI Co-Founder in a Box

FoundersAgent is a Python and Streamlit startup-assistance prototype that brings idea evaluation, market research, business planning, and operational tasks into one interface. Built for hackathon demonstrations and experimentation, it includes two independently runnable applications.

## Application versions

| Entry point | Purpose | Implementation | Report export |
| --- | --- | --- | --- |
| [app.py](app.py) | AI-assisted startup research with nine selectable agents | Groq, LangGraph, LangChain, and optional search APIs | Plain text (`.txt`) |
| [FoundersAgent.py](FoundersAgent.py) | Broader demonstration with 24 agent options across nine categories | Python rules, calculations, templates, and evidence checklists | JSON (`.json`) |

**Start with `FoundersAgent.py` for a demonstration without model credentials. Use `app.py` for Groq-generated responses and optional external research.**

The two files have separate interfaces and execution paths. Selecting an agent runs that agent; the current implementation does not automatically coordinate all agents in a shared workflow.

## What you can do

### AI-assisted application — `app.py`

| Agent | Current behavior |
| --- | --- |
| Idea Evaluation | Combines optional trend, competitor, and market-validation searches with a weighted score and model-generated interpretation |
| Market Research | Retrieves competitor and market evidence before drafting a report, with instructions to cite supplied sources |
| Domain Suggestions | Uses the entered name to produce a registrar search link. Availability remains unverified |
| VC Funding | Calculates a revenue-multiple valuation and generates funding guidance |
| CA & Legal | Produces registration guidance from embedded country information and a model response |
| Tax Filing | Estimates tax using annual inputs, the selected jurisdiction, and a rate entered by the user. Does not file returns |
| Payslip Generator | Uses the entered employee, gross salary, deductions, and payroll month |
| Astrology Support | Generates motivational astrology-themed content |
| CRM Integration | Uses the entered lead information to create a local draft. Does not write to a remote CRM |

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

**Implementation status:** the extended application contains templates and calculations, not 24 model-backed autonomous agents. Idea Scoring returns an evidence checklist instead of a random score. Problem Validation returns interview questions instead of fabricated social findings. Trademark and domain helpers explicitly say searches have not occurred. Resume Screener calculates literal skill coverage from pasted resumes. Static business and legal templates still need review.

Reports and the last 50 local traces survive reruns within the current Streamlit session. No remote Arize, Google Cloud Agent Builder, registrar, CRM, or tax-filing integration is implemented.

## Technology stack

| Component | Technology |
| --- | --- |
| User interface | Streamlit with custom CSS |
| Language | Python |
| AI workflow in `app.py` | LangGraph |
| Model integration in `app.py` | Groq hosted inference through the OpenAI-compatible API, using LangChain `ChatOpenAI` |
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

Use Python 3.11 or newer (Python 3.12 recommended). The regression checks were run on Python 3.12. Top-level dependency versions are pinned in `requirements.txt`.

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

`requirements.txt` includes the Streamlit interface, Groq/LangGraph dependencies, and optional research SDKs. The `google-search-results` distribution provides the `serpapi.GoogleSearch` import. API keys are still needed to use hosted services.

### 4. Choose an application

**Extended demo — no API keys required**

```bash
python -m streamlit run FoundersAgent.py
```

**Groq application**

Create a file named `.env` in the repository root:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
SERPAPI_API_KEY=your_serpapi_api_key
TAVILY_API_KEY=your_tavily_api_key
EXA_API_KEY=your_exa_api_key
```

Replace the placeholders with your own credentials. Optional keys can be omitted.

The provider endpoint is `https://api.groq.com/openai/v1`. Only a Groq API key is required for model calls, even though the compatibility client is named `ChatOpenAI`. An OpenAI API key is not needed. Use a model available to your Groq account. See [Groq models](https://console.groq.com/docs/models) and [API compatibility](https://console.groq.com/docs/openai). Set `GROQ_API_KEY` in your local `.env` or deployment secrets, reinstall `requirements.txt`, and restart Streamlit after updating.

```bash
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually [http://localhost:8501](http://localhost:8501).

## API configuration

| Variable | Required for | Behavior when missing |
| --- | --- | --- |
| `GROQ_API_KEY` | AI requests in both applications | The research app stops without it. Job fields remain manually editable |
| `GROQ_MODEL` | Optional model override | Defaults to `openai/gpt-oss-20b` |
| `SERPAPI_API_KEY` | Google Trends tool in `app.py` | Returns an error indicator. Idea Evaluation refuses to produce a viability score |
| `TAVILY_API_KEY` | Competitor search in `app.py` | Returns an empty competitor list with an error indicator. Idea Evaluation stops scoring |
| `EXA_API_KEY` | Market validation in `app.py` | Returns an empty product list with an error indicator. Idea Evaluation stops scoring |

`FoundersAgent.py` also reads `ARIZE_API_KEY` and `ARIZE_SPACE_KEY`, but its current tracker does not use them to connect to a remote service.

Use your own provider accounts and check their usage limits and charges. Keep credentials out of Git commits, screenshots, and shared reports. Inputs sent through `app.py` may be transmitted to Groq and the configured search providers.

## How to use

### Research a startup idea

1. Launch `app.py` and select **Idea Evaluation**.
2. Enter a specific startup idea, such as:
   > An AI learning assistant for engineering students that answers questions from course materials and helps trainers identify learning gaps.
3. Click **Analyze Now**.
4. Review the generated analysis, score, and any available research results.
5. Use **Download Report** to save the text output.

For **VC Funding** or **Tax Filing**, supply annual financial inputs. Tax estimates also require an assumed rate and country. Payroll, CRM, and domain suggestions have dedicated input fields. For **CA & Legal**, select a country and enter a city.

Each run starts with a new workflow state. Running Idea Evaluation first does not automatically pass its score into another agent.

### Explore the extended demo

1. Launch `FoundersAgent.py`.
2. Choose a category and an agent.
3. Complete the displayed inputs.
4. Click **Execute**.
5. Review the result and trace details, then download the JSON report.

For Resume Screener, enter comma-separated required skills and paste each candidate name on its own first line followed by resume text. Separate candidates with a line containing `---`. The result measures skill keyword coverage only, not suitability or verified experience.

For Productivity Coach, enter 0.25–12 hours and separate priorities with commas or newlines. For Payslip, enter gross salary and total deductions explicitly. Content Marketing returns the chosen template type, including a case-study outline. MVP Builder includes the features entered by the user.

### Job posting with salary

In **HR & People → Job Posting**, enter a minimum and maximum salary, currency, and pay period (year, month, or hour). Draft role responsibilities, required skills and experience, and benefits with the **Draft … with AI** buttons, or enter them manually. Every field remains editable. The application email/careers URL field has been removed. Choose LinkedIn, Naukri, and/or Indeed, then execute the helper.

AI drafting uses the existing `GROQ_API_KEY` from `.env` or deployment secrets and the `openai/gpt-oss-20b` model. It runs only when a draft button is clicked, uses the entered job context and current text, and replaces only the chosen section. Missing credentials or request failures leave the existing text intact. Manual editing and the rest of the extended application do not require a key. Review benefits suggestions before offering them to candidates.

The result provides a copyable description, a text download, and buttons to open the selected platform's official employer posting page. Sign in to the employer account, paste the draft, complete any remaining fields, and publish there. These buttons do not prefill or submit forms, purchase listings, or report publication success. A salary range of zero or a minimum above the maximum is rejected.

Automatic publishing is not connected. LinkedIn job-publishing APIs require approved access, and Indeed uses partner integration credentials. A Naukri employer integration would also need a supported posting method and authorized account access. Never paste account passwords into the source code.

References: [LinkedIn job API access](https://learn.microsoft.com/en-us/linkedin/talent/job-postings/api/overview), [Indeed Job Sync API](https://docs.indeed.com/job-sync-api/), [Naukri employer posting](https://www.naukri.com/recruit/job-posting).

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
| Market trend | 30% | Numeric timeline values from the trend provider |
| Competition | 25% | Rule-based score from the number of competitor search results |
| Market validation | 25% | Rule-based score from the number of similar-product results |
| Innovation | 20% | Model assessment clamped to 0–100, with fallback 65 if parsing fails |

Idea Evaluation reports insufficient evidence instead of scoring when a research tool returns an error. A successful empty search is still different from proof of no competition. Search-result counts and model innovation assessments remain rough heuristics, not validated predictions of startup success.

## Repository structure

| File | Purpose |
| --- | --- |
| [app.py](app.py) | Nine-agent Groq application, tool definitions, workflow state, and Streamlit interface |
| [FoundersAgent.py](FoundersAgent.py) | Independent 24-option demonstration application and local trace tracker |
| [prompts.yaml](prompts.yaml) | Additional code-agent prompt templates; neither application currently loads this file |
| [requirements.txt](requirements.txt) | Pinned top-level dependencies for both applications |
| [test_agents.py](test_agents.py) | Offline logic regressions and a smoke check of all 24 helpers |
| [test_ui.py](test_ui.py) | Streamlit interaction and report-persistence regressions |

## Current limitations

- **External actions are demonstrations:** domain availability is not checked against a live registrar in `app.py`, CRM records are returned without a persistent CRM connection, and tax calculations do not submit filings.
- **Payroll drafts:** both applications use the supplied gross salary and deductions. They do not determine statutory payroll deductions automatically.
- **Simplified finance and legal logic:** registration guidance remains embedded and can become outdated. Tax estimates use a user-supplied rate and selected country. They do not implement jurisdiction-specific law.
- **No persistent workspace:** there is no database-backed chat history, user account system, or shared cross-agent memory. Reports and local traces persist only within the browser session and can disappear when the session ends or the server restarts.
- **No guaranteed research accuracy:** model responses can contain unsupported claims, and optional search tools may return empty or default results.
- **No automated MVP delivery:** the MVP Builder option provides planning output rather than deploying a complete application.
- **No benchmark claims:** the repository does not establish measured accuracy, latency, or production reliability.

Verify business research against original sources and review generated financial and legal material with qualified professionals before using it for decisions. Astrology content is for entertainment.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `ModuleNotFoundError: langgraph`, `langchain_openai`, or `langchain_core` | Activate the virtual environment and install `requirements.txt` |
| Missing Groq key message | Place `.env` beside `app.py`, set `GROQ_API_KEY`, and restart Streamlit |
| Empty competitor or market results | Check the relevant optional key, SDK installation, provider quota, and returned error details |
| Idea Evaluation reports insufficient evidence | Configure the missing research providers and retry. The application deliberately avoids scoring provider failures |
| Provider authentication or quota error | Check account access, key validity, usage limits, and billing with that provider |
| Port 8501 is occupied | Run with `--server.port 8502` and open the URL Streamlit prints |
| Idea Scoring returns no numeric score | The extended helper requires research evidence before a meaningful score can be produced |
| Report history disappears after server restart | Session state is not a database. Persistent storage remains a roadmap item |

## Development roadmap

Potential improvements for future development:

- Replace simulated outputs with verified data sources.
- Add persistent storage for reports, trace history, and shared agent state.
- Connect real registrar, CRM, payroll, and observability services.
- Introduce coordinated workflows with explicit handoffs between agents.
- Validate structured model outputs and add provider retries and clearer failure handling.
- Support additional document export formats.

These are proposed improvements, not features already implemented.

## Verification

Run the offline logic regressions:

```bash
python -m unittest -v test_agents.py
```

After installing requirements, run the Streamlit interaction regressions:

```bash
python -m unittest -v test_ui.py
```

The tests exercise all 24 extended helpers and critical research-app flows without live API calls. They do not establish production readiness or validate provider credentials, external search quality, or hosted model accuracy.

## Contributing

Open an issue describing the problem or proposed improvement before making substantial changes. For a pull request, explain the behavior changed, include setup or configuration updates where needed, and describe how you verified it. Never include API credentials or private customer data.

## License

No license file is currently included in the repository root. Add an explicit license before distributing the project under open-source terms.

