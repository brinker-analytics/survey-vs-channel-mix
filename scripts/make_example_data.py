#!/usr/bin/env python3
"""Seeded generator for the made-up example data. Not from any store or client."""
import csv
import datetime as dt
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "example_data"
random.seed(20261113)
START = dt.date(2026, 8, 3)  # a Monday
DAYS = 12 * 7

# Settings, all made up. The survey weights are the share of answers each label gets.
CHANNELS = {
    "Meta": dict(spend=900, cpm=12.0, orders=30),
    "Google Search": dict(spend=600, cpm=40.0, orders=28),
    "YouTube": dict(spend=300, cpm=14.0, orders=3),
}
SURVEY = {
    "Facebook / Instagram": 0.30,
    "Google search": 0.18,
    "YouTube": 0.16,
    "Podcast": 0.12,
    "Friend or family": 0.14,
    "Other": 0.10,
}
OTHER_TEXT = ["saw it at a market", "a newsletter", "my sister", "a podcast ad I think", "can't remember"]


def main():
    OUT.mkdir(exist_ok=True)
    with open(OUT / "EXAMPLE_channels.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "channel", "spend", "impressions", "attributed_orders"])
        for i in range(DAYS):
            d = START + dt.timedelta(days=i)
            for ch, s in CHANNELS.items():
                spend = s["spend"] * random.uniform(0.8, 1.2)
                imps = int(spend / s["cpm"] * 1000)
                orders = max(0, int(random.gauss(s["orders"], s["orders"] ** 0.5)))
                w.writerow([d.isoformat(), ch, f"{spend:.2f}", imps, orders])
    labels, weights = zip(*SURVEY.items())
    with open(OUT / "EXAMPLE_survey.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "answer", "other_text"])
        for i in range(DAYS):
            d = START + dt.timedelta(days=i)
            for _ in range(random.randint(4, 12)):
                a = random.choices(labels, weights)[0]
                w.writerow([d.isoformat(), a, random.choice(OTHER_TEXT) if a == "Other" else ""])
    with open(OUT / "EXAMPLE_mapping.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["answer", "channel"])
        w.writerow(["Facebook / Instagram", "Meta"])
        w.writerow(["Google search", "Google Search"])
        w.writerow(["YouTube", "YouTube"])


if __name__ == "__main__":
    main()
