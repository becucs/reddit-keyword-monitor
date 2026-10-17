# reddit-keyword-monitor

A small **personal, non-commercial, read-only** script for keyword trend monitoring on a few public subreddits.

## What it does
- Uses [PRAW](https://praw.readthedocs.io/) with a Reddit **script-type app**, OAuth **read-only** scope.
- Searches a short, configured list of subreddits for a few keywords, **at most a few times per day**.
- Stores only **aggregate counts per keyword per day**, plus post IDs, titles and scores for manual review.

## What it does NOT do
- Does not store usernames or any personal user data.
- Does not post, comment, vote, or send messages.
- No data resale, no ad targeting, no AI/ML training.

## Rate limits
PRAW's built-in rate limiting is respected, and the script sleeps between requests.

## Usage
```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml
export REDDIT_CLIENT_ID=... REDDIT_CLIENT_SECRET=... REDDIT_USER_AGENT="script:reddit-keyword-monitor:v0.1 (by u/zhangyao_2026)"
python monitor.py
```
Output: `data/counts.csv` (date, subreddit, keyword, count) and `data/posts_YYYY-MM-DD.csv` (post id, title, score).

## License
MIT
