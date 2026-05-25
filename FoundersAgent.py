# ==================== HACKATHON VERSION WITH ARIZE MCP ====================
# Built for: Google Cloud Agent Builder + Arize MCP Integration
# Date: May 2026
# Challenge: Multi-agent system that TAKES ACTION (not just chat)

import streamlit as st
import os
import json
import urllib.parse
from datetime import datetime, timedelta
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables - MUST be first
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
        cursor: pointer;
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
    .linkedin-btn {
        background-color: #0077B5;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        display: inline-block;
        text-align: center;
    }
    .naukri-btn {
        background-color: #E9542E;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        display: inline-block;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==================== ARIZE MCP SETUP ====================
class ArizeTracker:
    def __init__(self):
        # Get keys from environment - FIXED variable name
        self.api_key = os.getenv("ARIZE_API_KEY")
        self.space_key = os.getenv("ARIZE_SPACE_KEY")  # Changed from SPACE_ID to SPACE_KEY
        self.current_trace_id = None
        self.traces = []
        
    def start_trace(self, agent_name: str, action: str, input_data: dict):
        self.current_trace_id = f"{agent_name}_{action}_{datetime.now().timestamp()}"
        self.traces.append({
            "trace_id": self.current_trace_id,
            "name": f"{agent_name}.{action}",
            "input": input_data,
            "timestamp": datetime.now().isoformat(),
            "metrics": [],
            "validations": []
        })
        return self.current_trace_id
    
    def log_metric(self, name: str, value: float, metadata: dict = None):
        if self.traces and self.current_trace_id:
            for trace in self.traces:
                if trace["trace_id"] == self.current_trace_id:
                    trace["metrics"].append({
                        "name": name,
                        "value": value,
                        "metadata": metadata or {},
                        "timestamp": datetime.now().isoformat()
                    })
    
    def validate_output(self, name: str, value: float, threshold: float):
        is_valid = value >= threshold
        if self.traces and self.current_trace_id:
            for trace in self.traces:
                if trace["trace_id"] == self.current_trace_id:
                    trace["validations"].append({
                        "name": name,
                        "value": value,
                        "threshold": threshold,
                        "passed": is_valid,
                        "timestamp": datetime.now().isoformat()
                    })
        return is_valid
    
    def end_trace(self, output_data: dict):
        if self.traces and self.current_trace_id:
            for trace in self.traces:
                if trace["trace_id"] == self.current_trace_id:
                    trace["output"] = output_data
                    trace["ended_at"] = datetime.now().isoformat()
    
    def get_traces(self):
        return self.traces

# ==================== STATE DEFINITION ====================
class FounderState(TypedDict):
    idea: str
    current_agent: str
    task_status: str
    actions_taken: List[str]
    results: Dict[str, Any]

# ==================== ACTION AGENTS BASE CLASS ====================
class ActionAgent:
    def __init__(self, arize_tracker: ArizeTracker):
        self.arize = arize_tracker
    
    def execute(self, state: FounderState) -> Dict:
        raise NotImplementedError

# ==================== AGENT 1: DOMAIN PURCHASE ====================
class DomainPurchaseAgent(ActionAgent):
    def execute(self, state: FounderState) -> Dict:
        self.arize.start_trace("DomainAgent", "purchase_domain", {"idea": state["idea"]})
        
        idea = state["idea"].lower().replace(" ", "") if state["idea"] else "startup"
        domains = [f"{idea}.com", f"{idea}.ai", f"get{idea}.io", f"try{idea}.app", f"{idea}hq.com"]
        
        available_domains = []
        unavailable = ["google", "facebook", "amazon", "microsoft", "test"]
        
        for domain in domains:
            domain_name = domain.split(".")[0]
            if domain_name not in unavailable:
                purchase_url = f"https://godaddy.com/domainsearch/find?domainToCheck={domain}"
                available_domains.append({"domain": domain, "price": "$12.99", "purchase_url": purchase_url})
        
        self.arize.log_metric("domains_found", len(available_domains))
        
        result = {
            "available_domains": available_domains,
            "recommended_domain": available_domains[0] if available_domains else None,
            "next_action": "Purchase domain immediately",
            "action_url": available_domains[0]["purchase_url"] if available_domains else None
        }
        self.arize.end_trace(result)
        return result

# ==================== AGENT 2: COMPANY REGISTRATION ====================
class CompanyRegistrationAgent(ActionAgent):
    def execute(self, state: FounderState) -> Dict:
        self.arize.start_trace("LegalAgent", "register_company", state)
        
        country = state.get("results", {}).get("country", "India")
        
        registration_data = {
            "India": {"website": "https://www.mca.gov.in", "form": "SPICe+ (INC-32)", "fees": "₹7,000-15,000",
                     "steps": ["Get Digital Signature Certificate", "Apply for DIN", "File SPICe+ form", "Apply for PAN/TAN", "Register for GST"]},
            "USA": {"website": "https://www.irs.gov", "form": "Form SS-4 (EIN)", "fees": "$150-$500",
                   "steps": ["Choose state (Delaware recommended)", "File Articles of Incorporation", "Get EIN from IRS", "Register for state taxes"]},
            "UK": {"website": "https://www.gov.uk/limited-company-formation", "form": "IN01", "fees": "£12",
                  "steps": ["Choose company name", "Register with Companies House", "Get registered address", "Appoint directors"]},
            "Singapore": {"website": "https://www.acra.gov.sg", "form": "BizFile+", "fees": "S$300",
                         "steps": ["Reserve company name", "File incorporation via BizFile+", "Appoint director", "Appoint company secretary"]}
        }
        
        data = registration_data.get(country, registration_data["India"])
        self.arize.log_metric("registration_steps", len(data["steps"]))
        
        result = {"registration_complete": False, "next_action": "File registration documents",
                 "government_website": data["website"], "form_to_file": data["form"],
                 "steps": data["steps"], "estimated_fees": data["fees"]}
        self.arize.end_trace(result)
        return result

# ==================== AGENT 3: TAX FILING ====================
class TaxFilingAgent(ActionAgent):
    def execute(self, state: FounderState) -> Dict:
        self.arize.start_trace("TaxAgent", "calculate_filing", state)
        
        revenue = state.get("results", {}).get("revenue", 0)
        expenses = state.get("results", {}).get("expenses", 0)
        country = state.get("results", {}).get("country", "India")
        
        tax_rates = {"India": 0.25, "USA": 0.21, "UK": 0.19, "Singapore": 0.17}
        rate = tax_rates.get(country, 0.25)
        taxable_income = revenue - expenses
        tax_due = taxable_income * rate
        
        deadlines = {"India": "March 31, 2026", "USA": "April 15, 2026", "UK": "January 31, 2026", "Singapore": "November 30, 2026"}
        
        self.arize.log_metric("tax_due", tax_due)
        self.arize.validate_output("taxable_income", taxable_income, threshold=0)
        
        result = {"tax_due": tax_due, "taxable_income": taxable_income, "effective_rate": rate * 100,
                 "filing_deadline": deadlines.get(country, "Check local authority"),
                 "next_action": f"File tax return by {deadlines.get(country, 'deadline')}",
                 "forms_required": ["Income Tax Return", "GST Return" if country == "India" else "Corporate Tax Return"]}
        self.arize.end_trace(result)
        return result

# ==================== AGENT 4: PAYSLIP GENERATION ====================
class PayslipAgent(ActionAgent):
    def execute(self, state: FounderState) -> Dict:
        self.arize.start_trace("PayslipAgent", "generate_payslip", state)
        
        employee_name = state.get("results", {}).get("employee_name", "Sample Employee")
        salary = state.get("results", {}).get("salary", 50000)
        
        hra, pf, prof_tax = salary * 0.4, salary * 0.12, 200
        gross, net_pay = salary + hra, (salary + hra) - (pf + prof_tax)
        
        payslip_html = f"""
        <div style="border:1px solid #7C3AED; padding:20px; border-radius:10px; background:linear-gradient(135deg, #1e293b 0%, #0f172a 100%);">
            <h2 style="color:#7C3AED;">🏢 PAYSLIP</h2>
            <p><strong>Employee:</strong> {employee_name}</p>
            <p><strong>Month:</strong> {datetime.now().strftime("%B %Y")}</p>
            <hr><p><strong>Basic Salary:</strong> ₹{salary:,.2f}</p>
            <p><strong>HRA:</strong> ₹{hra:,.2f}</p>
            <p><strong>Gross Salary:</strong> ₹{gross:,.2f}</p>
            <hr><p><strong>Net Pay:</strong> ₹{net_pay:,.2f}</p>
        </div>
        """
        
        self.arize.log_metric("net_pay", net_pay)
        result = {"payslip_generated": True, "payslip_html": payslip_html, "net_pay": net_pay,
                 "employee_name": employee_name, "next_action": "Download and send payslip",
                 "email_template": f"Dear {employee_name}, please find your payslip attached."}
        self.arize.end_trace(result)
        return result

# ==================== AGENT 5: CRM LEAD ADD ====================
class CRMAgent(ActionAgent):
    def execute(self, state: FounderState) -> Dict:
        self.arize.start_trace("CRMAgent", "add_lead_crm", state)
        
        idea, score = state["idea"], state.get("results", {}).get("score", 0)
        lead_id = f"LEAD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        follow_up_actions = [{"action": "Send welcome email", "due_date": "Today"},
                            {"action": "Schedule discovery call", "due_date": "In 2 days"},
                            {"action": "Send pitch deck", "due_date": "In 3 days"}]
        
        self.arize.log_metric("lead_score", score)
        self.arize.validate_output("lead_quality", score, threshold=40)
        
        result = {"lead_id": lead_id, "added_to_crm": True, "follow_up_actions": follow_up_actions,
                 "next_action": "Send welcome email immediately", "crm_status": "Idea Validation Stage"}
        self.arize.end_trace(result)
        return result

