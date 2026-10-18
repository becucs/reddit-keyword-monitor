# reddit-keyword-monitor

A small **personal, non-commercial, read-only** hobby script. It counts how often common travel and tech questions appear in a few public subreddits, so I can decide which free guides/FAQs to write.

The script is used only by me. It never posts, comments, votes, messages, or contacts anyone on Reddit.

## What it does
- Uses [PRAW](https://praw.readthedocs.io/) with a Reddit **script-type app**, OAuth **`read` scope only**, and `reddit.read_only = True`. There is no user interface.
- Searches six public subreddits, each only for the one or two general question phrases listed for that subreddit (10 requests per run).
- Intended to run twice a day by cron (about 20 requests a day).
- Stores only **daily aggregate counts** (`date, subreddit, phrase, count`) and, for manual review, **`post_id` plus the permalink**.
- Deletes post IDs and permalinks automatically after 30 days. Only the anonymous daily counts are kept. Titles, usernames, author IDs, post bodies, comments, and media are never stored. Posts are read live on reddit.com.

Example count line: `2026-10-17, solotravel, "SIM card", 6`

## What it does NOT do
- Does not store usernames, author IDs, titles, post bodies, comments, or media.
- Does not post, comment, vote, message, or contact anyone.
- Does not sell, license, or share Reddit data.
- Does not use the data for ads or targeting.
- Does not use Reddit content for AI/ML training, and does not feed Reddit content into any AI model.
- Does not profile users, infer personal or sensitive traits, or attempt re-identification.

## Reddit API compliance
- **Approved access only:** runs only with credentials issued after Reddit approves a Data API access request, under the Data API Terms, Developer Terms, and Responsible Builder Policy.
- **Scope:** script app, OAuth `read` scope, `reddit.read_only = True`. The only endpoint used is subreddit search: `GET /r/{subreddit}/search` with `restrict_sr`, `sort=new`, `t=day`, and `limit≤25`.
- **Targets:** 6 subreddits (r/travel, r/solotravel, r/chinatravel, r/techsupport, r/software, r/technology), each with 1–2 general question phrases (see `config.example.yaml`).
- **Volume:** 10 requests per run, 2 runs a day (about 20 requests a day), with a 2 s sleep between requests and a 60 s back-off on HTTP 429 (one retry). This is far below 100 queries per minute. PRAW also honours Reddit's rate-limit headers.
- **User-Agent:** `script:reddit-keyword-monitor:v0.3 (by u/zhangyao_2026)`
- **Data stored:** aggregate counts plus post IDs and permalinks only. No usernames, author IDs, titles, bodies, or comments.
- **Retention:** post IDs and permalinks are deleted after 30 days (`retention_days`). Content is read live on reddit.com. Because no post text is copied, a post a person deletes on Reddit is not kept here as content.
- **Storage / security:** counts and short-lived post IDs stay in local CSV files on my personal computer (`data/` is gitignored). Credentials come from environment variables and are never committed (`.env` and `config.yaml` are gitignored). Nothing collected is published, shared, or uploaded.
- **Never:** posting, commenting, voting, messaging; resale, licensing, or sharing of Reddit data; ad targeting; AI/ML training or feeding Reddit content into any AI model; user profiling; inferring personal or sensitive traits; re-identification.

## Rate limits
There is a 2-second sleep between requests. PRAW honours Reddit's rate-limit headers. On HTTP 429 the script waits 60 seconds and retries the same request once.

## Usage
```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
export REDDIT_USER_AGENT="script:reddit-keyword-monitor:v0.3 (by u/zhangyao_2026)"
python monitor.py
```

Output:
- `data/counts.csv` — `date, subreddit, phrase, count`
- `data/posts_YYYY-MM-DD.csv` — `post_id, permalink` (removed after 30 days)

To check the script against the approved mapping without calling Reddit:

```bash
python3 -m unittest discover -s tests -v
```

## License
MIT
