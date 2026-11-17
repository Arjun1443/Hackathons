"""Offline tests. No LinkedIn, Indeed, or Naukri accounts are contacted."""
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import requests
from streamlit.testing.v1 import AppTest
from job_publishing import publish_linkedin_post, PublishingError, PublishingUncertain, publication_fingerprint

class FakeHTTP:
    def __init__(self, status=201, post_id='urn:li:share:123456', exception=None):
        self.status, self.post_id, self.exception = status, post_id, exception
        self.calls = []
    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.exception:
            raise self.exception
        return SimpleNamespace(status_code=self.status, headers={'x-restli-id':self.post_id} if self.post_id else {})

class PublishingTests(unittest.TestCase):
    def test_posts_exact_reviewed_text_once_to_official_endpoint(self):
        http = FakeHTTP()
        result = publish_linkedin_post('We are hiring a Python trainer.', 'private-token', 'urn:li:person:abc123', http=http)
        self.assertEqual(result['status'], 'published')
        self.assertEqual(len(http.calls), 1)
        url, kwargs = http.calls[0]
        self.assertEqual(url, 'https://api.linkedin.com/rest/posts')
        self.assertEqual(kwargs['json']['commentary'], 'We are hiring a Python trainer.')
        self.assertEqual(kwargs['json']['author'], 'urn:li:person:abc123')
        self.assertFalse(kwargs['allow_redirects'])
        self.assertEqual(kwargs['headers']['LinkedIn-Version'], '202606')
        self.assertNotIn('private-token', json.dumps(result))

    def test_rejects_invalid_inputs_without_sending(self):
        for text, token, author in [('', 'token', 'urn:li:person:abc'), ('x'*3001, 'token', 'urn:li:person:abc'), ('text', '', 'urn:li:person:abc'), ('text','token','urn:li:organization:123')]:
            http = FakeHTTP()
            with self.subTest(author=author), self.assertRaises(PublishingError):
                publish_linkedin_post(text, token, author, http=http)
            self.assertEqual(http.calls, [])

    def test_errors_do_not_claim_publication_or_expose_tokens(self):
        for status in (400,401,403,429,302):
            with self.subTest(status=status), self.assertRaises(PublishingError) as error:
                publish_linkedin_post('Text', 'private-token', 'urn:li:person:abc', http=FakeHTTP(status=status))
            self.assertNotIn('private-token', str(error.exception))

    def test_uncertain_outcomes_never_retry_automatically(self):
        cases = [FakeHTTP(exception=requests.Timeout('private-token')), FakeHTTP(status=503), FakeHTTP(post_id=None)]
        for http in cases:
            with self.assertRaises(PublishingUncertain):
                publish_linkedin_post('Text', 'private-token', 'urn:li:person:abc', http=http)
            self.assertEqual(len(http.calls), 1)

    def test_fingerprints_distinguish_author_and_content(self):
        self.assertEqual(publication_fingerprint('a','text'), publication_fingerprint('a',' text '))
        self.assertNotEqual(publication_fingerprint('a','text'), publication_fingerprint('b','text'))
        self.assertNotEqual(publication_fingerprint('a','text'), publication_fingerprint('a','other'))

    def composer(self):
        at = AppTest.from_file(str(Path(__file__).with_name('FoundersAgent.py')), default_timeout=20).run()
        at.selectbox[0].select('HR & People').run()
        at.button(key='Job Posting').click().run()
        next(x for x in at.button if x.label.startswith('🚀 Execute')).click().run()
        self.assertFalse(at.exception, [x.message for x in at.exception])
        return at

    def test_linkedin_preview_uses_personal_voice(self):
        at = self.composer()
        self.assertTrue(next(x for x in at.text_area if x.label=='Post content').value.startswith("I'm hiring:"))
        self.assertEqual(at.button(key='publish_LinkedIn').label, 'Post from my LinkedIn profile')
        self.assertTrue(any('Your personal LinkedIn profile' in x.value for x in at.caption))
        next(x for x in at.selectbox if x.label=='Post preview platform').select('Indeed').run()
        self.assertTrue(next(x for x in at.text_area if x.label=='Post content').value.startswith("We're hiring:"))

    def test_preview_publishes_only_on_click_and_prevents_duplicate(self):
        at = self.composer()
        self.assertTrue(at.button(key='publish_LinkedIn').disabled)
        next(x for x in at.text_area if x.label=='Post content').set_value('My reviewed hiring post').run()
        next(x for x in at.text_input if x.label=='LinkedIn OAuth access token').set_value('private-session-token')
        next(x for x in at.text_input if x.label=='LinkedIn Person URN').set_value('urn:li:person:abc123')
        with patch('job_publishing.publish_linkedin_post', return_value={'status':'published','post_id':'urn:li:share:123','post_url':'https://www.linkedin.com/feed/update/urn:li:share:123/'}) as publish:
            at.run()
            publish.assert_not_called()
            at.button(key='publish_LinkedIn').click().run()
            self.assertFalse(at.exception, [x.message for x in at.exception])
            self.assertEqual(publish.call_count,1)
            self.assertEqual(publish.call_args.args[0], 'My reviewed hiring post')
            self.assertEqual(publish.call_args.args[1], 'private-session-token')
            at.run()
            self.assertEqual(publish.call_count,1)
            self.assertTrue(at.button(key='publish_LinkedIn').disabled)
        exported = json.dumps(at.session_state['agent_results']['Job Posting'])
        self.assertNotIn('private-session-token', exported)
        next(x for x in at.button if x.label=='Clear LinkedIn credentials').click().run()
        self.assertFalse(next(x for x in at.text_input if x.label=='LinkedIn OAuth access token').value)

    def test_platform_previews_preserve_edits_and_disable_unconnected_posting(self):
        at = self.composer()
        next(x for x in at.text_area if x.label=='Post content').set_value('LinkedIn edited').run()
        next(x for x in at.selectbox if x.label=='Post preview platform').select('Indeed').run()
        self.assertTrue(at.button(key='publish_Indeed').disabled)
        next(x for x in at.text_area if x.label=='Post content').set_value('Indeed edited').run()
        next(x for x in at.selectbox if x.label=='Post preview platform').select('Naukri').run()
        self.assertTrue(at.button(key='publish_Naukri').disabled)
        next(x for x in at.selectbox if x.label=='Post preview platform').select('LinkedIn').run()
        self.assertEqual(next(x for x in at.text_area if x.label=='Post content').value, 'LinkedIn edited')
        self.assertFalse(at.exception)

    def test_timeout_requires_manual_resolution_before_another_attempt(self):
        at = self.composer()
        next(x for x in at.text_input if x.label=='LinkedIn OAuth access token').set_value('private-session-token')
        next(x for x in at.text_input if x.label=='LinkedIn Person URN').set_value('urn:li:person:abc123')
        at.run()
        with patch('job_publishing.publish_linkedin_post', side_effect=PublishingUncertain('Check your feed')) as publish:
            at.button(key='publish_LinkedIn').click().run()
            at.run()
            self.assertEqual(publish.call_count,1)
            self.assertTrue(at.button(key='publish_LinkedIn').disabled)
            self.assertTrue(any('previous request' in x.value.lower() for x in at.warning))

if __name__ == '__main__':
    unittest.main()
