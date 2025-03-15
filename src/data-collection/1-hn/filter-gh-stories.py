import csv
from urllib.parse import urlparse, unquote

def is_github_repo_url(url):
    """
    Check if a URL is a GitHub repository root URL.
    Returns True for URLs like 'https://github.com/username/repository'
    Returns False for URLs pointing to specific files, commits, pulls, gists, etc.
    """
    try:
        # Parse the URL
        parsed = urlparse(unquote(url))

        # Check if it's a GitHub URL
        if parsed.netloc != 'github.com':
            return False

        # Split the path into components
        parts = [p for p in parsed.path.split('/') if p]

        # A valid repo URL should have exactly 2 parts (username/repository)
        if len(parts) != 2:
            return False

        # Check for specific patterns that indicate non-repository URLs
        non_repo_patterns = [
            r'/blob/',
            r'/tree/',
            r'/commit/',
            r'/pull/',
            r'/issues/',
            r'/releases/',
            r'/actions/',
            r'/wiki/',
            r'/settings/',
            r'/branches/'
        ]

        return not any(pattern in url for pattern in non_repo_patterns)

    except Exception:
        return False

def filter_github_urls(input_file, output_file, url_column):
    """
    Filter CSV file to keep only rows with valid GitHub repository URLs.

    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file
        url_column (str): Name of the column containing URLs
    """
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        # Verify URL column exists
        if url_column not in reader.fieldnames:
            raise ValueError(f"Column '{url_column}' not found in CSV file")

        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            writer.writeheader()

            for row in reader:
                url = row[url_column].strip()
                if is_github_repo_url(url):
                    writer.writerow(row)

HN_STORIES_CSV_INPUT = './hn-stories-all.csv'
HN_STORIES_GH_CSV_OUTPUT = './hn-stories-gh.csv'
url_column = "url"  # Change this to match your CSV column name

filter_github_urls(HN_STORIES_CSV_INPUT, HN_STORIES_GH_CSV_OUTPUT, url_column)