"""Read-only Reddit keyword trend monitor (personal, non-commercial)."""
import csv, datetime, os, time
import praw, yaml

def main():
    cfg = yaml.safe_load(open(os.environ.get("CONFIG", "config.yaml")))
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
    )
    reddit.read_only = True
    today = datetime.date.today().isoformat()
    limit = cfg.get("limit", 25)
    pause = cfg.get("sleep_seconds", 2)
    os.makedirs("data", exist_ok=True)
    counts, posts = [], []
    for sub in cfg["subreddits"]:
        for kw in cfg["keywords"]:
            n = 0
            for s in reddit.subreddit(sub).search(f'"{kw}"', sort="new", time_filter="day", limit=limit):
                n += 1
                posts.append([sub, kw, s.id, s.title, s.score])  # no usernames stored
            counts.append([today, sub, kw, n])
            time.sleep(pause)
    new = not os.path.exists("data/counts.csv")
    with open("data/counts.csv", "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["date", "subreddit", "keyword", "count"])
        w.writerows(counts)
    with open(f"data/posts_{today}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["subreddit", "keyword", "post_id", "title", "score"]); w.writerows(posts)

if __name__ == "__main__":
    main()
