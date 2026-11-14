#!/usr/bin/env python3
"""Compare post-purchase survey answers with spend share, impression share and attributed orders.

Standard library only. It shows, period by period, whether each channel's share of
survey answers sits above or below all three of its other shares, and how many
periods in a row that has held. It sets no numeric gap that "triggers" a test:
survey answers swing without statistical confidence, so the thing to look for is
a change, or a consistency that keeps recurring.

By Eric Brinker, Brinker Analytics (https://brinkeranalytics.com). MIT license.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

SURVEY_COLS = ["date", "answer"]
CHANNEL_COLS = ["date", "channel", "spend", "impressions", "attributed_orders"]
MAPPING_COLS = ["answer", "channel"]
OTHER = "Other"
MEASURES = ("spend", "impressions", "attributed_orders")


def _parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s.strip()[:10])


def period_key(d: dt.date, period: str) -> str:
    if period == "month":
        return f"{d.year:04d}-{d.month:02d}"
    if period == "week":
        monday = d - dt.timedelta(days=d.weekday())
        return monday.isoformat()
    raise ValueError("period must be 'week' or 'month'")


def _read(path: str, required: List[str]) -> List[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        missing = [c for c in required if c not in (r.fieldnames or [])]
        if missing:
            sys.exit(f"{path}: missing columns {missing}")
        return list(r)


def load_mapping(path: Optional[str]) -> Dict[str, str]:
    if not path:
        return {}
    return {row["answer"].strip(): row["channel"].strip() for row in _read(path, MAPPING_COLS)}


def survey_counts(rows: List[dict], mapping: Dict[str, str], period: str
                  ) -> Tuple[Dict[str, Dict[str, int]], List[dict]]:
    """Responses per period per channel. Unmapped answers keep their own label; blanks go to Other."""
    counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    other_text: List[dict] = []
    for row in rows:
        p = period_key(_parse_date(row["date"]), period)
        ans = (row.get("answer") or "").strip() or OTHER
        ch = mapping.get(ans, ans)
        counts[p][ch] += 1
        txt = (row.get("other_text") or "").strip()
        if txt:
            other_text.append({"period": p, "answer": ans, "other_text": txt})
    return counts, other_text


def channel_totals(rows: List[dict], period: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    tot: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for row in rows:
        p = period_key(_parse_date(row["date"]), period)
        ch = row["channel"].strip()
        for m in MEASURES:
            v = (row.get(m) or "").strip()
            tot[p][ch][m] += float(v) if v else 0.0
    return tot


def _share(part: float, whole: float) -> Optional[float]:
    return part / whole if whole > 0 else None


def direction(survey_share: float, others: List[Optional[float]]) -> str:
    """'above' if the survey share is above every comparison share, 'below' if below every one."""
    known = [o for o in others if o is not None]
    if not known:
        return "no channel data"
    if all(survey_share > o for o in known):
        return "above all"
    if all(survey_share < o for o in known):
        return "below all"
    return "mixed"


def compare(counts, totals) -> List[dict]:
    periods = sorted(set(counts) | set(totals))
    out = []
    for p in periods:
        n = sum(counts.get(p, {}).values())
        chans = set(counts.get(p, {})) | set(totals.get(p, {}))
        whole = {m: sum(totals.get(p, {}).get(c, {}).get(m, 0.0) for c in chans) for m in MEASURES}
        paid = set(totals.get(p, {}))
        n_paid = sum(v for c, v in counts.get(p, {}).items() if c in paid)
        for c in sorted(chans):
            resp = counts.get(p, {}).get(c, 0)
            in_data = c in paid
            # Compare like with like: a channel's share of the answers that name a channel
            # in the spend data, against its share of that same set of channels' spend.
            s_share = _share(resp, n_paid) if in_data else None
            shares = {m: (_share(totals[p][c][m], whole[m]) if in_data else None) for m in MEASURES}
            out.append({
                "period": p,
                "channel": c,
                "responses": resp,
                "period_responses": n,
                "share_of_all_answers": _share(resp, n),
                "survey_share": s_share,
                "spend_share": shares["spend"],
                "impression_share": shares["impressions"],
                "attributed_orders_share": shares["attributed_orders"],
                "direction": ("no channel data" if not in_data else
                              "no responses" if s_share is None else
                              direction(s_share, list(shares.values()))),
            })
    return out


def signals(rows: List[dict]) -> List[dict]:
    """Per channel: the latest direction, how many periods in a row it has held, and whether it just changed."""
    by_ch: Dict[str, List[dict]] = defaultdict(list)
    for r in rows:
        by_ch[r["channel"]].append(r)
    out = []
    for c, rs in sorted(by_ch.items()):
        rs.sort(key=lambda r: r["period"])
        dirs = [r["direction"] for r in rs]
        latest = dirs[-1]
        streak = 1
        for d in reversed(dirs[:-1]):
            if d != latest:
                break
            streak += 1
        prior = dirs[-1 - streak] if len(dirs) > streak else None
        same_count = sum(1 for d in dirs if d == latest)
        out.append({
            "channel": c,
            "periods": len(dirs),
            "latest_direction": latest,
            "periods_in_a_row": streak,
            "periods_with_this_direction": same_count,
            "changed_from": prior if streak == 1 and prior is not None else "",
            "total_responses": sum(r["responses"] for r in rs),
        })
    return out


def _fmt(v):
    if isinstance(v, float):
        return f"{v:.4f}"
    return "" if v is None else v


def write_csv(path: str, rows: List[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: _fmt(v) for k, v in r.items()})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--survey", required=True, help="one row per response: date, answer[, other_text]")
    ap.add_argument("--channels", required=True,
                    help="date, channel, spend, impressions, attributed_orders (daily or per period)")
    ap.add_argument("--mapping", help="answer, channel: maps survey labels to your channel names")
    ap.add_argument("--period", default="week", choices=["week", "month"])
    ap.add_argument("--out", default="output")
    a = ap.parse_args(argv)

    mapping = load_mapping(a.mapping)
    counts, other_text = survey_counts(_read(a.survey, SURVEY_COLS), mapping, a.period)
    totals = channel_totals(_read(a.channels, CHANNEL_COLS), a.period)
    rows = compare(counts, totals)
    sig = signals(rows)
    os.makedirs(a.out, exist_ok=True)
    write_csv(os.path.join(a.out, "1_by_period.csv"), rows)
    write_csv(os.path.join(a.out, "2_signals.csv"), sig)
    write_csv(os.path.join(a.out, "3_other_answers.csv"), other_text)
    print(f"{len(rows)} period-channel rows, {len(sig)} channels. Wrote {a.out}/")
    for s in sig:
        print(f"  {s['channel']}: {s['latest_direction']} for {s['periods_in_a_row']} period(s) in a row"
              f" ({s['periods_with_this_direction']} of {s['periods']}), {s['total_responses']} responses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
