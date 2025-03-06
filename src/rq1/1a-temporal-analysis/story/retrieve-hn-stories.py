import asyncio
import aiohttp
import json
import os
import nest_asyncio
import re
from tqdm.notebook import tqdm

KEYWORDS_TXT = '/content/drive/MyDrive/datasets/muict-naist-senior/rq1/rq1_freq_analysis/rq1_ai_keywords.txt'

# json's
HN_STORIES_JSON = '../../data/hn_stories_dataset_final.json' # contains the raw fetched hn stories and comment ids
HN_STORIES_GH_JSON = '../../data/hn_stories_dataset_gh_final.json'

# csv's
HN_STORIES_CSV = '../../data/hn_stories_dataset_final.csv' # after converting raw json to raw csv
HN_STORIES_GH_CSV = '../../data/hn_stories_dataset_gh_final.csv' # after converting raw json to raw csv

# txt's
KEYWORDS_TXT = 'ai_keywords.txt' # used to match relevant hn stories titles
HN_GITHUB_URLS_TXT = 'hn_github_urls.txt'

# Define the base URL for the Hacker News API
BASE_URL = 'https://hacker-news.firebaseio.com/v0'

# HN stories id's
CHATGPT_RELEASE_ID = 33804874 # nov 30th 2022
START_ID = 31300000 # may 8th 2022
END_ID = 40300000 # may 9th 2024

# dataset retrieval parameters
INCREMENT = 1 # 1: fetch every stories, 2: skip every other stories, 3: skip every 2 stories, etc.
DEPTH = 3 # comments depth, minimum as 1

nest_asyncio.apply()
keywords = []

async def get_top_story_ids(session):
    async with session.get(f'{BASE_URL}/topstories.json') as response:
        return await response.json()

async def get_item(session, item_id):
    async with session.get(f'{BASE_URL}/item/{item_id}.json') as response:
        return await response.json()

def load_progress(dataset_json_filename):
    if os.path.exists(dataset_json_filename):
        with open(dataset_json_filename, 'r') as f:
            return json.load(f)
    return {'processed_story_max_id': -1, 'stories': []}

def save_progress(data, dataset_json_filename):
    with open(dataset_json_filename, 'w') as f:
        json.dump(data, f, indent=4)

async def search_stories(dataset_json_filename, start_id, end_id):
    progress = load_progress(dataset_json_filename)
    progress_story_max_id = progress['processed_story_max_id']
    stories = progress['stories']

    async with aiohttp.ClientSession() as session:
        if progress_story_max_id < 0:
            # Starting from the specified story id until we reached the required quantity
            story_id = start_id
        else:
            # otherwise, start from the last processed story
            story_id = progress_story_max_id

        pbar = tqdm(total=end_id-start_id, desc="Fetching stories")
        pbar.update(story_id-start_id)

        # main loop
        increment = INCREMENT
        while story_id < end_id:
            try:
                # check whether we already retrieved title
                if story_id <= progress_story_max_id:
                    story_id += increment
                    pbar.update(increment)
                    continue

                # get story
                story = await get_item(session, story_id)

                # check whether story exists, if not then skip next time
                if not story or 'title' not in story:
                    story_id += increment
                    progress_story_max_id = story_id
                    pbar.update(increment)
                    continue

                # Minimum score of 20 to ensure that there's enough discussions going on
                if story['score'] < 20:
                    story_id += increment
                    progress_story_max_id = story_id
                    pbar.update(increment)
                    continue

                # check if the story title contains keyword
                title_lower = story['title'].lower()
                for keyword in keywords:
                    pattern = r'\b' + re.escape(keyword.lower()) + r'\b'

                    if re.search(pattern, title_lower):
                        # add to stories
                        stories.append(story)
                        break
                story_id += increment
                progress_story_max_id = story_id
                pbar.update(increment)

                # save progress periodically
                progress['processed_story_max_id'] = progress_story_max_id
                progress['stories'] = stories
                save_progress(progress, dataset_json_filename)

            except Exception as e:
                # Save progress before exiting due to error
                print(f"Error processing story {story_id}: {e}")
                progress['processed_story_max_id'] = progress_story_max_id
                progress['stories'] = stories
                save_progress(progress, dataset_json_filename)
        pbar.close()
    return stories

async def main():
    with open(KEYWORDS_TXT, 'r') as f:
        keywords = [keyword.strip() for keyword in f.readlines()]
    try:
        print(f'Searching for stories containing keywords: {keywords}')
        stories_chatgpt = await search_stories(dataset_json_filename=HN_STORIES_JSON, start_id=START_ID, end_id=END_ID)
        print(f'Found {len(stories_chatgpt)} stories containing keywords.')
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())