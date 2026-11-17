"""Streamlit UI regressions. Uses placeholder keys and never calls hosted models."""
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from streamlit.testing.v1 import AppTest

class InterfaceTests(unittest.TestCase):
    def test_all_extended_agents_and_persistence(self):
        at=AppTest.from_file(str(Path(__file__).with_name('FoundersAgent.py')), default_timeout=15).run()
        assert not at.exception, [x.message for x in at.exception]
        completed=[]
        for category in list(at.selectbox[0].options):
            at.selectbox[0].select(category).run()
            names=[button.key for button in at.button if button.key]
            for name in names:
                at.button(key=name).click().run()
                assert not at.exception, (name, [x.message for x in at.exception])
                for widget in at.text_input:
                    if not widget.value:
                        widget.set_value('Learning assistant')
                for widget in at.text_area:
                    if widget.label == 'Candidate resumes':
                        widget.set_value('Naga\nPython, React, AWS trainer\n---\nOther\nJava developer')
                    elif widget.label == 'Required skills (comma-separated)':
                        widget.set_value('Python, React')
                    elif not widget.value:
                        widget.set_value('Learning, Customer calls')
                if name == 'Job Posting':
                    next(x for x in at.number_input if x.label == 'Minimum salary').set_value(60000.0)
                    next(x for x in at.number_input if x.label == 'Maximum salary').set_value(90000.0)
                    next(x for x in at.selectbox if x.label == 'Salary period').select('month')
                execute=next(button for button in at.button if button.label.startswith('🚀 Execute'))
                execute.click().run()
                assert not at.exception, (name, [x.message for x in at.exception])
                assert not at.error, (name, [x.value for x in at.error])
                assert name in at.session_state['agent_results'], (name,[x.value for x in at.warning])
                if name == 'Job Posting':
                    result = at.session_state['agent_results'][name]
                    assert result['salary']['minimum'] == 60000
                    assert 'per month' in result['description']
                    assert len(at.get('link_button')) == 3
                    assert any(x.label == 'Download job description' for x in at.get('download_button'))
                at.run()
                assert any(x.value == '### Result' for x in at.markdown), (name,'Result disappeared on rerun')
                assert not at.exception, (name, [x.message for x in at.exception])
                completed.append(name)
        print('PASS: all',len(completed),'agent UI flows and report persistence:', ', '.join(completed))
        # A failed rerun must not keep presenting a previous successful report.
        at.selectbox[0].select('HR & People').run()
        at.button(key='Payslip').click().run()
        next(x for x in at.number_input if 'gross' in x.label).set_value(100)
        next(x for x in at.number_input if 'deductions' in x.label).set_value(200)
        next(x for x in at.button if x.label.startswith('🚀 Execute')).click().run()
        assert at.warning and 'Payslip' not in at.session_state['agent_results']
        assert not at.exception
        print('PASS: invalid payroll gives a warning and clears the stale result')

    @patch.dict(os.environ, clear=False)
    def test_ai_job_sections_remain_editable_and_application_field_is_removed(self):
        os.environ['GROQ_API_KEY'] = 'offline-test-placeholder'
        at = AppTest.from_file(str(Path(__file__).with_name('FoundersAgent.py')), default_timeout=20).run()
        at.selectbox[0].select('HR & People').run()
        at.button(key='Job Posting').click().run()
        assert not any(x.label == 'Application email or careers URL' for x in at.text_input)
        with patch('langchain_openai.ChatOpenAI') as client:
            for field, label in [('responsibilities','Role responsibilities'), ('requirements','Required skills and experience'), ('benefits','Benefits offered')]:
                client.return_value.invoke.return_value = SimpleNamespace(content='Draft for ' + field)
                at.button(key='job_ai_' + field).click().run()
                assert not at.exception, [x.message for x in at.exception]
                widget = next(x for x in at.text_area if x.label == label)
                assert 'Draft for ' + field in widget.value
                widget.set_value('My edited ' + field).run()
                assert not at.exception
            for field, label in [('responsibilities','Role responsibilities'), ('requirements','Required skills and experience'), ('benefits','Benefits offered')]:
                assert next(x for x in at.text_area if x.label == label).value == 'My edited ' + field
            client.return_value.invoke.return_value = SimpleNamespace(content='')
            at.button(key='job_ai_requirements').click().run()
            assert at.warning
            assert next(x for x in at.text_area if x.label == 'Required skills and experience').value == 'My edited requirements'
            client.return_value.invoke.side_effect = RuntimeError('private-provider-details')
            at.button(key='job_ai_benefits').click().run()
            assert at.error
            assert 'private-provider-details' not in at.error[0].value
            assert next(x for x in at.text_area if x.label == 'Benefits offered').value == 'My edited benefits'
        next(x for x in at.button if x.label.startswith('🚀 Execute')).click().run()
        assert not at.exception
        description = at.session_state['agent_results']['Job Posting']['description']
        for field in ['responsibilities','requirements','benefits']:
            assert 'My edited ' + field in description
        assert 'How to apply' not in description
        at.run()
        assert not at.exception
        assert next(x for x in at.text_area if x.label == 'Role responsibilities').value == 'My edited responsibilities'

    @patch.dict(os.environ, clear=False)
    def test_ai_job_section_missing_key_preserves_manual_text(self):
        os.environ['GROQ_API_KEY'] = ''
        at = AppTest.from_file(str(Path(__file__).with_name('FoundersAgent.py')), default_timeout=15).run()
        at.selectbox[0].select('HR & People').run()
        at.button(key='Job Posting').click().run()
        next(x for x in at.text_area if x.label == 'Role responsibilities').set_value('Teach Python').run()
        at.button(key='job_ai_responsibilities').click().run()
        assert at.warning
        assert not at.exception
        assert next(x for x in at.text_area if x.label == 'Role responsibilities').value == 'Teach Python'

    @patch.dict(os.environ, clear=False)
    def test_research_offline_flows_and_persistence(self):
        os.environ['GROQ_API_KEY']='offline-test-placeholder'
        for key in ['SERPAPI_API_KEY','TAVILY_API_KEY','EXA_API_KEY']:
            os.environ[key]=''
        for key in ['ALL_PROXY','all_proxy','HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy']:
            os.environ.pop(key,None)
        at=AppTest.from_file(str(Path(__file__).with_name('app.py')), default_timeout=20).run()
        assert not at.exception, [x.message for x in at.exception]
        for name in ['payslip','tax_filing','domain_purchase','idea_evaluation']:
            at.button(key='btn_'+name).click().run()
            assert not at.exception, (name,[x.message for x in at.exception])
            if name=='payslip':
                next(x for x in at.text_input if x.label=='Employee name').set_value('Naga')
                next(x for x in at.number_input if x.label=='Gross salary (USD)').set_value(1000.0)
                next(x for x in at.number_input if x.label=='Total deductions (USD)').set_value(100.0)
            elif name=='tax_filing':
                next(x for x in at.number_input if x.label=='Annual Revenue (USD)').set_value(1000)
                next(x for x in at.number_input if x.label=='Annual Expenses (USD)').set_value(200)
                next(x for x in at.number_input if x.label.startswith('Assumed tax')).set_value(10.0)
                at.selectbox[0].select('UK')
            elif name=='domain_purchase':
                next(x for x in at.text_input if x.label=='Preferred domain base name').set_value('learnflow')
            else:
                at.text_area[0].set_value('Learning assistant')
            next(x for x in at.button if x.label=='🚀 Analyze Now').click().run()
            assert not at.exception, (name,[x.message for x in at.exception])
            assert not at.error, (name,[x.value for x in at.error])
            assert at.session_state['research_report_agent']==name
            if name=='idea_evaluation':
                assert at.session_state['research_report']['current_task']=='insufficient_evidence'
            at.run()
            assert not at.exception
            assert any(x.value=='### Analysis report' for x in at.markdown), (name,'Report disappeared')
            print('PASS:',name,'UI, graph execution, and persistent report')

if __name__ == '__main__':
    unittest.main()