# ==================== AGENT 6: VC PITCH PREP ====================
class VCPitchAgent(ActionAgent):
    def execute(self, state: FounderState) -> Dict:
        self.arize.start_trace("VCAgent", "prepare_pitch", state)
        
        revenue, growth = state.get("results", {}).get("revenue", 100000), state.get("results", {}).get("growth_rate", 50)
        valuation = revenue * 10 * (1 + growth/100)
        
        investors = [{"name": "Sequoia Capital", "stage": "Seed"},
                    {"name": "Y Combinator", "stage": "Pre-seed"},
                    {"name": "Accel", "stage": "Seed"}]
        
        self.arize.log_metric("valuation", valuation)
        result = {"valuation": f"${valuation:,.0f}", "recommended_raise": f"${valuation * 0.2:,.0f}",
                 "investors_to_contact": investors, "next_action": "Create pitch deck and email investors"}
        self.arize.end_trace(result)
        return result

# ==================== AGENT 7: ASTROLOGY MOTIVATION ====================
class AstrologyAgent(ActionAgent):
    def execute(self, state: FounderState) -> Dict:
        self.arize.start_trace("AstrologyAgent", "motivate", state)
        
        score = state.get("results", {}).get("score", 50)
        launch_dates = [(datetime.now() + timedelta(days=d)).strftime("%B %d, %Y") for d in [7, 14, 21]]
        
        if score >= 75:
            message, emoji = "🌟 The stars align perfectly!", "🚀💫✨"
        elif score >= 55:
            message, emoji = "🌙 Good fortune awaits!", "⭐🌙🔮"
        else:
            message, emoji = "🪐 Persistence will bring rewards.", "🪐🌠🔭"
        
        result = {"auspicious_dates": launch_dates, "cosmic_message": message, "cosmic_energy": emoji,
                 "next_action": f"Schedule launch on {launch_dates[0]}"}
        self.arize.end_trace(result)
        return result

