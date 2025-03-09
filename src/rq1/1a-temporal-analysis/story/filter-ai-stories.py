import re
import pandas as pd

stories_df_gh = pd.read_csv('./hn-stories-gh.csv')

def load_keywords():
    """Load keywords from file and compile regex patterns."""
    KEYWORDS_TXT = './rq1_ai_keywords.txt'
    with open(KEYWORDS_TXT, 'r') as f:
        keywords = [keyword.strip().lower() for keyword in f.readlines()]
    return [re.compile(r'\b' + re.escape(kw) + r'\b') for kw in keywords]

keywords = load_keywords()

stories = []
for i, story in stories_df_gh.iterrows():
    title_lower = story['title'].lower()
    if any(pattern.search(title_lower) for pattern in keywords):
        stories.append(story)

stories_df_gh_ai = pd.DataFrame(stories)

# stories_df_gh_ai = stories_df_gh_ai.drop_duplicates(subset=['url'])

stories_df_gh_ai.to_csv('hn-stories-gh-ai.csv', index=False)
print(f"Number of HN GH-AI stories: {len(stories_df_gh_ai)} out of {len(stories_df_gh)}")