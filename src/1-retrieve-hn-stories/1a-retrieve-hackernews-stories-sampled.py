# for running on a screen session

import aiohttp
import json
import os
import re
import asyncio

from tqdm import tqdm

NUM_KIDS = 100 # per story
PROGRESS_FILENAME = 'sampled_hn_stories_dataset.json'
KEYWORDS_FILENAME = 'ai_keywords.txt'
chatgpt_gh_filename = 'github_links_chatgpt.json'
BASE_URL = 'https://hacker-news.firebaseio.com/v0'
CHATGPT_RELEASE_ID = 33804874 # just for reference
START_ID = 31300000 # may 8th 2022
END_ID = 40300000 # may 9th 2024
INCREMENT = 10
DEPTH = 3 # comments depth
THRESHOLD = .5 # threshold for keyword relevance with stories

# retrieve keywords from ai_keywords.txt
keywords = []
with open(KEYWORDS_FILENAME, 'r') as f:
    keywords = [keyword.strip() for keyword in f.readlines()]

async def get_item(session, item_id):
    async with session.get(f'{BASE_URL}/item/{item_id}.json') as response:
        return await response.json()

def load_progress(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {'processed_story_max_id': -1, 'stories': []}

def save_progress(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

async def search_stories(progress_filename, start_id, end_id):
    progress = load_progress(progress_filename)
    progress_story_max_id = progress['processed_story_max_id']
    stories = progress['stories']

    async with aiohttp.ClientSession() as session:
        if progress_story_max_id < 0:
            story_id = start_id
        else:
            story_id = progress_story_max_id

        pbar = tqdm(total=end_id-start_id, desc="Fetching stories")
        pbar.update(story_id-start_id)

        increment = INCREMENT
        while story_id < end_id:
            try:
                if story_id <= progress_story_max_id:
                    story_id += increment
                    pbar.update(increment)
                    continue

                story = await get_item(session, story_id)

                if not story or 'title' not in story:
                    story_id += increment
                    progress_story_max_id = story_id
                    pbar.update(increment)
                    continue

                if story['score'] < 20:
                    story_id += increment
                    progress_story_max_id = story_id
                    pbar.update(increment)
                    continue

                title_lower = story['title'].lower()
                for keyword in keywords:
                    pattern = r'\b' + re.escape(keyword.lower()) + r'\b'

                    if re.search(pattern, title_lower):
                        stories.append(story)
                        break

                story_id += increment
                progress_story_max_id = story_id
                pbar.update(increment)

                progress['processed_story_max_id'] = progress_story_max_id
                progress['stories'] = stories
                save_progress(progress, progress_filename)

            except Exception as e:
                print(f"Error processing story {story_id}: {e}")
                progress['processed_story_max_id'] = progress_story_max_id
                progress['stories'] = stories
                save_progress(progress, progress_filename)

        pbar.close()
    return stories

async def main():
    try:
        stories_chatgpt = await search_stories(progress_filename=PROGRESS_FILENAME, start_id=START_ID, end_id=END_ID)
        print(f'ChatGPT: found {len(stories_chatgpt)} relevant stories')
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())