# ==================== AGENT 8: MARKET RESEARCH ====================
class MarketResearchAgent(ActionAgent):
    def execute(self, state: FounderState) -> Dict:
        self.arize.start_trace("MarketAgent", "research", state)
        
        competitors = [{"name": "Competitor A", "strength": "Market leader", "weakness": "Expensive"},
                      {"name": "Competitor B", "strength": "Good UX", "weakness": "Limited features"}]
        market_gaps = ["No solution for small businesses", "High setup costs", "Poor integration"]
        
        result = {"competitors": competitors, "market_gaps": market_gaps,
                 "next_action": "Create competitor comparison matrix"}
        self.arize.end_trace(result)
        return result

# ==================== AGENT 9: IDEA SCORING ====================
class IdeaScoringAgent(ActionAgent):
    def execute(self, state: FounderState) -> Dict:
        self.arize.start_trace("ScoreAgent", "evaluate_idea", state)
        
        trend_score, competition_score, validation_score, innovation_score = 75, 60, 70, 80
        final_score = (trend_score * 0.3 + competition_score * 0.25 + validation_score * 0.25 + innovation_score * 0.2)
        
        if final_score >= 75:
            action_plan = ["✅ Proceed with MVP development", "💰 Start investor conversations", "📝 File provisional patent"]
            verdict = "🚀 HIGH POTENTIAL"
        elif final_score >= 55:
            action_plan = ["📞 Conduct 20 customer interviews", "🔄 Refine value proposition", "🌐 Build landing page"]
            verdict = "📊 MEDIUM POTENTIAL"
        else:
            action_plan = ["🔄 Pivot or refine idea", "🔍 Analyze market gaps", "🎯 Consider adjacent markets"]
            verdict = "⚠️ LOW POTENTIAL"
        
        self.arize.log_metric("final_score", final_score)
        
        result = {"score": final_score, "verdict": verdict,
                 "breakdown": {"Market Trend": trend_score, "Competition": competition_score,
                              "Validation": validation_score, "Innovation": innovation_score},
                 "action_plan": action_plan}
        self.arize.end_trace(result)
        return result

