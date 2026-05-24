import streamlit as st
import os
import re
from typing import TypedDict, List, Annotated
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
import json
from datetime import datetime

load_dotenv()

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="FoundersAgent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .main-title {
        text-align: center;
        background: linear-gradient(135deg, #1A365D 0%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
    }
    .agent-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 0.5rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid #334155;
        text-align: center;
    }
    .agent-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px -5px rgba(124, 58, 237, 0.3);
        border-color: #7C3AED;
    }
    .agent-card.selected {
        border: 2px solid #7C3AED;
        box-shadow: 0 0 20px rgba(124, 58, 237, 0.3);
    }
    .agent-icon {
        font-size: 2.5rem;
    }
    .agent-name {
        font-size: 1rem;
        font-weight: bold;
        margin-top: 0.5rem;
        color: #e2e8f0;
    }
    .agent-desc {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 0.3rem;
    }
    .score-card {
        background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%);
        border-radius: 1rem;
        padding: 1rem;
        text-align: center;
    }
    .score-number {
        font-size: 2rem;
        font-weight: bold;
        color: white;
    }
    .report-container {
        background: #0f172a;
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid #334155;
        margin-top: 1rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        font-weight: bold;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
    }
</style>
""", unsafe_allow_html=True)

# ==================== CONFIGURATION ====================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")

if not DEEPSEEK_API_KEY:
    st.error("❌ Please set DEEPSEEK_API_KEY in your .env file")
    st.stop()

# ==================== TOOL DEFINITIONS (Copy all your @tool functions here) ====================
# [PASTE ALL YOUR @tool FUNCTIONS HERE - google_trends_tool, competitor_search_tool, 
#  market_validation_tool, idea_scorer_tool, get_country_regulation_info,
#  calculate_tax_liability, generate_payslip, check_domain_availability, 
#  add_to_crm, calculate_vc_valuation]

# ==================== TOOL 1: GOOGLE TRENDS (SerpAPI) ====================

@tool
def google_trends_tool(startup_idea: str) -> str:
    """
    Get Google Trends data for a startup idea.
    Returns trend score (0-100) and related queries.
    """
    if not SERPAPI_API_KEY:
        return json.dumps({
            "trend_score": 50,
            "trend_data": "SerpAPI key not configured",
            "error": "SERPAPI_API_KEY not set"
        })
    
    try:
        from serpapi import GoogleSearch
        
        keywords = startup_idea[:100].split()[:5]
        query = " ".join(keywords)
        
        params = {
            "api_key": SERPAPI_API_KEY,
            "engine": "google_trends",
            "q": query,
            "data_type": "TIMESERIES"
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        interest_over_time = results.get("interest_over_time", {})
        timeline_data = interest_over_time.get("timeline_data", [])
        
        if timeline_data:
            scores = [point.get("value", [{}])[0].get("value", 0) for point in timeline_data if point.get("value")]
            avg_score = sum(scores) / len(scores) if scores else 50
        else:
            avg_score = 50
        
        return json.dumps({
            "trend_score": int(avg_score),
            "query": query,
            "data_points": len(timeline_data),
            "source": "Google Trends via SerpAPI"
        })
    except Exception as e:
        return json.dumps({
            "trend_score": 50,
            "error": str(e),
            "note": "Using default score"
        })

# ==================== TOOL 2: COMPETITOR SEARCH (Tavily) ====================

@tool
def competitor_search_tool(startup_idea: str) -> str:
    """
    Search for competitors using Tavily API.
    Returns list of competitors with descriptions.
    """
    if not TAVILY_API_KEY:
        return json.dumps({
            "competitors": [],
            "error": "TAVILY_API_KEY not set",
            "note": "Get key from https://tavily.com"
        })
    
    try:
        from tavily import TavilyClient
        
        client = TavilyClient(api_key=TAVILY_API_KEY)
        
        search_query = f"top competitors for {startup_idea[:150]} startup company"
        response = client.search(
            query=search_query,
            search_depth="advanced",
            max_results=8,
            include_answer=True
        )
        
        competitors = []
        for result in response.get('results', []):
            competitors.append({
                "name": result.get('title', 'Unknown')[:50],
                "description": result.get('content', '')[:200],
                "url": result.get('url', ''),
                "relevance": result.get('score', 0)
            })
        
        return json.dumps({
            "competitors": competitors,
            "summary": response.get('answer', '')[:500],
            "total_found": len(competitors),
            "source": "Tavily API"
        })
    except Exception as e:
        return json.dumps({
            "competitors": [],
            "error": str(e)
        })

# ==================== TOOL 3: MARKET VALIDATION (Exa AI) ====================

@tool
def market_validation_tool(startup_idea: str) -> str:
    """
    Search for similar products and market trends using Exa AI.
    Returns traction signals and market interest.
    """
    if not EXA_API_KEY:
        return json.dumps({
            "similar_products": [],
            "error": "EXA_API_KEY not set",
            "note": "Get key from https://exa.ai"
        })
    
    try:
        from exa_py import Exa
        
        exa = Exa(api_key=EXA_API_KEY)
        
        results = exa.search(
            f"startup product similar to {startup_idea[:100]} launch funding",
            type="auto",
            num_results=6,
            contents={"highlights": True}
        )
        
        similar_products = []
        for result in results.results:
            similar_products.append({
                "title": result.title[:100] if result.title else "Unknown",
                "url": result.url if result.url else "",
                "highlights": result.highlights[:200] if hasattr(result, 'highlights') and result.highlights else ""
            })
        
        trends = exa.search(
            f"{startup_idea[:80]} market trends 2025 2026",
            type="auto",
            num_results=4,
            contents={"highlights": True}
        )
        
        market_trends = []
        for t in trends.results[:3]:
            market_trends.append({
                "title": t.title[:100] if t.title else "Unknown",
                "url": t.url if t.url else ""
            })
        
        return json.dumps({
            "similar_products": similar_products,
            "market_trends": market_trends,
            "similar_count": len(similar_products),
            "source": "Exa AI"
        })
    except Exception as e:
        return json.dumps({
            "similar_products": [],
            "error": str(e)
        })

# ==================== TOOL 4: IDEA SCORER (Combines all data) ====================

@tool
def idea_scorer_tool(
    startup_idea: str,
    trend_score: int,
    competitors: list,
    market_validation: dict
) -> str:
    """
    Calculate final startup score (0-100) combining all data sources.
    Weighted by: Market Trend (30%), Competition (25%), Validation (25%), Innovation (20%)
    """
    trend_weighted = trend_score * 0.30
    
    num_competitors = len(competitors) if isinstance(competitors, list) else 0
    if num_competitors == 0:
        competition_score = 60
    elif num_competitors <= 3:
        competition_score = 80
    elif num_competitors <= 6:
        competition_score = 60
    elif num_competitors <= 10:
        competition_score = 40
    else:
        competition_score = 25
    competition_weighted = competition_score * 0.25
    
    similar_count = market_validation.get('similar_count', 0) if isinstance(market_validation, dict) else 0
    if similar_count == 0:
        validation_score = 50
    elif similar_count <= 2:
        validation_score = 75
    elif similar_count <= 5:
        validation_score = 60
    else:
        validation_score = 40
    validation_weighted = validation_score * 0.25
    
    innovation_score = 65
    innovation_weighted = innovation_score * 0.20
    
    final_score = trend_weighted + competition_weighted + validation_weighted + innovation_weighted
    
    if final_score >= 75:
        recommendation = "HIGH POTENTIAL - Strong market signals, proceed with MVP"
        urgency = "Move quickly to capture market opportunity"
    elif final_score >= 55:
        recommendation = "MEDIUM POTENTIAL - Refine positioning and validate further"
        urgency = "Conduct customer discovery interviews"
    elif final_score >= 35:
        recommendation = "LOW POTENTIAL - Significant pivot or repositioning needed"
        urgency = "Re-evaluate problem-solution fit"
    else:
        recommendation = "UNFAVORABLE - Consider different direction or market"
        urgency = "Pivot or explore adjacent markets"
    
    return json.dumps({
        "final_score": round(final_score, 1),
        "breakdown": {
            "market_trend": round(trend_weighted, 1),
            "competition": round(competition_weighted, 1),
            "market_validation": round(validation_weighted, 1),
            "innovation": round(innovation_weighted, 1)
        },
        "raw_scores": {
            "trend_score": trend_score,
            "competition_score": competition_score,
            "validation_score": validation_score,
            "innovation_score": innovation_score
        },
        "recommendation": recommendation,
        "urgency": urgency,
        "weights": {
            "market_trend": "30%",
            "competition": "25%",
            "market_validation": "25%",
            "innovation": "20%"
        }
    })

# ==================== TOOL 5: COUNTRY REGULATION INFO (For CA Agent) ====================

@tool
def get_country_regulation_info(country: str, city: str = None) -> str:
    """
    Get company registration information, government policies, and legal requirements for a specific country.
    """
    country_data = {
        "india": {
            "company_registration": {
                "types": ["Private Limited Company", "LLP", "One Person Company"],
                "recommended": "Private Limited Company (recommended for startups)",
                "process": "Register through MCA (Ministry of Corporate Affairs) portal",
                "website": "https://www.mca.gov.in",
                "steps": [
                    "Obtain Digital Signature Certificate (DSC)",
                    "Apply for Director Identification Number (DIN)",
                    "Name reservation through RUN or SPICe+ form",
                    "File SPICe+ form (INC-32) for incorporation",
                    "Apply for PAN and TAN",
                    "Open bank account"
                ],
                "fee": {
                    "private_limited": "₹7,000 - ₹15,000",
                    "dsc": "₹1,500 - ₹2,500 per director",
                    "stamp_duty": "₹500 - ₹5,000"
                },
                "timeframe": "10-15 working days"
            },
            "startup_benefits": {
                "dpiit_recognition": {
                    "benefits": [
                        "Tax exemption for 3 consecutive years",
                        "Angel tax exemption",
                        "Patent filing rebate (80% reduction)",
                        "Easy winding up process (90 days)",
                        "Priority in government procurement"
                    ],
                    "website": "https://www.startupindia.gov.in",
                    "fee": "Free registration"
                }
            },
            "licenses": {
                "gst": {"required": True, "threshold": "₹20 lakhs", "website": "https://www.gst.gov.in"},
                "msme": {"required": True, "website": "https://www.msme.gov.in"}
            },
            "taxation": {
                "corporate_tax": "22% for domestic companies",
                "gst": "5% to 28% depending on product/service",
                "due_dates": "GST returns: 20th of next month, Income Tax: 30th September"
            }
        },
        "usa": {
            "company_registration": {
                "types": ["LLC", "C-Corporation", "S-Corporation"],
                "recommended": "C-Corporation (for VC funding) or LLC (for small businesses)",
                "process": "Register with Secretary of State in your chosen state",
                "website": "https://www.sba.gov",
                "steps": [
                    "Choose state (Delaware recommended for startups)",
                    "Choose registered agent service",
                    "File Articles of Organization/Incorporation",
                    "Obtain EIN from IRS",
                    "Create Operating Agreement/Bylaws"
                ],
                "fee": {"state_filing": "$90 - $500", "registered_agent": "$100 - $300/year"},
                "timeframe": "1-7 business days"
            },
            "taxation": {"federal_corporate_tax": "21%", "state_taxes": "Varies by state"}
        },
        "uk": {
            "company_registration": {
                "types": ["Private Limited Company (Ltd)"],
                "recommended": "Private Limited Company",
                "process": "Register with Companies House",
                "website": "https://www.gov.uk/limited-company-formation",
                "steps": [
                    "Choose company name",
                    "Register online with Companies House",
                    "Get registered address",
                    "Appoint directors and shareholders"
                ],
                "fee": {"standard": "£12", "same_day": "£100"},
                "timeframe": "3-24 hours"
            },
            "taxation": {"corporation_tax": "19%", "vat": "20%"}
        },
        "singapore": {
            "company_registration": {
                "types": ["Private Limited Company (Pte Ltd)"],
                "recommended": "Private Limited Company",
                "process": "Register through ACRA",
                "website": "https://www.acra.gov.sg",
                "steps": [
                    "Reserve company name",
                    "File incorporation via BizFile+",
                    "Appoint director (Singapore resident)",
                    "Appoint company secretary"
                ],
                "fee": {"registration": "S$300"},
                "timeframe": "1-3 working days"
            },
            "taxation": {"corporate_tax": "17%", "gst": "8%"}
        },
        "germany": {
            "company_registration": {
                "types": ["GmbH", "UG (haftungsbeschränkt)"],
                "recommended": "GmbH (standard) or UG (low capital)",
                "process": "Register at local trade office and commercial register",
                "steps": [
                    "Draft partnership agreement (notarized)",
                    "Minimum capital: €25,000 for GmbH, €1 for UG",
                    "Register at trade office (Gewerbeamt)",
                    "Register at commercial register (Handelsregister)"
                ],
                "fee": {"notary": "€500 - €1,500", "court_fees": "€200 - €400"},
                "timeframe": "2-4 weeks"
            }
        },
        "uae": {
            "company_registration": {
                "types": ["Mainland LLC", "Free Zone Company"],
                "recommended": "Free Zone Company (100% ownership, tax benefits)",
                "website": "https://www.dubaiinternetcity.com",
                "steps": ["Choose free zone", "Submit application", "Get business license"],
                "fee": "AED 15,000 - AED 50,000",
                "timeframe": "2-4 weeks"
            },
            "taxation": {"corporate_tax": "0% (free zones)", "vat": "5%"}
        }
    }
    
    country_key = country.lower().strip()
    data = country_data.get(country_key, country_data["india"])
    
    city_specific = ""
    if city and country_key == "india":
        city_roc = {
            "mumbai": "ROC Mumbai (Maharashtra)",
            "delhi": "ROC Delhi (NCT of Delhi)",
            "bangalore": "ROC Bangalore (Karnataka)",
            "chennai": "ROC Chennai (Tamil Nadu)",
            "kolkata": "ROC Kolkata (West Bengal)",
            "hyderabad": "ROC Hyderabad (Telangana)",
            "vijayawada": "ROC Vijayawada (Andhra Pradesh)"
        }
        if city.lower() in city_roc:
            city_specific = f"📍 Local ROC for {city}: {city_roc[city.lower()]}"
    
    return json.dumps({
        "country": country,
        "city": city or "Not specified",
        "data": data,
        "city_specific": city_specific
    })
# ==================== TRADITIONAL TOOLS ====================

@tool
def calculate_tax_liability(revenue: float, expenses: float, jurisdiction: str) -> str:
    """Calculate tax liability based on revenue, expenses, and jurisdiction."""
    taxable_income = revenue - expenses
    tax_rates = {
        "USA": 0.21,
        "UK": 0.19,
        "INDIA": 0.25,
        "GERMANY": 0.30
    }
    rate = tax_rates.get(jurisdiction.upper(), 0.25)
    tax = taxable_income * rate
    return json.dumps({
        "tax_due": round(tax, 2),
        "taxable_income": round(taxable_income, 2),
        "effective_rate": rate,
        "currency": "USD" if jurisdiction == "USA" else "Local"
    })

@tool
def generate_payslip(employee_name: str, salary: float, deductions: float, month: str) -> str:
    """Generate a payslip for an employee."""
    net_pay = salary - deductions
    return json.dumps({
        "employee": employee_name,
        "month": month,
        "gross_salary": salary,
        "deductions": deductions,
        "net_pay": net_pay,
        "generated_date": datetime.now().isoformat()
    })

@tool
def check_domain_availability(domain_name: str, tld: str = "com") -> str:
    """Check if a domain name is available for purchase."""
    unavailable = ["google", "facebook", "amazon", "microsoft"]
    if domain_name.lower() in unavailable:
        return json.dumps({"available": False, "domain": f"{domain_name}.{tld}", "suggestion": f"Try {domain_name}ai.{tld}"})
    return json.dumps({
        "available": True,
        "domain": f"{domain_name}.{tld}",
        "price": 12.99,
        "registrar": "GoDaddy",
        "purchase_url": f"https://example.com/buy/{domain_name}"
    })

@tool
def add_to_crm(lead_name: str, email: str, stage: str, score: int) -> str:
    """Add a lead to the CRM system."""
    return json.dumps({
        "status": "success",
        "lead_id": f"LEAD_{datetime.now().timestamp()}",
        "name": lead_name,
        "email": email,
        "stage": stage,
        "score": score,
        "added_at": datetime.now().isoformat()
    })

@tool
def calculate_vc_valuation(revenue: float, growth_rate: float, industry_multiplier: float = 10) -> str:
    """Calculate startup valuation for VC funding."""
    valuation = revenue * industry_multiplier * (1 + growth_rate/100)
    return json.dumps({
        "valuation": round(valuation, 2),
        "method": "Revenue Multiple",
        "multiple_used": industry_multiplier,
        "adjusted_for_growth": growth_rate,
        "recommended_raise": round(valuation * 0.20, 2)
    })



# For brevity in this response, I'm showing the structure.
# YOU MUST PASTE YOUR ACTUAL TOOL FUNCTIONS HERE.

# ==================== LLM INITIALIZATION ====================
llm_pro = ChatDeepSeek(
    model="deepseek-chat",
    api_key=DEEPSEEK_API_KEY,
    temperature=0.3,
    max_tokens=4096
)

llm_flash = ChatDeepSeek(
    model="deepseek-chat",
    api_key=DEEPSEEK_API_KEY,
    temperature=0.9,
    max_tokens=2048
)

# ==================== STATE DEFINITION ====================
class FounderState(TypedDict):
    messages: List
    current_task: str
    idea_description: str
    idea_score: int
    market_research_results: str
    financial_metrics: dict
    domain_info: dict
    tax_info: dict
    vc_info: dict
    ca_info: dict
    crm_status: str
    payslip_info: dict
    astrology_advice: str
    trend_score: int
    competitors_data: dict
    market_validation_data: dict
    quantitative_score: float

# ==================== AGENT FUNCTIONS ====================
# [PASTE ALL YOUR AGENT FUNCTIONS HERE - idea_evaluation_agent, market_research_agent,
#  domain_purchase_agent, tax_filing_agent, vc_funding_agent, ca_work_agent,
# ==================== AGENT 1: IDEA EVALUATION ====================

def idea_evaluation_agent(state: FounderState):
    """Evaluates startup idea using real data from Google Trends, Tavily, and Exa AI"""
    
    idea = state.get("idea_description", "")
    
    print("\n📊 Collecting real-time market data...")
    
    print("   🔍 Fetching Google Trends data...")
    trend_result = google_trends_tool.invoke({"startup_idea": idea})
    trend_data = json.loads(trend_result)
    trend_score = trend_data.get("trend_score", 50)
    print(f"      📈 Trend Score: {trend_score}/100")
    
    print("   🔍 Searching for competitors...")
    competitor_result = competitor_search_tool.invoke({"startup_idea": idea})
    competitor_data = json.loads(competitor_result)
    competitors = competitor_data.get("competitors", [])
    print(f"      🏢 Found {len(competitors)} competitors")
    
    print("   🔍 Checking market validation...")
    validation_result = market_validation_tool.invoke({"startup_idea": idea})
    validation_data = json.loads(validation_result)
    print(f"      ✅ Found {validation_data.get('similar_count', 0)} similar products")
    
    print("   🔍 Calculating quantitative score...")
    
    innovation_prompt = f"""Rate the innovation level of this startup idea from 0-100:
    
