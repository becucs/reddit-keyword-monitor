"""Read-only Reddit keyword monitor (personal hobby, non-commercial)."""

import csv
import datetime
import os
import time

import praw
import prawcore
import yaml

USER_AGENT = "script:reddit-keyword-monitor:v0.3 (by u/zhangyao_2026)"
POSTS_PREFIX = "posts_"
COUNTS_HEADER = ["date", "subreddit", "phrase", "count"]
POSTS_HEADER = ["post_id", "permalink"]
# Complete approved list from the Data API access request. Nothing else is searched.
APPROVED_TARGETS = {
    "travel": ["visa", "flight"],
    "solotravel": ["SIM card", "itinerary"],
    "chinatravel": ["visa", "payment app"],
    "techsupport": ["not working"],
    "software": ["app recommendation", "alternative to"],
    "technology": ["app recommendation"],
}


def load_config(path=None):
    path = path or os.environ.get("CONFIG", "config.yaml")
    with open(path, encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)
    if cfg.get("targets") != APPROVED_TARGETS:
        raise ValueError(
            "config targets must be the approved six-subreddit phrase mapping"
        )
    return cfg


def make_reddit():
    # Script app, application-only OAuth. reddit.read_only = True is set so
    # the client cannot post, comment, vote, or message even if asked to.
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ.get("REDDIT_USER_AGENT", USER_AGENT),
    )
    reddit.read_only = True
    return reddit


def purge_old_post_ids(data_dir, retention_days):
    """Delete post_id/permalink files that are retention_days old or older."""
    cutoff = datetime.date.today() - datetime.timedelta(days=retention_days)
    if not os.path.isdir(data_dir):
        return
    for name in os.listdir(data_dir):
        if not name.startswith(POSTS_PREFIX) or not name.endswith(".csv"):
            continue
        date_str = name[len(POSTS_PREFIX) : -len(".csv")]
        try:
            file_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            continue
        if file_date <= cutoff:
            os.remove(os.path.join(data_dir, name))


def permalink_url(submission):
    path = submission.permalink
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return "https://www.reddit.com" + path


def search_subreddit(reddit, sub, phrase, limit):
    """One GET /r/{sub}/search (restrict_sr, sort=new, t=day). Retry once on 429."""
    subreddit = reddit.subreddit(sub)

    def _run():
        # PRAW sets restrict_sr=True when the search is on a named subreddit.
        # That is the only Reddit endpoint this script calls.
        return list(
            subreddit.search(
                f'"{phrase}"',
                sort="new",
                time_filter="day",
                limit=limit,
            )
        )

    try:
        return _run()
    except prawcore.exceptions.TooManyRequests:
        time.sleep(60)
        return _run()


def collect_counts(reddit, cfg, today, sleeper=time.sleep):
    """Search each subreddit only for its own phrases. Store counts and ids."""
    limit = cfg.get("limit", 25)
    pause = cfg.get("sleep_seconds", 2)
    counts = []
    posts = []
    first = True
    for sub, phrases in cfg["targets"].items():
        for phrase in phrases:
            if not first:
                sleeper(pause)
            first = False
            submissions = search_subreddit(reddit, sub, phrase, limit)
            counts.append([today, sub, phrase, len(submissions)])
            for submission in submissions:
                posts.append([submission.id, permalink_url(submission)])
    return counts, posts


def write_counts(path, counts):
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(COUNTS_HEADER)
        writer.writerows(counts)


def write_posts(path, posts):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(POSTS_HEADER)
        writer.writerows(posts)


def main():
    cfg = load_config()
    reddit = make_reddit()
    today = datetime.date.today().isoformat()
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    purge_old_post_ids(data_dir, cfg.get("retention_days", 30))
    counts, posts = collect_counts(reddit, cfg, today)
    write_counts(os.path.join(data_dir, "counts.csv"), counts)
    write_posts(os.path.join(data_dir, f"{POSTS_PREFIX}{today}.csv"), posts)


if __name__ == "__main__":
    main()