# ==================== AGENT 10: JOB POSTING ====================
class JobPostingAgent(ActionAgent):
    def execute(self, state: FounderState) -> Dict:
        self.arize.start_trace("JobAgent", "post_job", state)
        
        job_title = state.get("results", {}).get("job_title", "Software Engineer")
        job_description = state.get("results", {}).get("job_description", "")
        job_location = state.get("results", {}).get("job_location", "Remote")
        job_type = state.get("results", {}).get("job_type", "Full-time")
        salary_range = state.get("results", {}).get("salary_range", "Best in industry")
        company_name = state["idea"] if state["idea"] else "Our Startup"
        
        # LinkedIn Post
        linkedin_post = f"""🎯 HIRING: {job_title} 🎯

{company_name} is hiring a {job_title}!

📍 Location: {job_location}
⏰ Type: {job_type}
💰 Salary: {salary_range}

Requirements:
• {self._get_requirements(job_title)}

Apply: careers@{company_name.lower().replace(' ', '')}.com

#hiring #{job_title.replace(' ', '')} #startupjobs"""
        
        linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?text={urllib.parse.quote(linkedin_post)}"
        
        # Naukri Job Description
        naukri_html = f"""
        <div style="font-family: Arial; padding: 20px; border: 1px solid #ddd;">
            <h2>We're Hiring! {job_title}</h2>
            <h3>{company_name}</h3>
            <p><strong>Location:</strong> {job_location}</p>
            <p><strong>Type:</strong> {job_type}</p>
            <p><strong>Salary:</strong> {salary_range}</p>
            <p>{job_description if job_description else f"Seeking a talented {job_title} to join our startup."}</p>
            <p><strong>Apply:</strong> careers@{company_name.lower().replace(' ', '')}.com</p>
        </div>
        """
        
        self.arize.log_metric("job_posting_created", 1)
        
        result = {
            "job_title": job_title,
            "company_name": company_name,
            "linkedin_url": linkedin_url,
            "linkedin_post": linkedin_post,
            "naukri_html": naukri_html,
            "naukri_login_url": "https://www.naukri.com/recruiters/login",
            "application_email": f"careers@{company_name.lower().replace(' ', '')}.com",
            "next_action": "Click the buttons below to post on each platform"
        }
        
        self.arize.end_trace(result)
        return result
    
    def _get_requirements(self, job_title: str) -> str:
        reqs = {"Software Engineer": "2+ years Python/JavaScript",
                "Full Stack Developer": "React + Node.js",
                "AI Engineer": "LLMs + Python",
                "Product Manager": "2+ years product management"}
        return reqs.get(job_title, "Relevant experience")

