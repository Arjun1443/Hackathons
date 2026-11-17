"""Offline regression tests for agent logic embedded in the Streamlit entrypoints.

Extract definitions to avoid launching the UI or requiring API credentials.
Run: python -m unittest -v test_agents.py
"""
import ast
import copy
import html
import json
import math
import random
import re
import unittest
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import TypedDict, List
from uuid import uuid4
from types import SimpleNamespace

ROOT = Path(__file__).parent

class Tool:
    def __init__(self, function):
        self.function = function
    def invoke(self, values):
        return self.function(**values)

class Message:
    def __init__(self, content):
        self.content = content

def definitions(filename):
    tree = ast.parse((ROOT / filename).read_text())
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) or isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'AGENTS' for t in node.targets)]
    namespace = dict(globals(), tool=Tool, AIMessage=Message, HumanMessage=Message, SystemMessage=Message)
    for key in ('SERPAPI_API_KEY', 'TAVILY_API_KEY', 'EXA_API_KEY'):
        namespace[key] = None
    exec(compile(ast.Module(body=nodes, type_ignores=[]), filename, 'exec'), namespace)
    if 'ArizeTracker' in namespace:
        import os
        namespace['os'] = os
        namespace['arize'] = namespace['ArizeTracker']()
    return namespace

class AgentTests(unittest.TestCase):
    def setUp(self):
        self.demo = definitions('FoundersAgent.py')
        self.main = definitions('app.py')

    def execute(self, name, **inputs):
        return self.demo[name].execute(inputs)

    def test_all_24_helpers_return_serializable_results(self):
        inputs = dict(skills='Python, AI', budget='5000', industry='SaaS', country='India', interests='learning', idea_name='Learning assistant', problem='Tracking learning progress', business_type='B2B SaaS', idea='Learnflow', document_type='NDA', company_name='Learnflow', brand_name='Learnflow', revenue=100000, expenses=40000, tax_rate=20, monthly_burn=50000, cash_balance=500000, monthly_revenue=10000, client_name='Client', amount=5000, description='Training', job_title='Trainer', company='Learnflow', location='Remote', job_type='Contract', job_requirements='Python, ML', resumes='Naga\nPython and ML trainer', employee_name='Naga', salary=50000, salary_min=500000, salary_max=800000, deductions=1000, month='November 2026', role='Trainer', lead_name='Client', lead_score=75, prospect_name='Client', value_prop='training', topic='Learning', content_type='Blog Post', growth_rate=50, profit_margin=20, product_type='AI App', features='document search, citations', zodiac='Leo', score=65, work_hours=2, priorities='Customer calls, Product development')
        self.assertEqual(len(self.demo['AGENTS']), 24)
        for name, info in self.demo['AGENTS'].items():
            with self.subTest(agent=name):
                result = info['agent'].execute(copy.deepcopy(inputs))
                self.assertIsInstance(result, dict)
                self.assertTrue(result.get('next_action'))
                json.dumps(result, allow_nan=False)

    def test_job_posting_salary_and_platform_options(self):
        result = self.execute('JobPostingAgent', job_title='AI Trainer', company='AIQUBIX', location='Remote', salary_min=60000, salary_max=90000, salary_currency='INR', salary_period='month', responsibilities='Teach Python', requirements='Python and ML', benefits='Flexible hours', application_contact='hiring@example.com')
        self.assertIn('INR 60,000.00 – 90,000.00 per month', result['description'])
        self.assertIn('Teach Python', result['description'])
        self.assertIn('hiring@example.com', result['description'])
        self.assertEqual([x['platform'] for x in result['posting_options']], ['LinkedIn', 'Naukri', 'Indeed'])
        self.assertTrue(all(x['status']=='not_published' for x in result['posting_options']))
        self.assertNotIn('sharing/share-offsite', result['posting_options'][0]['url'])

    def test_job_posting_rejects_invalid_salary_and_platforms(self):
        base = dict(job_title='Trainer', company='AIQUBIX', location='Remote', salary_min=100, salary_max=200)
        for changes in ({'salary_min':300}, {'salary_min':-1}, {'salary_max':float('inf')}, {'posting_platforms':[]}, {'posting_platforms':['Unknown']}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.execute('JobPostingAgent', **(base | changes))
        result = self.execute('JobPostingAgent', **(base | {'posting_platforms':['Indeed']}))
        self.assertEqual(len(result['posting_options']), 1)
        self.assertEqual(result['posting_options'][0]['platform'], 'Indeed')

    def test_productivity_uses_full_priorities_and_exact_budget(self):
        result = self.execute('ProductivityCoachAgent', work_hours=2, priorities='Product development, Customer calls')
        self.assertEqual([x['task'] for x in result['daily_schedule']], ['Product development', 'Customer calls'])
        self.assertEqual(sum(x['minutes'] for x in result['daily_schedule']), 120)
        self.assertEqual(result['daily_schedule'][-1]['end'], '11:00')

    def test_fractional_work_hours_and_invalid_hours(self):
        result = self.execute('ProductivityCoachAgent', work_hours=0.25, priorities='A,B')
        self.assertEqual(result['allocated_minutes'], 15)
        for hours in (0, -1, 13, float('nan')):
            with self.subTest(hours=hours), self.assertRaises(ValueError):
                self.execute('ProductivityCoachAgent', work_hours=hours, priorities='A')

    def test_cfo_reconciles_runway_and_forecast(self):
        result = self.execute('CFOAgent', monthly_burn=50000, monthly_revenue=10000, cash_balance=500000)
        self.assertEqual(result['runway_months'], 12.5)
        self.assertEqual(result['cash_flow_forecast'][0]['cash_balance'], 460000)
        self.assertNotIn('survival_probability', result)

    def test_cfo_no_cash_depletion(self):
        for revenue in (100, 200):
            result = self.execute('CFOAgent', monthly_burn=100, monthly_revenue=revenue, cash_balance=1000)
            self.assertIsNone(result['runway_months'])
            json.dumps(result, allow_nan=False)

    def test_resume_results_change_with_requirements(self):
        inputs = {'resumes': 'Alice\nPython React\n---\nBob\nJava Spring'}
        self.assertEqual(self.execute('ResumeScreeningAgent', job_requirements='Python, React', **inputs)['candidates'][0]['name'], 'Alice')
        self.assertEqual(self.execute('ResumeScreeningAgent', job_requirements='Java, Spring', **inputs)['candidates'][0]['name'], 'Bob')

    def test_resume_skill_boundaries_and_no_fake_candidates(self):
        result = self.execute('ResumeScreeningAgent', job_requirements='Java, C++', resumes='Naga\nJavaScript and C++')
        self.assertEqual(result['candidates'][0]['matched_skills'], ['c++'])
        with self.assertRaises(ValueError):
            self.execute('ResumeScreeningAgent', job_requirements='Python', resumes='')

    def test_payslip_respects_gross_and_deductions(self):
        result = self.execute('PayslipAgent', employee_name='<script>alert(1)</script>', salary=50000, deductions=5000)
        self.assertEqual(result['net_pay'], 45000)
        self.assertNotIn('<script>', result['payslip_html'])
        with self.assertRaises(ValueError):
            self.execute('PayslipAgent', employee_name='Naga', salary=100, deductions=200)

    def test_unverified_agents_do_not_invent_evidence(self):
        self.assertIsNone(self.execute('IdeaScoringAgent', idea_name='AI tutor')['score'])
        self.assertIsNone(self.execute('TrademarkAgent', brand_name='AI tutor')['risk_score'])
        result = self.execute('DomainPurchaseAgent', idea='AI Tutor')
        self.assertEqual(result['availability'], 'not_checked')
        self.assertNotIn('available_domains', result)
        self.assertEqual(self.execute('ProblemValidationAgent', problem='Learning')['status'], 'validation_plan')

    def test_tax_uses_supplied_rate_and_clamps_losses(self):
        result = self.execute('TaxFilingAgent', revenue=100, expenses=150, country='India', tax_rate=20)
        self.assertEqual(result['tax_due'], 0)
        result = self.execute('TaxFilingAgent', revenue=1000, expenses=200, country='UK', tax_rate=10)
        self.assertEqual(result['tax_due'], 80)

    def test_content_type_and_mvp_features_affect_results(self):
        result = self.execute('ContentMarketingAgent', topic='Learning', content_type='Case Study')
        self.assertEqual(result['content_type'], 'Case Study')
        self.assertIn('Case study outline', result['content'])
        result = self.execute('MVPBuilderAgent', product_type='AI App', features='OCR, citations')
        self.assertEqual(result['requested_features'], ['OCR', 'citations'])

    def test_trace_history_is_bounded(self):
        tracker = self.demo['arize']
        for i in range(100):
            tracker.start_trace('test', str(i), {})
        self.assertEqual(len(tracker.get_traces()), 50)

    def test_main_innovation_score_reaches_final_score(self):
        scorer = self.main['idea_scorer_tool']
        base = dict(startup_idea='AI tutor', trend_score=50, competitors=[], market_validation={'innovation_score': 0})
        low = json.loads(scorer.invoke(base))
        base['market_validation']['innovation_score'] = 100
        high = json.loads(scorer.invoke(base))
        self.assertEqual(high['final_score'] - low['final_score'], 20)

    def test_main_missing_providers_prevent_score(self):
        result = self.main['idea_evaluation_agent']({'idea_description': 'AI tutor'})
        self.assertEqual(result['current_task'], 'insufficient_evidence')
        self.assertEqual(result['quantitative_score'], 0)
        self.assertIn('No viability score', result['messages'][0].content)

    def test_main_payroll_uses_real_values(self):
        result = self.main['payslip_generator_agent']({'payslip_info': {'employee_name': 'Naga', 'salary': 1000, 'deductions': 100, 'month': 'November 2026'}})
        self.assertEqual(result['payslip_info']['employee'], 'Naga')
        self.assertEqual(result['payslip_info']['net_pay'], 900)

    def test_main_tax_respects_country_and_rate(self):
        result = self.main['tax_filing_agent']({'financial_metrics': {'revenue': 1000, 'expenses': 200, 'tax_rate': 10}, 'ca_info': {'country': 'UK'}})
        self.assertEqual(result['tax_info']['jurisdiction'], 'UK')
        self.assertEqual(result['tax_info']['tax_due'], 80)

    def test_main_domain_does_not_claim_availability(self):
        result = self.main['domain_purchase_agent']({'domain_info': {'name': 'Learnflow'}})
        self.assertIsNone(result['domain_info']['available'])
        self.assertNotIn('example.com', json.dumps(result['domain_info']))

    def test_main_crm_requires_actual_inputs(self):
        with self.assertRaises(ValueError):
            self.main['add_to_crm'].invoke({'lead_name': '', 'email': '', 'stage': 'New', 'score': 0})
        result = json.loads(self.main['add_to_crm'].invoke({'lead_name': 'Naga', 'email': 'naga@example.com', 'stage': 'New', 'score': 80}))
        self.assertEqual(result['status'], 'draft_only')

if __name__ == '__main__':
    unittest.main()
