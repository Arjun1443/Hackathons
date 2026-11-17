"""LinkedIn feed publishing. No account credentials are stored by this module.

Official API reference:
https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
"""
import hashlib
import re
from urllib.parse import quote


class PublishingError(Exception):
    """A known API failure, safe to show without exposing credentials."""


class PublishingUncertain(PublishingError):
    """The request may have reached the platform. Never automatically retry."""


def publication_fingerprint(author, text):
    return hashlib.sha256((author.strip() + '\0' + text.strip()).encode()).hexdigest()


def publish_linkedin_post(text, access_token, author_urn, api_version='202606', *, http=None):
    """Publish the exact reviewed text after an explicit button click.

    This creates a feed post, not a listing in LinkedIn Jobs. HTTP transport is
    injectable for offline tests. No retries or redirects send a second POST.
    """
    import requests
    text = str(text).strip()
    token = str(access_token).strip()
    author = str(author_urn).strip()
    version = str(api_version).strip()
    if not token:
        raise PublishingError('Connect a LinkedIn OAuth access token first. A Groq key cannot publish to LinkedIn.')
    if not re.fullmatch(r'urn:li:person:[A-Za-z0-9_-]+', author):
        raise PublishingError('Enter the Person URN for the LinkedIn member who authorized this token.')
    if not text or len(text) > 3000:
        raise PublishingError('The LinkedIn post must contain between 1 and 3,000 characters.')
    if not re.fullmatch(r'20\d{2}(0[1-9]|1[0-2])', version):
        raise PublishingError('LinkedIn API version must use YYYYMM format.')
    payload = {
        'author': author,
        'commentary': text,
        'visibility': 'PUBLIC',
        'distribution': {'feedDistribution': 'MAIN_FEED', 'targetEntities': [], 'thirdPartyDistributionChannels': []},
        'lifecycleState': 'PUBLISHED',
        'isReshareDisabledByAuthor': False,
    }
    transport = http or requests
    try:
        response = transport.post(
            'https://api.linkedin.com/rest/posts',
            headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'LinkedIn-Version': version, 'X-Restli-Protocol-Version': '2.0.0'},
            json=payload, timeout=25, allow_redirects=False,
        )
    except requests.RequestException:
        raise PublishingUncertain('The request outcome is unknown. Check your LinkedIn feed before retrying to avoid a duplicate post.') from None
    if response.status_code == 201:
        post_id = response.headers.get('x-restli-id')
        if not post_id:
            raise PublishingUncertain('LinkedIn accepted the request but returned no post ID. Check your feed before retrying.')
        post_url = None
        if re.fullmatch(r'urn:li:(?:share|ugcPost):\d+', post_id):
            post_url = 'https://www.linkedin.com/feed/update/' + quote(post_id, safe=':') + '/'
        return {'status': 'published', 'platform': 'LinkedIn', 'post_id': post_id, 'post_url': post_url}
    if response.status_code == 401:
        raise PublishingError('LinkedIn rejected the token. Reauthorize your LinkedIn account and enter a valid access token.')
    if response.status_code == 403:
        raise PublishingError('LinkedIn denied publishing permission. Your app/token needs w_member_social and access to this API for the specified member.')
    if response.status_code == 429:
        raise PublishingError('LinkedIn rate-limited this request. Wait before trying again.')
    if response.status_code >= 500:
        raise PublishingUncertain('LinkedIn returned a server error. Check your feed before retrying because the publication outcome is unknown.')
    raise PublishingError(f'LinkedIn did not confirm publication (HTTP {response.status_code}). Check your app permissions, API version, and post content.')


def clear_linkedin_credentials(state):
    state.pop('linkedin_access_token', None)
    state.pop('linkedin_author_urn', None)


