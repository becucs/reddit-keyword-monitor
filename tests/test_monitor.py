"""Checks that the public script matches the Data API reapplication claims."""

import datetime
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import prawcore
import yaml

import monitor


FORM_TARGETS = {
    "travel": ["visa", "flight"],
    "solotravel": ["SIM card", "itinerary"],
    "chinatravel": ["visa", "payment app"],
    "techsupport": ["not working"],
    "software": ["app recommendation", "alternative to"],
    "technology": ["app recommendation"],
}

class ConfigMatchesFormTests(unittest.TestCase):
    def test_example_config_is_the_form_mapping(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "config.example.yaml"), encoding="utf-8") as handle:
            cfg = yaml.safe_load(handle)
        self.assertEqual(cfg["targets"], FORM_TARGETS)
        self.assertEqual(monitor.APPROVED_TARGETS, FORM_TARGETS)
        self.assertEqual(sum(len(phrases) for phrases in cfg["targets"].values()), 10)
        self.assertEqual(cfg["limit"], 25)
        self.assertEqual(cfg["sleep_seconds"], 2)
        self.assertEqual(cfg["retention_days"], 30)

    def test_load_config_rejects_unapproved_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.yaml")
            extra = dict(FORM_TARGETS)
            extra["travel"] = ["visa", "flight", "extra"]
            with open(path, "w", encoding="utf-8") as handle:
                yaml.safe_dump({"targets": extra, "limit": 25}, handle)
            with self.assertRaises(ValueError):
                monitor.load_config(path)


class RetentionTests(unittest.TestCase):
    def test_deletes_post_files_30_days_old_or_older(self):
        today = datetime.date.today()
        with tempfile.TemporaryDirectory() as tmp:
            keep = os.path.join(tmp, f"posts_{(today - datetime.timedelta(days=29)).isoformat()}.csv")
            drop_exact = os.path.join(tmp, f"posts_{(today - datetime.timedelta(days=30)).isoformat()}.csv")
            drop_older = os.path.join(tmp, f"posts_{(today - datetime.timedelta(days=45)).isoformat()}.csv")
            counts = os.path.join(tmp, "counts.csv")
            for path in (keep, drop_exact, drop_older, counts):
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write("post_id,permalink\n")
            monitor.purge_old_post_ids(tmp, 30)
            self.assertTrue(os.path.exists(keep))
            self.assertFalse(os.path.exists(drop_exact))
            self.assertFalse(os.path.exists(drop_older))
            self.assertTrue(os.path.exists(counts))


class CollectCountsTests(unittest.TestCase):
    def test_searches_only_each_subreddits_own_phrases(self):
        reddit = MagicMock()
        calls = []

        def fake_search(reddit_obj, sub, phrase, limit):
            calls.append((sub, phrase, limit))
            return [SimpleNamespace(id=f"{sub}-{phrase}", permalink=f"/r/{sub}/comments/abc/")]

        cfg = {
            "targets": FORM_TARGETS,
            "limit": 25,
            "sleep_seconds": 2,
        }
        sleeps = []
        with patch.object(monitor, "search_subreddit", side_effect=fake_search):
            counts, posts = monitor.collect_counts(
                reddit, cfg, "2026-10-17", sleeper=lambda seconds: sleeps.append(seconds)
            )

        self.assertEqual(calls, [(sub, phrase, 25) for sub, phrases in FORM_TARGETS.items() for phrase in phrases])
        self.assertEqual(len(calls), 10)
        self.assertEqual(sleeps, [2] * 9)
        self.assertEqual(counts[2], ["2026-10-17", "solotravel", "SIM card", 1])
        self.assertEqual(posts[0], ["travel-visa", "https://www.reddit.com/r/travel/comments/abc/"])
        self.assertTrue(all(len(row) == 2 for row in posts))

    def test_retries_once_after_429(self):
        reddit = MagicMock()
        search = MagicMock(
            side_effect=[
                prawcore.exceptions.TooManyRequests(MagicMock(headers={"retry_after": "60"})),
                [SimpleNamespace(id="abc", permalink="/r/travel/comments/abc/")],
            ]
        )
        reddit.subreddit.return_value.search = search
        with patch.object(monitor.time, "sleep") as sleep:
            results = monitor.search_subreddit(reddit, "travel", "visa", 25)
        sleep.assert_called_once_with(60)
        self.assertEqual(search.call_count, 2)
        self.assertEqual(results[0].id, "abc")
        _, kwargs = search.call_args
        self.assertEqual(kwargs["sort"], "new")
        self.assertEqual(kwargs["time_filter"], "day")
        self.assertEqual(kwargs["limit"], 25)


class WriteShapeTests(unittest.TestCase):
    def test_post_csv_has_only_id_and_permalink(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "posts_2026-10-17.csv")
            monitor.write_posts(path, [["abc123", "https://www.reddit.com/r/travel/comments/abc123/"]])
            with open(path, encoding="utf-8") as handle:
                header = handle.readline().strip().split(",")
            self.assertEqual(header, ["post_id", "permalink"])
            self.assertNotIn("title", header)
            self.assertNotIn("score", header)
            self.assertNotIn("author", header)


class UserAgentTests(unittest.TestCase):
    def test_default_user_agent_matches_form(self):
        self.assertEqual(
            monitor.USER_AGENT,
            "script:reddit-keyword-monitor:v0.3 (by u/zhangyao_2026)",
        )


if __name__ == "__main__":
    unittest.main()