Idea: {idea}

Consider:
- Uniqueness (is this truly novel or a copy?)
- Technology advancement
- Business model innovation
- Barrier to entry

Respond ONLY with a number between 0-100."""
    
    innovation_response = llm_flash.invoke([
        SystemMessage(content="You are an innovation expert. Respond with only a number."),
        HumanMessage(content=innovation_prompt)
    ])
    
    try:
        innovation_score = int(re.search(r'\d+', innovation_response.content).group())
        innovation_score = min(100, max(0, innovation_score))
    except:
        innovation_score = 65
    
    validation_data['innovation_score'] = innovation_score
    
    score_result = idea_scorer_tool.invoke({
        "startup_idea": idea,
        "trend_score": trend_score,
        "competitors": competitors,
        "market_validation": validation_data
    })
    score_data = json.loads(score_result)
    
    print("   📝 Generating comprehensive report...")
    
    evaluation_prompt = f"""Based on REAL MARKET DATA, evaluate this startup idea:

STARTUP IDEA: {idea}

QUANTITATIVE DATA:
- Google Trends Score: {trend_score}/100
- Competitors Found: {len(competitors)}
- Similar Products Found: {validation_data.get('similar_count', 0)}
- Innovation Score: {innovation_score}/100
- Final Score: {score_data['final_score']}/100
- Recommendation: {score_data['recommendation']}

