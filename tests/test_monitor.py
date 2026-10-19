"""Checks that the public script matches the Data API application."""
import os, sys, tempfile, time, unittest
import yaml
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import monitor

TARGETS = {
    "travel": ["visa", "flight"],
    "solotravel": ["SIM card", "itinerary"],
    "chinatravel": ["visa", "payment app"],
    "techsupport": ["not working"],
    "software": ["app recommendation", "alternative to"],
    "technology": ["app recommendation"],
}

class Tests(unittest.TestCase):
    def test_config(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cfg = yaml.safe_load(open(os.path.join(root, "config.example.yaml")))
        self.assertEqual(cfg["targets"], TARGETS)

    def test_constants(self):
        self.assertEqual(monitor.DAILY_CAP, 20)
        self.assertEqual(monitor.TEMP_RETENTION_HOURS, 48)
        self.assertEqual(monitor.USER_AGENT, "script:reddit-keyword-monitor:v0.4 (by /u/zhangyao_2026)")

    def test_purge(self):
        with tempfile.TemporaryDirectory() as d:
            monitor.DATA = d
            old, new = os.path.join(d, "posts_tmp_old.csv"), os.path.join(d, "posts_tmp_new.csv")
            for p in (old, new): open(p, "w").close()
            t = time.time() - 49 * 3600
            os.utime(old, (t, t))
            monitor.purge_temp()
            self.assertFalse(os.path.exists(old)); self.assertTrue(os.path.exists(new))

if __name__ == "__main__":
    unittest.main()
