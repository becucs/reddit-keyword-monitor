"""reddit-keyword-monitor: personal, non-commercial, READ-ONLY phrase counter.

- Only GET /r/{sub}/search (restrict_sr, sort=new, t=day, limit<=25) via PRAW.
- Hard cap: 20 requests per day (2 runs x 10 searches), enforced locally.
- Stores aggregate daily counts only (date, subreddit, phrase, count).
- post_id/permalink go to a temp file that is purged after 48 hours.
- Never stores titles, bodies, scores, usernames or author IDs.
"""
import csv, datetime, glob, json, os, time
import praw, prawcore, yaml

USER_AGENT = "script:reddit-keyword-monitor:v0.4 (by /u/zhangyao_2026)"
DAILY_CAP = 20
TEMP_RETENTION_HOURS = 48
DATA = "data"
USAGE = os.path.join(DATA, "usage.json")


def purge_temp():
    cutoff = time.time() - TEMP_RETENTION_HOURS * 3600
    for p in glob.glob(os.path.join(DATA, "posts_tmp_*.csv")):
        if os.path.getmtime(p) < cutoff:
            os.remove(p)


def load_usage(today):
    try:
        u = json.load(open(USAGE))
        if u.get("date") == today:
            return u
    except (OSError, ValueError):
        pass
    return {"date": today, "requests": 0}


def main():
    cfg = yaml.safe_load(open(os.environ.get("CONFIG", "config.yaml")))
    os.makedirs(DATA, exist_ok=True)
    purge_temp()
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=USER_AGENT,
    )
    reddit.read_only = True
    today = datetime.date.today().isoformat()
    limit = min(int(cfg.get("limit", 25)), 25)
    pause = cfg.get("sleep_seconds", 2)
    usage = load_usage(today)
    counts, posts = [], []
    stop = False
    for sub, phrases in cfg["targets"].items():
        for phrase in phrases:
            if usage["requests"] >= DAILY_CAP:
                print("Daily cap of", DAILY_CAP, "requests reached; stopping.")
                stop = True
                break
            for attempt in (1, 2):
                usage["requests"] += 1
                try:
                    n = 0
                    for s in reddit.subreddit(sub).search(f'"{phrase}"', sort="new",
                                                          time_filter="day", limit=limit):
                        n += 1
                        posts.append([s.id, "https://www.reddit.com" + s.permalink])
                    counts.append([today, sub, phrase, n])
                    break
                except prawcore.exceptions.TooManyRequests:
                    if attempt == 2 or usage["requests"] >= DAILY_CAP:
                        stop = True
                        break
                    time.sleep(60)
            json.dump(usage, open(USAGE, "w"))
            if stop:
                break
            time.sleep(pause)
        if stop:
            break
    path = os.path.join(DATA, "counts.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "subreddit", "phrase", "count"])
        w.writerows(counts)
    if posts:
        tmp = os.path.join(DATA, f"posts_tmp_{datetime.datetime.now():%Y%m%d%H%M%S}.csv")
        with open(tmp, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["post_id", "permalink"])
            w.writerows(posts)


if __name__ == "__main__":
    main()