COMPETITOR LIST:
{json.dumps(competitors[:3], indent=2) if competitors else 'No competitors found'}

MARKET TRENDS:
{json.dumps(validation_data.get('market_trends', [])[:2], indent=2)}

Provide a detailed evaluation with:
1. **EXECUTIVE SUMMARY** (2-3 sentences)
2. **SCORE BREAKDOWN** (explain each component)
3. **MARKET OPPORTUNITY** (problems, gaps, your advantage)
4. **COMPETITIVE LANDSCAPE** (threats and differentiation)
5. **TOP 3 RISKS** (specific and actionable)
6. **TOP 3 OPPORTUNITIES** (how to win)
7. **ACTIONABLE RECOMMENDATIONS** (next steps)

Be brutally honest and data-driven."""
    
    response = llm_pro.invoke([
        SystemMessage(content="You are a senior startup analyst with VC experience."),
        HumanMessage(content=evaluation_prompt)
    ])
    
    final_output = f"""

📊 QUANTITATIVE SCORE BREAKDOWN


🎯 FINAL SCORE: {score_data['final_score']}/100
📈 RECOMMENDATION: {score_data['recommendation']}
⚡ URGENCY: {score_data['urgency']}

Detailed Breakdown:
   📊 Market Trend:     {score_data['breakdown']['market_trend']}/30
   🏢 Competition:      {score_data['breakdown']['competition']}/25
   ✅ Validation:       {score_data['breakdown']['market_validation']}/25
   💡 Innovation:       {score_data['breakdown']['innovation']}/20

