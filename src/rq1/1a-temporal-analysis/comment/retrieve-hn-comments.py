import asyncio
import aiohttp
import json
import os
from tqdm.notebook import tqdm

# CSV Paths
HN_STORIES_JSON = './stories_github_valid-13_missing.csv'
HN_COMMENTS_JSON = './comments_github_valid-13_missing.csv'

# Retrieval parameters
INCREMENT = 1 # 1: Fetch every stories, 2: skip every other stories, 3: skip every 2 stories, etc.
DEPTH = 1 # Comments depth, minimum as 1
NUM_KIDS = 100 # Number of maximum comments per story

# Define the base URL for the Hacker News API
BASE_URL = 'https://hacker-news.firebaseio.com/v0'

async def get_top_story_ids(session):
    """Fetches the top story IDs from the Hacker News API."""
    async with session.get(f'{BASE_URL}/topstories.json') as response:
        return await response.json()

async def get_item(session, item_id):
    """Fetches an individual story or comment by ID from the Hacker News API."""
    async with session.get(f'{BASE_URL}/item/{item_id}.json') as response:
        return await response.json()

async def get_kids_hierarchical(session, item, depth=DEPTH):
    """
    Recursively fetches comments (kids) for a given story or comment.

    Parameters:
    - session: aiohttp session for making API requests
    - item: The story or comment object containing 'kids' (child comments)
    - depth: The remaining depth level to fetch comments

    Returns:
    - A hierarchical structure of comments up to the specified depth.
    """
    if 'kids' not in item or depth <= 0:
        return []  # Base case: No kids or max depth reached

    kids_hierarchy = []
    tasks = []

    # Fetch a limited number of child comments in parallel
    for kid_id in item['kids'][:NUM_KIDS]:
        tasks.append(get_item(session, kid_id))

    kids = await asyncio.gather(*tasks)  # Run all fetch tasks concurrently

    # Process each retrieved comment
    for kid in kids:
        if kid:
            kid_data = {
                'id': kid.get('id'),
                'text': kid.get('text'),
                'time': kid.get('time'),
                'author': kid.get('by'),
                'depth': DEPTH - depth + 1,  # Calculate comment depth
                'children': await get_kids_hierarchical(session, kid, depth - 1)  # Recursively fetch child comments
            }
            kids_hierarchy.append(kid_data)

    return kids_hierarchy

def load_progress(filename):
    """
    Loads previously processed story IDs and stored comments from a JSON file.

    Returns:
    - A set of processed story IDs
    - A list of previously processed stories and their comments
    """
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            return set(data.get('processed_story_ids', [])), data.get('stories', [])
    return set(), []  # If file does not exist, return empty data

def save_progress(processed_story_ids, stories, filename):
    """
    Saves the progress of processed story IDs and comments to a JSON file.

    Parameters:
    - processed_story_ids: Set of story IDs that have been processed
    - stories: List of processed stories and their associated comments
    - filename: Destination file to save progress
    """
    with open(filename, 'w') as f:
        json.dump({'processed_story_ids': list(processed_story_ids), 'stories': stories}, f, indent=4)

async def retrieve_stories_comments(stories_source_filename, comments_dest_filename):
    """
    Main function that processes stories and retrieves their comments.

    Parameters:
    - stories_source_filename: JSON file containing the list of stories
    - comments_dest_filename: JSON file to store processed stories and comments

    Returns:
    - List of processed stories with their associated comments
    """
    # Load previously processed story IDs and stored comments
    processed_story_ids, stories_comments_dest = load_progress(comments_dest_filename)

    # Load all available stories from the source JSON file
    stories_source = load_progress(stories_source_filename)[1]  # Load only stories

    total_num_stories = len(stories_source)
    curr_num_stories = len(stories_comments_dest)  # Already processed stories count

    async with aiohttp.ClientSession() as session:
        # Initialize progress bar
        pbar = tqdm(total=total_num_stories, desc="Fetching comments from stories")
        pbar.update(curr_num_stories)

        for story in stories_source:
            story_id = story['id']

            # Skip stories that have already been processed
            if story_id in processed_story_ids:
                continue

            try:
                print(f"Processing story ID: {story_id}")

                # Fetch comments recursively
                story['kids_text'] = await get_kids_hierarchical(session, story, depth=DEPTH)
                stories_comments_dest.append(story)

                # Mark story as processed
                processed_story_ids.add(story_id)

                # Update progress bar and save current progress
                pbar.update(1)
                save_progress(processed_story_ids, stories_comments_dest, comments_dest_filename)
            except Exception as e:
                print(f"Error processing story {story_id}: {e}")
                save_progress(processed_story_ids, stories_comments_dest, comments_dest_filename)  # Save progress even on failure

        pbar.close()  # Close progress bar
    return stories_comments_dest

def count_comments(data):
    return len(data['stories']), sum(len(story['kids_text']) for story in data['stories'])


async def main():
    try:
        # Process the stories and fetch comments
        processed_data = await retrieve_stories_comments(HN_STORIES_JSON, HN_COMMENTS_JSON)

        # Count the number of stories and comments
        with open(HN_COMMENTS_JSON) as f:
            data = json.load(f)
        num_stories, num_comments = count_comments(data)
        print(f"Total number of stories: {num_stories}")
        print(f"Total number of comments: {num_comments}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())