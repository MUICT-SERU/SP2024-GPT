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
    title_lower = str(story['title']).lower()
    if not any(pattern.search(title_lower) for pattern in keywords):
        stories.append(story)

stories_df_gh_nonai = pd.DataFrame(stories)

# stories_df_gh_nonai = stories_df_gh_nonai.drop_duplicates(subset=['url'])

stories_df_gh_nonai.to_csv('hn-stories-gh-nonai.csv', index=False)
print(f"Number of HN GH-nonAI stories: {len(stories_df_gh_nonai)} out of {len(stories_df_gh)}")