Raw Scores:
   Google Trends:       {trend_score}/100
   Competition Level:   {score_data['raw_scores']['competition_score']}/100
   Market Validation:   {score_data['raw_scores']['validation_score']}/100
   Innovation:          {innovation_score}/100


📋 DETAILED ANALYSIS


{response.content}
"""
    
    return {
        "messages": [AIMessage(content=final_output)],
        "idea_score": int(score_data['final_score'] / 10),
        "trend_score": trend_score,
        "competitors_data": competitor_data,
        "market_validation_data": validation_data,
        "quantitative_score": score_data['final_score'],
        "current_task": "evaluated"
    }

# ==================== AGENT 2: MARKET RESEARCH ====================

def market_research_agent(state: FounderState):
    """Conducts thorough market research with problems and solutions"""
    idea = state.get("idea_description", "")
    quantitative_score = state.get("quantitative_score", 0)
    competitors = state.get("competitors_data", {}).get("competitors", [])
    
    system_prompt = f"""You are a senior market research analyst. Using this data:

QUANTITATIVE SCORE: {quantitative_score}/100
COMPETITORS FOUND: {len(competitors)}

Provide a COMPREHENSIVE market research report with:

**1. CURRENT MARKET PROBLEMS (3-5 specific pain points)**
List major problems customers face. Be specific and actionable.

