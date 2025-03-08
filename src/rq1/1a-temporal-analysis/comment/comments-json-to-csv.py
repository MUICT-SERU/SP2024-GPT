import json
import csv
import html
from datetime import datetime
import re
from bs4 import BeautifulSoup

HN_COMMENTS_JSON_INPUT = "data/hn_comments_gh.json"
HN_COMMENTS_CSV_OUTPUT = "data/hn_comments_gh.csv"

def read_json_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def extract_github_urls(text):
    github_url_pattern = r"https://github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-_.]+(?:/(?:issues|pull)/\d+)?"
    return list(set(re.findall(github_url_pattern, text)))

def is_github_repo_or_issue(url):
    if not url.startswith("https://github.com/"):
        return "Not GitHub"
    if "/issues/" in url:
        return "GitHub Issue"
    if "/pull/" in url:
        return "GitHub PR"
    return "GitHub Repo"

def unix_to_datetime(unix_timestamp):
    return datetime.fromtimestamp(unix_timestamp).strftime('%Y-%m-%d %H:%M:%S')

def clean_html(html_text):
    if html_text is None:
        return ''
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text(separator=' ', strip=True)

def flatten_comments(comments, discussion_id, title, url, discussion_date, parent_id=None, depth=0):
    flattened = []
    if not isinstance(comments, list):
        print(f"Warning: comments is not a list. Type: {type(comments)}")
        return flattened

    for i, comment in enumerate(comments):
        if not isinstance(comment, dict):
            print(f"Warning: comment {i} is not a dict. Type: {type(comment)}")
            continue

        comment_id = comment.get('id', '')
        comment_text = comment.get('text')
        if comment_text is None:
            print(f"Warning: comment {comment_id} has None text")
            comment_text = ''
        else:
            comment_text = clean_html(comment_text)
        comment_date = unix_to_datetime(comment.get('time', 0))
        comment_author = comment.get('author', '')

        flattened.append({
            'discussion_id': discussion_id,
            'title': title,
            'url': url,
            'discussion_date': discussion_date,
            'comment_id': comment_id,
            'parent_id': parent_id,
            'depth': depth,
            'comment_text': comment_text,
            'comment_date': comment_date,
            'comment_author': comment_author,
        })

        children = comment.get('children', [])
        if isinstance(children, list):
            flattened.extend(flatten_comments(children, discussion_id, title, url, discussion_date, comment_id, depth + 1))
        else:
            print(f"Warning: children for comment {comment_id} is not a list. Type: {type(children)}")

    return flattened

def process_stories(discussions):
    rows = []
    github_urls = set()

    for i, discussion in enumerate(discussions['stories']):
        discussion_id = discussion.get('id')
        title = discussion.get('title', '')
        url = discussion.get('url', '')
        discussion_date = unix_to_datetime(discussion.get('time', 0))

        print(f"Processing discussion {i+1}: ID {discussion_id}, Title: {title[:30]}...")

        github_urls.update(extract_github_urls(title))
        github_urls.update(extract_github_urls(url))

        comments_hierarchy = discussion.get('kids_text', None)
        if comments_hierarchy is not None:
            # print(f"  Found {len(comments_hierarchy)} top-level comments")
            for j, comment in enumerate(comments_hierarchy):
                comment_text = comment.get('text', 'N/A')
                comment_text_preview = comment_text[:30] if comment_text is not None else 'None'
                # print(f"    Comment {j+1}: ID {comment.get('id', 'N/A')}, Author: {comment.get('author', 'N/A')}, Text: {comment_text_preview}...")
            rows.extend(flatten_comments(comments_hierarchy, discussion_id, title, url, discussion_date))
        else:
            # print("  No comments found for this discussion")
            rows.append({
                'discussion_id': discussion_id,
                'title': title,
                'url': url,
                'discussion_date': discussion_date,
                'comment_id': '',
                'parent_id': '',
                'depth': 0,
                'comment_text': '',
                'comment_date': '',
                'comment_author': '',
            })

    print(f"Processed {len(discussions['stories'])} discussions, found {len(rows)} total comments")
    return rows, github_urls

def write_csv(filename, data, fieldnames):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

hn_comments_data = read_json_file(HN_COMMENTS_JSON_INPUT)

comments_rows, comments_github_urls = process_stories(hn_comments_data)

fieldnames = [
    'discussion_id',
    'title',
    'url',
    'discussion_date',
    'comment_id',
    'parent_id',
    'depth',
    'comment_text',
    'comment_date',
    'comment_author',
]

write_csv(HN_COMMENTS_CSV_OUTPUT, comments_rows, fieldnames)