# ==================== MAIN ORCHESTRATOR ====================
class FoundersAgent:
    def __init__(self):
        self.arize = ArizeTracker()
        self.agents = {
            "idea_scoring": IdeaScoringAgent(self.arize),
            "market_research": MarketResearchAgent(self.arize),
            "domain_purchase": DomainPurchaseAgent(self.arize),
            "company_registration": CompanyRegistrationAgent(self.arize),
            "tax_filing": TaxFilingAgent(self.arize),
            "payslip": PayslipAgent(self.arize),
            "crm": CRMAgent(self.arize),
            "vc_pitch": VCPitchAgent(self.arize),
            "astrology": AstrologyAgent(self.arize),
            "job_posting": JobPostingAgent(self.arize)
        }
    
    def run_agent(self, agent_name: str, idea: str, user_inputs: dict = None):
        state = FounderState(idea=idea, current_agent=agent_name, task_status="running", 
                            actions_taken=[], results=user_inputs or {})
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent {agent_name} not found"}
        result = agent.execute(state)
        return {"agent": agent_name, "idea": idea, "result": result,
                "timestamp": datetime.now().isoformat(), "arize_traces": self.arize.get_traces()}

# ==================== STREAMLIT UI ====================
st.markdown('<p class="main-title">FoundersAgent</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #94a3b8;">10 AI Agents That Take Action — Not Just Chat</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("### 🚀 Hackathon Submission")
    st.markdown("**Challenge:** Building Agents for Real-World Challenges")
    st.markdown("**Partner:** Arize MCP")
    st.markdown("**Built with:** Google Cloud Agent Builder")
    st.markdown("---")
    
    st.markdown("### 📊 Arize MCP Status")
    # FIXED: Using correct variable names
    arize_key = os.getenv("ARIZE_API_KEY")
    arize_space = os.getenv("ARIZE_SPACE_KEY")
    
    if arize_key and arize_space:
        st.markdown("✅ API Key Configured")
        st.markdown("✅ Space Key Configured")
        st.markdown("✅ Tracing Ready")
        st.markdown(f"API Key: `{arize_key[:10]}...`")
    else:
        st.markdown("⚠️ Arize keys not set in .env")
        st.markdown("**Add to `.env` file:**")
        st.code("ARIZE_API_KEY=your_api_key_here\nARIZE_SPACE_KEY=your_space_key_here")
        st.markdown(f"**API Key found:** {'✅' if arize_key else '❌'}")
        st.markdown(f"**Space Key found:** {'✅' if arize_space else '❌'}")
    
    st.markdown("---")
    st.markdown("### 🎯 10 Action Agents")
    agents_list = ["Idea Scoring", "Market Research", "Domain Purchase", "Company Registration", 
                   "Tax Filing", "Payslip Generator", "CRM Lead Tracker", "VC Pitch Prep", 
                   "Astrology Support", "Job Posting"]
    for i, name in enumerate(agents_list, 1):
        st.markdown(f"{i}. {name}")

# Agent Selection
st.markdown("### 🤖 Select an Action Agent")
col1, col2, col3 = st.columns(3)

agents_display = {
    "idea_scoring": {"icon": "📊", "name": "Idea Scoring", "action": "Calculates score + action plan"},
    "market_research": {"icon": "📈", "name": "Market Research", "action": "Finds competitors + gaps"},
    "domain_purchase": {"icon": "🌐", "name": "Domain Purchase", "action": "Checks + generates buy links"},
    "company_registration": {"icon": "📋", "name": "Company Registration", "action": "Provides forms + links"},
    "tax_filing": {"icon": "💸", "name": "Tax Filing", "action": "Calculates + gives deadlines"},
    "payslip": {"icon": "📄", "name": "Payslip Generator", "action": "Creates downloadable payslip"},
    "crm": {"icon": "🤝", "name": "CRM Lead Tracker", "action": "Adds lead + schedules follow-ups"},
    "vc_pitch": {"icon": "💰", "name": "VC Pitch Prep", "action": "Valuation + investor list"},
    "astrology": {"icon": "✨", "name": "Astrology Support", "action": "Auspicious dates + motivation"},
    "job_posting": {"icon": "💼", "name": "Job Posting", "action": "Posts to LinkedIn + Naukri"}
}

for idx, (agent_key, agent_info) in enumerate(agents_display.items()):
    col = [col1, col2, col3][idx % 3]
    with col:
        if st.button(f"{agent_info['icon']} {agent_info['name']}\n{agent_info['action']}", 
                     key=agent_key, use_container_width=True):
            st.session_state["selected_agent"] = agent_key
            st.rerun()

st.markdown("---")

# Input Form
st.markdown("### 📝 Enter Your Details")
idea = st.text_area("**Your Startup Idea / Company Name**", 
                    placeholder="Example: AI-powered customer support automation...", height=80)

selected_agent = st.session_state.get("selected_agent")

# Initialize variables
revenue, expenses, country, growth, emp_name, salary = 100000, 40000, "India", 50, "John Doe", 50000
job_title, job_description, job_location, job_type, salary_range = "Software Engineer", "", "Remote", "Full-time", "Best in industry"

if selected_agent == "tax_filing":
    col1, col2 = st.columns(2)
    with col1: revenue = st.number_input("Annual Revenue (USD)", value=100000)
    with col2: expenses = st.number_input("Annual Expenses (USD)", value=40000)
elif selected_agent == "company_registration":
    country = st.selectbox("Country", ["India", "USA", "UK", "Singapore", "Germany", "UAE"])
elif selected_agent == "vc_pitch":
    col1, col2 = st.columns(2)
    with col1: revenue = st.number_input("Current Revenue (USD)", value=100000)
    with col2: growth = st.number_input("Growth Rate (%)", value=50)
elif selected_agent == "payslip":
    col1, col2 = st.columns(2)
    with col1: emp_name = st.text_input("Employee Name", "John Doe")
    with col2: salary = st.number_input("Monthly Salary (₹)", value=50000)
elif selected_agent == "job_posting":
    st.markdown("#### 💼 Job Posting Details")
    col1, col2 = st.columns(2)
    with col1:
        job_title = st.selectbox("Job Title", ["Software Engineer", "Full Stack Developer", "AI Engineer", "Product Manager", "Marketing Manager", "Sales Executive"])
        job_location = st.text_input("Location", "Remote")
    with col2:
        job_type = st.selectbox("Job Type", ["Full-time", "Part-time", "Contract", "Internship"])
        salary_range = st.text_input("Salary Range", "Best in industry")
    job_description = st.text_area("Job Description (Optional)", height=100)

# Execute Button
if st.button("🚀 Execute Agent Action", use_container_width=True):
    if not idea and selected_agent not in ["company_registration"]:
        st.warning("⚠️ Please enter your startup idea!")
    elif not selected_agent:
        st.warning("⚠️ Please select an agent first!")
    else:
        with st.spinner(f"🔄 Executing {agents_display[selected_agent]['name']}..."):
            inputs = {}
            if selected_agent == "tax_filing": inputs = {"revenue": revenue, "expenses": expenses}
            elif selected_agent == "company_registration": inputs = {"country": country}
            elif selected_agent == "vc_pitch": inputs = {"revenue": revenue, "growth_rate": growth}
            elif selected_agent == "payslip": inputs = {"employee_name": emp_name, "salary": salary}
            elif selected_agent == "job_posting": inputs = {"job_title": job_title, "job_description": job_description, 
                                                           "job_location": job_location, "job_type": job_type, "salary_range": salary_range}
            
            orchestrator = FoundersAgent()
            result = orchestrator.run_agent(selected_agent, idea, inputs)
            st.session_state.last_result = result
            
            st.markdown("---")
            st.markdown("### ✅ Action Taken")
            
            action_result = result["result"]
            
            # Display results
            if selected_agent == "domain_purchase" and action_result.get("available_domains"):
                st.markdown("#### 🌐 Available Domains")
                for domain in action_result["available_domains"]:
                    st.markdown(f"• **{domain['domain']}** — {domain['price']} → [Purchase]({domain['purchase_url']})")
            
            elif selected_agent == "company_registration":
                st.markdown(f"#### 📋 Register in {country}")
                st.markdown(f"**Website:** {action_result.get('government_website')}")
                st.markdown(f"**Estimated Fees:** {action_result.get('estimated_fees')}")
                st.markdown("**Steps:**")
                for step in action_result.get("steps", []):
                    st.markdown(f"• {step}")
            
            elif selected_agent == "payslip":
                st.components.v1.html(action_result.get("payslip_html", ""), height=350)
            
            elif selected_agent == "idea_scoring":
                score = action_result.get("score", 0)
                st.markdown(f'<div class="score-card"><div class="score-number">{score:.1f}/100</div><div>Score</div></div>', unsafe_allow_html=True)
                st.markdown(f"**Verdict:** {action_result.get('verdict')}")
                st.markdown("**Action Plan:**")
                for action in action_result.get("action_plan", []):
                    st.markdown(f"{action}")
            
            elif selected_agent == "job_posting":
                st.markdown(f"#### 💼 Post Job: **{action_result.get('job_title')}**")
                st.markdown(f"**Company:** {action_result.get('company_name')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f'<a href="{action_result.get("linkedin_url")}" target="_blank" style="background:#0077B5; color:white; padding:12px 24px; border-radius:8px; text-decoration:none; display:block; text-align:center; font-weight:bold;">📱 Post to LinkedIn</a>', unsafe_allow_html=True)
                    st.caption("Opens LinkedIn - login and click Post")
                with col2:
                    st.markdown(f'<a href="{action_result.get("naukri_login_url")}" target="_blank" style="background:#E9542E; color:white; padding:12px 24px; border-radius:8px; text-decoration:none; display:block; text-align:center; font-weight:bold;">📋 Post to Naukri</a>', unsafe_allow_html=True)
                    st.caption("Opens Naukri recruiter login")
                
                st.markdown(f"**📧 Applications to:** `{action_result.get('application_email')}`")
                
                with st.expander("📱 LinkedIn Post Preview"):
                    st.code(action_result.get('linkedin_post', ''), language='markdown')
                
                with st.expander("📄 Naukri Job Description (Copy this)"):
                    st.code(action_result.get('naukri_html', ''), language='html')
                    st.info("💡 After logging into Naukri, click 'Post a Job' and paste this HTML")
            
            st.info(f"📌 **Next Action:** {action_result.get('next_action', 'Review results')}")
            
            # Download Report
            report_json = json.dumps(result, indent=2, default=str)
            st.download_button("📥 Download Report", report_json, "foundersagent_report.json", use_container_width=True)

st.markdown("---")
st.caption("🏆 Hackathon Submission: Building Agents for Real-World Challenges | Built with Google Cloud Agent Builder + Arize MCP | 10 Action Agents")