**2. EXISTING SOLUTIONS & COMPETITORS**
Based on the competitors found: {json.dumps([c.get('name') for c in competitors[:3]]) if competitors else 'No specific competitors found'}
What are their approaches and limitations?

**3. MARKET GAPS (What's missing)**
What problems remain unsolved? Where are competitors falling short?

**4. YOUR UNIQUE OPPORTUNITY**
How can this specific idea fill the gaps?

**5. MARKET SIZE & TRENDS**
Estimated TAM, SAM, SOM. Growth rates and emerging trends.

Be data-driven, specific, and brutally honest."""
    
    response = llm_pro.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Startup Idea: {idea}")
    ])
    
    return {
        "messages": [response],
        "market_research_results": response.content,
        "current_task": "market_researched"
    }

# ==================== AGENT 3: DOMAIN PURCHASE ====================

def domain_purchase_agent(state: FounderState):
    """Checks and suggests domain names"""
    idea = state.get("idea_description", "")
    
    response = llm_flash.invoke([
        SystemMessage(content="Generate 5 potential domain names based on this startup idea. Keep them short and memorable."),
        HumanMessage(content=idea)
    ])
    
    words = re.findall(r'\b\w+\b', response.content[:200])
    suggested_name = words[0] if words else "startup"
    
    availability = check_domain_availability.invoke({"domain_name": suggested_name})
    
    return {
        "messages": [response, AIMessage(content=f"Domain check: {availability}")],
        "domain_info": json.loads(availability),
        "current_task": "domain_checked"
    }

# ==================== AGENT 4: TAX FILING ====================

def tax_filing_agent(state: FounderState):
    """Handles tax calculations and filings"""
    financials = state.get("financial_metrics", {"revenue": 0, "expenses": 0})
    
    if financials.get("revenue", 0) == 0:
        return {
            "messages": [AIMessage(content="No financial data provided. Tax calculation skipped.")],
            "tax_info": {},
            "current_task": "tax_skipped"
        }
    
    tax_result = calculate_tax_liability.invoke({
        "revenue": financials.get("revenue", 0),
        "expenses": financials.get("expenses", 0),
        "jurisdiction": "USA"
    })
    
    response = llm_pro.invoke([
        SystemMessage(content="Explain this tax calculation in simple terms."),
        HumanMessage(content=f"Tax calculation result: {tax_result}")
    ])
    
    return {
        "messages": [response],
        "tax_info": json.loads(tax_result),
        "current_task": "tax_calculated"
    }

# ==================== AGENT 5: VC FUNDING ====================

def vc_funding_agent(state: FounderState):
    """Prepares for VC funding and valuations"""
    financials = state.get("financial_metrics", {"revenue": 0, "growth_rate": 0})
    quantitative_score = state.get("quantitative_score", 0)
    
    if financials.get("revenue", 0) == 0:
        return {
            "messages": [AIMessage(content="No revenue data provided. VC valuation skipped.")],
            "vc_info": {},
            "current_task": "vc_skipped"
        }
    
    valuation = calculate_vc_valuation.invoke({
        "revenue": financials.get("revenue", 0),
        "growth_rate": financials.get("growth_rate", 50),
        "industry_multiplier": 10
    })
    
    response = llm_pro.invoke([
        SystemMessage(content=f"You are a VC partner. The startup scored {quantitative_score}/100 on our evaluation. Provide funding advice."),
        HumanMessage(content=f"Valuation: {valuation}\nIdea: {state.get('idea_description', '')[:200]}")
    ])
    
    return {
        "messages": [response],
        "vc_info": json.loads(valuation),
        "current_task": "vc_advised"
    }

# ==================== AGENT 6: CA WORK (Enhanced with Country-Specific Guidance) ====================

def ca_work_agent(state: FounderState):
    """Enhanced CA agent with country-specific legal registration guidance"""
    
    ca_info = state.get("ca_info", {})
    
    if ca_info.get("country"):
        country = ca_info["country"]
        city = ca_info.get("city", "")
        print(f"\n📋 Using pre-selected country: {country.upper()}")
    else:
        print("📋 CA & LEGAL REGISTRATION AGENT")
        
        print("\nTo provide accurate legal guidance, please tell me:")
        
        print("\n🌍 Available Countries:")
        print("   • India")
        print("   • USA")
        print("   • UK")
        print("   • Singapore")
        print("   • Germany")
        print("   • UAE")
        
        country = input("\n👉 Which country are you registering in? ").strip()
        city = input(f"👉 Which city in {country}? ").strip()
    
    legal_result = get_country_regulation_info.invoke({"country": country, "city": city})
    legal_data = json.loads(legal_result)
    country_info = legal_data["data"]
    
    guide_prompt = f"""You are a Senior Chartered Accountant. Provide a detailed company registration guide for {country.upper()}.

REGISTRATION DATA:
{json.dumps(country_info, indent=2)}

Please provide a comprehensive guide with these exact sections:

**📍 REGISTRATION SUMMARY FOR {country.upper()}**
- Location: {city if city else 'Not specified'}

**✅ RECOMMENDED COMPANY STRUCTURE**
- Best structure for startups
- Why this is recommended

**📝 STEP-BY-STEP REGISTRATION PROCESS**
1. First step
2. Second step (continue through all steps)

**💰 REGISTRATION FEES BREAKDOWN**
- List all fees with amounts

**🏛️ GOVERNMENT WEBSITES & CONTACTS**
- Direct links to registration portals

**📋 REQUIRED LICENSES & PERMITS**
- Mandatory licenses with links

**⚡ STARTUP BENEFITS (if available)**
- Government incentives and schemes

**⚠️ COMMON LEGAL PITFALLS TO AVOID**

Keep it concise, actionable, and specific to {country}.
"""
    
    response = llm_pro.invoke([
        SystemMessage(content=guide_prompt),
        HumanMessage(content=f"Startup: {state.get('idea_description', '')[:150]}")
    ])
    
    registration_output = f"""

📋 COMPANY REGISTRATION GUIDE FOR {country.upper()}


📍 Location: {city if city else 'Not specified'}

✅ RECOMMENDED STRUCTURE: {country_info.get('company_registration', {}).get('recommended', 'See below')}

🌐 REGISTRATION WEBSITE: {country_info.get('company_registration', {}).get('website', 'Check local authority')}

💰 ESTIMATED FEES: 
{json.dumps(country_info.get('company_registration', {}).get('fee', {}), indent=2)}

⏱️ TIMEFRAME: {country_info.get('company_registration', {}).get('timeframe', '2-4 weeks')}

{legal_data.get('city_specific', '')}


📝 DETAILED REGISTRATION GUIDE


{response.content}


🔗 IMPORTANT LINKS FOR {country.upper()}


• Company Registration: {country_info.get('company_registration', {}).get('website', 'N/A')}
• Startup Benefits: {country_info.get('startup_benefits', {}).get('dpiit_recognition', {}).get('website', 'N/A')}
• Tax Portal: {country_info.get('licenses', {}).get('gst', {}).get('website', 'N/A')}


⚡ YOUR NEXT STEPS


1. Visit the registration website above
2. Prepare required documents (ID, address proof, business plan)
3. Register your company name
4. Complete incorporation filing
5. Apply for necessary licenses
6. Open a business bank account
7. Register for taxes

💡 Need help? Consult a local CA or legal expert in {city if city else 'your city'}.
"""
    
    return {
        "messages": [AIMessage(content=registration_output)],
        "ca_info": {
            "country": country,
            "city": city,
            "registration_guide": registration_output,
            "website": country_info.get('company_registration', {}).get('website', ''),
            "estimated_fee": country_info.get('company_registration', {}).get('fee', {})
        },
        "current_task": "ca_advised"
    }

# ==================== AGENT 7: PAYSLIP GENERATOR ====================

def payslip_generator_agent(state: FounderState):
    """Generates payslips for employees"""
    payslip = generate_payslip.invoke({
        "employee_name": "Sample Employee",
        "salary": 75000,
        "deductions": 15000,
        "month": datetime.now().strftime("%B %Y")
    })
    
    response = llm_flash.invoke([
        SystemMessage(content="Generate a professional email to send this payslip."),
        HumanMessage(content=f"Payslip data: {payslip}")
    ])
    
    return {
        "messages": [response],
        "payslip_info": json.loads(payslip),
        "current_task": "payslip_generated"
    }

# ==================== AGENT 8: ASTROLOGY SUPPORT ====================

def astrology_support_agent(state: FounderState):
    """Provides motivational astrology guidance"""
    idea = state.get("idea_description", "")
    score = state.get("idea_score", 5)
    quantitative_score = state.get("quantitative_score", 0)
    
    response = llm_flash.invoke([
        SystemMessage(content="""Provide motivational astrology guidance:
        1. Zodiac reading for the founder based on their startup journey
        2. Auspicious launch date in next 30 days
        3. Motivational message tied to their score"""),
        HumanMessage(content=f"Startup: {idea}\nScore: {score}/10 (Quantitative: {quantitative_score}/100)")
    ])
    
    return {
        "messages": [response],
        "astrology_advice": response.content,
        "current_task": "astrology_done"
    }

# ==================== AGENT 9: CRM INTEGRATION ====================

def crm_integration_agent(state: FounderState):
    """Integrates with CRM system"""
    score = state.get("idea_score", 0)
    quantitative_score = state.get("quantitative_score", 0)
    
    crm_result = add_to_crm.invoke({
        "lead_name": f"Startup_{datetime.now().strftime('%Y%m%d')}",
        "email": "founder@example.com",
        "stage": "Idea Validation",
        "score": int(quantitative_score)
    })
    
    response = llm_pro.invoke([
        SystemMessage(content="Summarize CRM addition and suggest next steps based on the quantitative score."),
        HumanMessage(content=f"CRM result: {crm_result}\nScore: {quantitative_score}/100")
    ])
    
    return {
        "messages": [response],
        "crm_status": crm_result,
        "current_task": "crm_updated"
    }


#  payslip_generator_agent, astrology_support_agent, crm_integration_agent]

# ==================== AGENT CARDS DATA ====================
AGENTS = {
    "idea_evaluation": {"name": "Idea Evaluation", "icon": "📊", "desc": "Data-driven startup scoring 0-100", "requires_financials": False, "requires_country": False},
    "market_research": {"name": "Market Research", "icon": "📈", "desc": "Problems, solutions & competitors", "requires_financials": False, "requires_country": False},
    "domain_purchase": {"name": "Domain Purchase", "icon": "🌐", "desc": "Domain availability check", "requires_financials": False, "requires_country": False},
    "vc_funding": {"name": "VC Funding", "icon": "💰", "desc": "Valuation & investor advice", "requires_financials": True, "requires_country": False},
    "ca_work": {"name": "CA & Legal", "icon": "📋", "desc": "Company registration & compliance", "requires_financials": False, "requires_country": True},
    "tax_filing": {"name": "Tax Filing", "icon": "💸", "desc": "Tax liability calculation", "requires_financials": True, "requires_country": False},
    "payslip": {"name": "Payslip Generator", "icon": "📄", "desc": "Payroll document generation", "requires_financials": True, "requires_country": False},
    "astrology": {"name": "Astrology Support", "icon": "✨", "desc": "Motivational cosmic guidance", "requires_financials": False, "requires_country": False},
    "crm": {"name": "CRM Integration", "icon": "🤝", "desc": "Lead tracking & follow-ups", "requires_financials": False, "requires_country": False}
}

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### 🚀 FoundersAgent")
    st.markdown("---")
    st.markdown("#### 🔧 API Status")
    st.markdown(f"DeepSeek: {'✅' if DEEPSEEK_API_KEY else '❌'}")
    st.markdown(f"SerpAPI: {'✅' if SERPAPI_API_KEY else '❌'}")
    st.markdown(f"Tavily: {'✅' if TAVILY_API_KEY else '❌'}")
    st.markdown(f"Exa AI: {'✅' if EXA_API_KEY else '❌'}")
    st.markdown("---")
    st.markdown("#### 📊 Stats")
    st.markdown("• 9 Specialized Agents")
    st.markdown("• Real-time Market Data")
    st.markdown("• 30-45 Second Analysis")
    st.markdown("---")
    with st.expander("ℹ️ How it works"):
        st.markdown("1. Select an agent from cards below\n2. Enter your startup idea\n3. Add optional details\n4. Click Analyze")
    st.markdown("---")
    st.caption("Made with ❤️ for Startup Founders")

# ==================== MAIN CONTENT ====================
st.markdown('<p class="main-title">FoundersAgent</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #94a3b8;">Your AI Co-Founder in a Box</p>', unsafe_allow_html=True)
st.markdown("---")

# ==================== AGENT SELECTION ====================
st.markdown("### 🤖 Select an Agent")
st.markdown('<p style="text-align: center; margin-bottom: 1rem;">Click on any card below to select an agent</p>', unsafe_allow_html=True)

# Create 3 columns for the grid
cols = st.columns(3)

# Convert AGENTS dict to list for easier indexing
# Convert AGENTS dict to list for easier indexing
agent_list = list(AGENTS.items())

for idx, (agent_key, agent_info) in enumerate(agent_list):
    col = cols[idx % 3]
    with col:
        is_selected = st.session_state.get("selected_agent") == agent_key
        border_style = "3px solid #7C3AED" if is_selected else "1px solid #334155"
        
        # Display the card (visual only)
        st.markdown(f"""
        <div class="agent-card" style="border: {border_style};">
            <div class="agent-icon">{agent_info['icon']}</div>
            <div class="agent-name">{agent_info['name']}</div>
            <div class="agent-desc">{agent_info['desc']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Create button with FULL TEXT (emoji + name + description)
        button_text = f"Select {agent_info['name']} Agent"
        
        if st.button(button_text, key=f"btn_{agent_key}", help=f"Select {agent_info['name']}", use_container_width=True):
            st.session_state["selected_agent"] = agent_key
            st.rerun()

st.markdown("---")

# ==================== SELECTED AGENT INFO ====================
# FIX: Initialize selected_agent variable here
selected_agent = None

if "selected_agent" in st.session_state:
    selected_agent = st.session_state["selected_agent"]
    agent_info = AGENTS[selected_agent]
    st.success(f"✅ **Selected:** {agent_info['icon']} {agent_info['name']} - {agent_info['desc']}")

# ==================== INPUT FORM ====================
st.markdown("### 📝 Enter Your Startup Details")

idea = st.text_area("**Startup Idea**", placeholder="Example: AI-powered drone delivery system for medicines and food...", height=100)

col1, col2 = st.columns(2)
financial_metrics = {"revenue": 0, "expenses": 0, "growth_rate": 0}
ca_country = ""
ca_city = ""

# Now selected_agent is always defined (even if None)
if selected_agent and AGENTS[selected_agent]["requires_financials"]:
    with col1:
        st.markdown("#### 💰 Financial Metrics")
        revenue = st.number_input("Monthly Revenue (USD)", min_value=0, value=0, step=1000)
        expenses = st.number_input("Monthly Expenses (USD)", min_value=0, value=0, step=1000)
        growth = st.number_input("Growth Rate (%)", min_value=0, value=0, step=5)
        financial_metrics = {"revenue": revenue, "expenses": expenses, "growth_rate": growth}

if selected_agent and AGENTS[selected_agent]["requires_country"]:
    with col2:
        st.markdown("#### 🌍 Location Info")
        ca_country = st.selectbox("Country", ["India", "USA", "UK", "Singapore", "Germany", "UAE"])
        ca_city = st.text_input("City", placeholder="e.g., Bangalore, Mumbai, Delhi")

# Center the analyze button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    analyze = st.button("🚀 Analyze Now", use_container_width=True)

# ==================== ANALYSIS ====================
if analyze and idea:
    if not selected_agent:
        st.warning("⚠️ Please select an agent first!")
        st.stop()
    
    with st.spinner(f"🔄 Running {AGENTS[selected_agent]['name']} agent... (30-45 seconds)"):
        # Build graph with single agent
        workflow = StateGraph(FounderState)
        
        agent_map = {
            "idea_evaluation": idea_evaluation_agent,
            "market_research": market_research_agent,
            "domain_purchase": domain_purchase_agent,
            "vc_funding": vc_funding_agent,
            "ca_work": ca_work_agent,
            "tax_filing": tax_filing_agent,
            "payslip": payslip_generator_agent,
            "astrology": astrology_support_agent,
            "crm": crm_integration_agent
        }
        
        workflow.add_node("agent", agent_map[selected_agent])
        workflow.set_entry_point("agent")
        workflow.add_edge("agent", END)
        app = workflow.compile()
        
        initial_state = {
            "messages": [], "current_task": "start", "idea_description": idea, "idea_score": 0,
            "market_research_results": "", "financial_metrics": financial_metrics,
            "domain_info": {}, "tax_info": {}, "vc_info": {}, "crm_status": "", "payslip_info": {},
            "astrology_advice": "", "trend_score": 0, "competitors_data": {}, "market_validation_data": {},
            "quantitative_score": 0, "ca_info": {"country": ca_country, "city": ca_city} if ca_country else {}
        }
        
        try:
            final_state = app.invoke(initial_state)
            
            st.markdown("---")
            st.markdown("### 📊 Analysis Report")
            
            if final_state.get("quantitative_score"):
                score = final_state["quantitative_score"]
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f'<div class="score-card"><div class="score-number">{score}/100</div><div>Score</div></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="score-card"><div class="score-number">{final_state.get("idea_score", 0)}/10</div><div>Converted</div></div>', unsafe_allow_html=True)
            
            for msg in final_state.get("messages", []):
                if isinstance(msg, AIMessage):
                    st.markdown(msg.content)
            
            report_text = "\n".join([m.content for m in final_state["messages"] if isinstance(m, AIMessage)])
            if report_text:
                st.download_button("📥 Download Report", report_text, f"foundersagent_report.txt", use_container_width=True)
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            
elif analyze and not idea:
    st.warning("⚠️ Please enter your startup idea!")

st.markdown("---")
st.caption("FoundersAgent - Your AI Co-Founder in a Box | Powered by DeepSeek V4")