def render_job_post_composer(result, selected_platform=None):
    """Render editable platform previews and an explicit, account-scoped publisher."""
    import streamlit as st
    platforms = [item['platform'] for item in result.get('posting_options', [])]
    if not platforms:
        return
    if selected_platform in platforms:
        st.session_state['job_compose_platform'] = selected_platform
    if st.session_state.get('job_compose_platform') not in platforms:
        st.session_state['job_compose_platform'] = platforms[0]
    platform = st.selectbox('Post preview platform', platforms, key='job_compose_platform')
    source = result['description']
    source_hash = hashlib.sha256(source.encode()).hexdigest()
    editor_key = 'posting_text_' + platform
    drafts = st.session_state.setdefault('job_platform_drafts', {})
    if drafts.get(platform, {}).get('source_hash') != source_hash:
        drafts[platform] = {'source_hash': source_hash, 'text': source}
        st.session_state[editor_key] = source
    elif editor_key not in st.session_state:
        # Streamlit removes widget state when another platform hides its editor.
        st.session_state[editor_key] = drafts[platform]['text']
    st.markdown('#### Ready-to-review ' + platform + ' post')
    text = st.text_area('Post content', key=editor_key, height=320)
    drafts[platform]['text'] = text
    st.caption('Your edits here are the exact text submitted by the publishing button.')
    st.download_button('Download this post', text, platform.lower() + '_job_post.txt', mime='text/plain')
    if platform != 'LinkedIn':
        if platform == 'Indeed':
            st.info('Indeed publishing is not connected. It requires an approved employer/ATS Job Sync integration and OAuth credentials. No job has been submitted.')
        else:
            st.info('Naukri publishing is not connected. Obtain employer posting API access and integration details from your Naukri account manager. No job has been submitted.')
        st.button('Post to ' + platform, disabled=True, key='publish_' + platform)
        return
    st.caption('Publishes a public hiring post to your LinkedIn member feed. LinkedIn Jobs listings and company-page publishing require separate integrations.')
    with st.expander('Connect your LinkedIn member account'):
        st.markdown('Use a LinkedIn Developer app with **Share on LinkedIn** and a member-authorized token with **w_member_social**. This is a LinkedIn credential, separate from Groq. Never enter your LinkedIn password.')
        st.link_button('LinkedIn authorization setup', 'https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin')
        st.button('Clear LinkedIn credentials', on_click=clear_linkedin_credentials, args=(st.session_state,))
        token = st.text_input('LinkedIn OAuth access token', type='password', key='linkedin_access_token')
        author = st.text_input('LinkedIn Person URN', placeholder='urn:li:person:YOUR_MEMBER_ID', key='linkedin_author_urn')
        version = st.text_input('LinkedIn API version', value='202606', key='linkedin_post_api_version')
        st.caption('Credentials stay in this browser session and are excluded from reports, traces, and downloads. They are not validated until you submit a post.')
    attempts = st.session_state.setdefault('linkedin_publication_attempts', {})
    fingerprint = publication_fingerprint(author, text)
    previous = attempts.get(fingerprint)
    if previous and previous['status'] == 'published':
        st.success('LinkedIn confirmed publication of this exact post.')
        if previous.get('post_url'):
            st.link_button('View published LinkedIn post', previous['post_url'])
    elif previous and previous['status'] in ('pending', 'uncertain'):
        st.warning('A previous request may have published this post. Check your LinkedIn feed before retrying.')
        if st.checkbox('I checked my LinkedIn feed and confirmed this post was not published', key='resolve_' + fingerprint):
            if st.button('Allow one retry', key='retry_' + fingerprint):
                attempts.pop(fingerprint, None)
                previous = None
    disabled = not token.strip() or not author.strip() or not text.strip() or len(text.strip()) > 3000 or previous is not None
    st.caption(f'{len(text.strip()):,} / 3,000 characters')
    if st.button('Post to LinkedIn feed', key='publish_LinkedIn', disabled=disabled):
        # The attempt precedes the request. Reruns cannot silently resubmit it.
        attempts[fingerprint] = {'status': 'pending'}
        try:
            with st.spinner('Publishing to LinkedIn...'):
                publication = publish_linkedin_post(text, token, author, version)
            attempts[fingerprint] = publication
            st.success('LinkedIn confirmed publication.')
            if publication.get('post_url'):
                st.link_button('View published LinkedIn post', publication['post_url'])
        except PublishingUncertain as exc:
            attempts[fingerprint] = {'status': 'uncertain'}
            st.warning(str(exc))
        except PublishingError as exc:
            attempts.pop(fingerprint, None)
            st.error(str(exc))
        except Exception:
            attempts[fingerprint] = {'status': 'uncertain'}
            st.error('Could not confirm publication. Check LinkedIn before trying again.')
