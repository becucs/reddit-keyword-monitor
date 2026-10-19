# reddit-keyword-monitor

A small **personal, non-commercial, read-only** hobby script by u/zhangyao_2026. It counts how often a short, fixed list of general question phrases appears in six public travel/tech subreddits, to help me decide which free travel and everyday-tech FAQs to write. This repository matches my Reddit Data API application (tickets 18619989 / 18616308).

## Targets (complete list)
| Subreddit | Phrases |
|---|---|
| r/travel | "visa", "flight" |
| r/solotravel | "SIM card", "itinerary" |
| r/chinatravel | "visa", "payment app" |
| r/techsupport | "not working" |
| r/software | "app recommendation", "alternative to" |
| r/technology | "app recommendation" |

No health, political, or other sensitive-topic subreddits; no sensitive-trait inference.

## How it works
- PRAW, Reddit **script** app, application-only OAuth, `reddit.read_only = True`.
- Only subreddit search (`GET /r/{sub}/search`, `restrict_sr`, `sort=new`, `t=day`, `limit<=25`).
- User-Agent: `script:reddit-keyword-monitor:v0.4 (by /u/zhangyao_2026)`.
- 10 searches per run, 2 runs/day via cron; **hard cap 20 requests/day** enforced in code.
- 2 s sleep between requests; PRAW honors rate-limit headers; on HTTP 429, sleep 60 s, retry once, then stop the run.

## Data
- `data/counts.csv`: aggregate daily counts only (`date, subreddit, phrase, count`).
- `data/posts_tmp_*.csv`: `post_id, permalink` only, for optional manual review; **purged after 48 hours** (on every run).
- **Never stored:** titles, bodies, scores, usernames, author IDs, media, flair.
- Local files on my computer only; no sharing, no cloud sync of Reddit data.

## What it does NOT do
- No posting, commenting, voting, or messaging (read-only).
- Non-commercial: no resale/licensing/sharing of data, no ads.
- **No AI/ML training** or model input using Reddit content.
- No re-identification of users.

## Usage
```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml
export REDDIT_CLIENT_ID=... REDDIT_CLIENT_SECRET=...   # never commit secrets
python monitor.py
```
Example cron (2 runs/day): `0 9,21 * * * cd /path/to/reddit-keyword-monitor && python monitor.py`

## License
MIT
