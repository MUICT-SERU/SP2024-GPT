import asyncio
import aiohttp
import json
import os
import nest_asyncio
import re
import time
from tqdm import tqdm

# Config paths
KEYWORDS_TXT = './rq1_ai_keywords.txt'
HN_STORIES_JSON = 'non_ai_hn_stories_dataset.json'

# HN API parameters
BASE_URL = 'https://hacker-news.firebaseio.com/v0'
START_ID = 31300000  # May 8th, 2022
END_ID = 40300000    # May 9th, 2024
INCREMENT = 1  # Fetch every story (or skip by N)

# Periodic save checkpoint
SAVE_EVERY = 100

nest_asyncio.apply()

def load_keywords():
    """Load keywords from file and compile regex patterns."""
    with open(KEYWORDS_TXT, 'r') as f:
        keywords = [keyword.strip().lower() for keyword in f.readlines()]
    return [re.compile(r'\b' + re.escape(kw) + r'\b') for kw in keywords]

def load_progress():
    """Load saved progress from JSON, handling potential errors."""
    if os.path.exists(HN_STORIES_JSON):
        try:
            with open(HN_STORIES_JSON, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print("Error loading progress. Starting fresh.")
    return {'processed_story_max_id': START_ID, 'stories': []}

def save_progress(data):
    """Save progress periodically."""
    with open(HN_STORIES_JSON, 'w') as f:
        json.dump(data, f, indent=4)

async def get_item(session, item_id, retries=3):
    """Fetch a Hacker News item with retry logic."""
    url = f'{BASE_URL}/item/{item_id}.json'
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    return await response.json()
        except aiohttp.ClientError:
            print(f"Network error fetching {item_id}, retrying ({attempt+1}/{retries})...")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    return None  # Return None after max retries

async def search_stories():
    """Fetch and filter stories by AI-related keywords."""
    progress = load_progress()
    story_id = max(progress['processed_story_max_id'], START_ID)
    stories = progress['stories']
    keywords = load_keywords()

    async with aiohttp.ClientSession() as session:
        pbar = tqdm(total=END_ID - START_ID, desc="Fetching stories", initial=story_id - START_ID)

        while story_id < END_ID:
            try:
                # Skip already processed stories
                if story_id <= progress['processed_story_max_id']:
                    story_id += INCREMENT
                    pbar.update(INCREMENT)
                    continue

                # Fetch story
                story = await get_item(session, story_id)
                if not story or 'title' not in story or story.get('score', 0) < 20:
                    story_id += INCREMENT
                    continue

                # Check if title matches any AI-related keyword
                title_lower = story['title'].lower()
                if any(pattern.search(title_lower) for pattern in keywords):
                    stories.append(story)

                # Update progress
                progress['processed_story_max_id'] = story_id
                progress['stories'] = stories

                # Periodically save progress
                if len(stories) % SAVE_EVERY == 0:
                    save_progress(progress)

                story_id += INCREMENT
                pbar.update(INCREMENT)

            except Exception as e:
                print(f"Error at {story_id}: {e}")
                save_progress(progress)
                break  # Exit loop on critical failure

        pbar.close()
    return stories

async def main():
    print("Starting story retrieval...")
    stories = await search_stories()
    print(f"Finished! Found {len(stories)} AI-related stories.")

if __name__ == "__main__":
    asyncio.run(main())
