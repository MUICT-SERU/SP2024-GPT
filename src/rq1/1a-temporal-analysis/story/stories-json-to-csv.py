from datetime import datetime
import csv
import random
import re
import json
from bs4 import BeautifulSoup

HN_STORIES_JSON_INPUT = 'hn_stories_2020-01-01_2020-12-31.json'
HN_STORIES_CSV_OUTPUT = 'hn_stories_2020-01-01_2020-12-31.csv'

def read_json_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def extract_github_urls(text):
    github_url_pattern = r"https://github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-_.]+(?:/(?:issues|pull)/\d+)?"
    return list(set(re.findall(github_url_pattern, text)))

def unix_to_datetime(unix_timestamp):
    return datetime.fromtimestamp(unix_timestamp)

def clean_html(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text(separator=' ', strip=True)

def process_stories(posts):
    rows = []

    for post in posts:
        post_id = post.get('id')
        title = post.get('title', '')
        url = post.get('url', '')
        date = (post.get('time', 0))

        rows.append({
            'discussion_id': post_id,
            'title': title,
            'url': url,
            'date': date,
        })

    return rows

def write_csv(filename, data, fieldnames):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

hn_stories_data = read_json_file(HN_STORIES_JSON_INPUT)
print(f"ChatGPT stories: {len(hn_stories_data['stories'])}")

chatgpt_rows = process_stories(hn_stories_data['stories'])
print(f"Total rows: {len(chatgpt_rows)}")

# Write to CSV files
fieldnames = ['discussion_id', 'title', 'url', 'date', ]

# # Write raw dataset
write_csv(HN_STORIES_CSV_OUTPUT, chatgpt_rows, fieldnames)