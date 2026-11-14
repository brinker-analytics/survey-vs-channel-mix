import csv
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import survey_mix as sm  # noqa: E402

EX = ROOT / "example_data"


def load_example(period="week"):
    mapping = sm.load_mapping(str(EX / "EXAMPLE_mapping.csv"))
    counts, other = sm.survey_counts(sm._read(str(EX / "EXAMPLE_survey.csv"), sm.SURVEY_COLS), mapping, period)
    totals = sm.channel_totals(sm._read(str(EX / "EXAMPLE_channels.csv"), sm.CHANNEL_COLS), period)
    return counts, other, totals


class Shares(unittest.TestCase):
    def setUp(self):
        counts, self.other, totals = load_example()
        self.rows = sm.compare(counts, totals)

    def test_every_answer_counted_once(self):
        n_rows = sum(1 for _ in open(EX / "EXAMPLE_survey.csv")) - 1
        self.assertEqual(sum(r["responses"] for r in self.rows), n_rows)

    def test_comparison_shares_add_to_one_per_period(self):
        by_p = defaultdict(lambda: defaultdict(float))
        for r in self.rows:
            for k in ("survey_share", "spend_share", "impression_share", "attributed_orders_share"):
                if r[k] is not None:
                    by_p[r["period"]][k] += r[k]
        for p, sums in by_p.items():
            for k, v in sums.items():
                self.assertAlmostEqual(v, 1.0, places=9, msg=f"{p} {k}")

    def test_unpaid_answers_kept_but_not_compared(self):
        podcast = [r for r in self.rows if r["channel"] == "Podcast"]
        self.assertTrue(podcast)
        self.assertTrue(all(r["direction"] == "no channel data" for r in podcast))
        self.assertTrue(all(r["share_of_all_answers"] > 0 for r in podcast))

    def test_other_free_text_is_kept(self):
        self.assertTrue(self.other)
        self.assertTrue(all(o["answer"] == "Other" for o in self.other))


class Direction(unittest.TestCase):
    def test_above_below_mixed(self):
        self.assertEqual(sm.direction(0.3, [0.1, 0.2, 0.25]), "above all")
        self.assertEqual(sm.direction(0.1, [0.2, 0.3, 0.15]), "below all")
        self.assertEqual(sm.direction(0.2, [0.1, 0.3, 0.15]), "mixed")

    def test_no_gap_threshold(self):
        # A tiny gap counts the same as a big one; the tool reads consistency, not size.
        self.assertEqual(sm.direction(0.2001, [0.2, 0.2, 0.2]), "above all")


class Signals(unittest.TestCase):
    def rows(self, dirs):
        return [{"channel": "X", "period": f"2026-{i + 1:02d}", "direction": d, "responses": 1}
                for i, d in enumerate(dirs)]

    def test_streak_counts_latest_run(self):
        s = sm.signals(self.rows(["mixed", "above all", "above all", "above all"]))[0]
        self.assertEqual(s["latest_direction"], "above all")
        self.assertEqual(s["periods_in_a_row"], 3)
        self.assertEqual(s["changed_from"], "")

    def test_change_is_flagged(self):
        s = sm.signals(self.rows(["above all", "above all", "below all"]))[0]
        self.assertEqual(s["periods_in_a_row"], 1)
        self.assertEqual(s["changed_from"], "above all")


class Periods(unittest.TestCase):
    def test_week_starts_monday(self):
        import datetime as dt
        self.assertEqual(sm.period_key(dt.date(2026, 11, 13), "week"), "2026-11-09")
        self.assertEqual(sm.period_key(dt.date(2026, 11, 13), "month"), "2026-11")

    def test_missing_columns_stop_the_run(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as f:
            csv.writer(f).writerow(["date", "wrong"])
        with self.assertRaises(SystemExit):
            sm._read(f.name, sm.SURVEY_COLS)


class Cli(unittest.TestCase):
    def test_cli_writes_three_files(self):
        with tempfile.TemporaryDirectory() as d:
            rc = sm.main(["--survey", str(EX / "EXAMPLE_survey.csv"), "--channels", str(EX / "EXAMPLE_channels.csv"),
                          "--mapping", str(EX / "EXAMPLE_mapping.csv"), "--period", "month", "--out", d])
            self.assertEqual(rc, 0)
            for f in ("1_by_period.csv", "2_signals.csv", "3_other_answers.csv"):
                self.assertTrue((Path(d) / f).exists())


if __name__ == "__main__":
    unittest.main()
