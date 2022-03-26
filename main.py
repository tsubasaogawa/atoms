from feedgen.feed import FeedGenerator
import html
import json
import markdown
from mdx_gfm import GithubFlavoredMarkdownExtension
import os
import requests


REQUEST_HEADER = {
    'Accept': 'application/vnd.github.v3+json'
}

USER = os.environ['USER']
REPO = os.environ['REPO']

MAX_ISSUE_NUM = int(os.environ.get('MAX_ISSUE_NUM', '10'))
PER_PAGE = int(os.environ.get('PER_PAGE', '30'))
SHORTEN_LENGTH = int(os.environ.get('SHORTEN_LENGTH', '100'))
ATOM_BASE_URL = os.environ.get('ATOM_BASE_URL', '')

REQUEST_URI = f'https://api.github.com/repos/{USER}/{REPO}/issues?per_page={PER_PAGE}'
ALLOW_PR = os.environ.get('ALLOW_PR', 'false').lower() == 'true'


def is_allowed_issue(issue):
    if ALLOW_PR:
        return True

    return 'pull_request' not in issue


def main():
    response = requests.get(REQUEST_URI, headers=REQUEST_HEADER)

    issues = json.loads(response.text)
    target_issues = sorted(
        list(filter(is_allowed_issue, issues)),
        key=lambda x: x['number'],
        reverse=True
    )

    feed_id = f'tag:issue2atom,2006-01-02:/{USER}/{REPO}/issues'

    feed = FeedGenerator()
    feed.id(feed_id)
    feed.title(f'{USER}/{REPO} - GitHub Issues')
    feed.author({'name': USER})
    if ATOM_BASE_URL:
        feed.link(href=f'{ATOM_BASE_URL}/{USER}/{REPO}/atom.xml', rel='self')
    feed.link(href=f'https://github.com/{USER}/{REPO}/issues', rel='alternate')
    # fg.logo('http://ex.com/logo.jpg')
    feed.subtitle(f'GitHub Issues of {USER}/{REPO}')
    feed.language('en')

    for issue in target_issues[0:MAX_ISSUE_NUM]:
        entry = feed.add_entry(order='append')
        entry.id(f'{feed_id}/{issue["number"]}')
        entry.title(issue['title'])
        entry.link(href=issue['html_url'], rel='alternate')
        entry.published(issue['created_at'])
        entry.updated(issue['updated_at'])
        summarized_body = ''.join(issue['body'].splitlines())[:SHORTEN_LENGTH] + '...'
        body_html = html.escape(markdown.markdown(issue['body'], extensions=[GithubFlavoredMarkdownExtension()]), quote=False)
        entry.summary(summarized_body)
        entry.content(content=''.join(body_html.splitlines()), type='html')

    save_dir = f'{USER}/{REPO}'
    atom_file = f'{save_dir}/atom.xml'

    os.makedirs(save_dir, exist_ok=True)
    feed.atom_file(atom_file)

    print(f"::set-output name=status_code::{response.status_code}")
    print(f"::set-output name=atom_file_path::{atom_file}")
    print(f"::set-output name=atom_file_size::{os.path.getsize(atom_file)}")


if __name__ == '__main__':
    main()
