# survey-vs-channel-mix

Lay your post-purchase survey answers ("How did you hear about us?") next to each channel's share of spend, impressions and attributed orders, period by period, and see which channels customers name more or less often than the rest of your measurement would suggest.

> **Built by [Brinker Analytics](https://brinkeranalytics.com).** Eric Brinker's marketing-measurement practice for DTC brands.
> **Contact:** [eric@brinkeranalytics.com](mailto:eric@brinkeranalytics.com) or the [contact page](https://brinkeranalytics.com/contact).

## How I read a post-purchase survey

A survey is a directional signal. It's never statistically rigorous enough to feed a model, and it has a sampling problem: the people who answer surveys are people who like to answer surveys. It's also the only method that asks the customer directly, and sometimes the answer is one no tracking could give you. A customer can click a Facebook ad and still tell you it was the TV spot that got them thinking about you.

So this tool doesn't treat survey answers as the truth, and it doesn't set a number that "triggers" a test. Survey answers swing without statistical confidence. What you're looking for is a change, or a consistency that keeps recurring.

## What it compares

For each period (week or month) and each channel:

| Column | What it is |
|---|---|
| `survey_share` | The channel's share of the answers that name a channel in your spend data |
| `spend_share` | Its share of spend across those channels |
| `impression_share` | Its share of impressions |
| `attributed_orders_share` | Its share of the orders the platforms attribute |
| `share_of_all_answers` | Its share of every answer, including "Friend or family," "Podcast," "Other" and anything else with no spend row |
| `direction` | `above all` if the survey share is above all three, `below all` if below all three, `mixed` otherwise |

Then, per channel, `2_signals.csv` shows the latest direction, how many periods in a row it has held, and what it changed from if it just flipped.

A tiny gap counts the same as a big one. The tool reads consistency, not size, on purpose.

Answers that don't match any paid channel (word of mouth, a podcast you don't pay for, "Other") are kept and counted. They're often the most interesting rows, because nothing else in your stack can see them. Free text from "Other" goes to `3_other_answers.csv`.

## Run it on the example data

Python 3.9 or newer, standard library only.

```bash
python survey_mix.py \
  --survey example_data/EXAMPLE_survey.csv \
  --channels example_data/EXAMPLE_channels.csv \
  --mapping example_data/EXAMPLE_mapping.csv \
  --period month --out output
```

The example data is made up (see `example_data/README.md`). By month, YouTube's survey share sits above its spend, impression and attributed-order shares in all three months. By week the same data looks noisier: YouTube is above all three in 7 of 12 weeks and mixed in the rest. That's why the period matters, and why one week on its own isn't a signal.

## Run it on your own data

1. Export your survey answers, one row per answer: `date`, `answer`, and `other_text` if you have it.
2. Export each channel's daily (or weekly) `spend`, `impressions` and `attributed_orders` into one file with a `channel` column. Use one attribution setting throughout.
3. Write a mapping file (`answer`, `channel`) from the labels your customers see to the channel names in your spend file. Answers you leave out keep their own label.
4. Run `survey_mix.py` with `--period week` and again with `--period month`.

Setting up the survey itself:

- Put in choices that reflect your media mix, worded the way a customer would recognize them: "Facebook / Instagram," not "social ads."
- Group or split choices the way your business makes decisions. If you budget TikTok and Pinterest separately, list them separately.
- Always include an "Other" box with free-form text.

## Reading the results

- **Small samples.** Don't ignore them. If even one person tells you where they came from, wouldn't you want to know? Treat it as anecdotal and keep it in your back pocket until you have more answers, or until the same answer keeps showing up day over day or week over week.
- **`above all` for many periods in a row.** Customers name this channel more often than its spend, reach or attributed orders would suggest. It may be doing work your attribution can't see.
- **`below all` for many periods in a row.** The channel gets credit in your reports that customers don't name. That isn't proof it does nothing.
- **A flip.** When `changed_from` fills in, something moved that period. Check what changed in the media or the survey before reading more into it.

Acting on survey data is a leap of faith, like every other measurement method. How big a leap depends on how many answers you have.

## What to do with this

- **If a channel is consistently `above all` and you'd change its budget and act on the result if it proved out,** that's a channel worth a test. Hold its spend back in some regions and see whether sales there drop.
- **If a channel is consistently `below all`,** don't cut it on the survey alone. Put it on the test list next to the channels above.
- **If an unpaid answer like a podcast or word of mouth keeps showing up,** use it to put your other channels in context.
- **If the weekly view and the monthly view disagree,** trust neither yet. Keep collecting answers until one pattern holds.
- **If nothing is consistent,** keep the survey running and look again next period.

If you want to know whether what your customers say is worth a test, send me a note and we'll talk it through: [Get in touch](https://brinkeranalytics.com/contact).

Lined the survey up against the mix and still not sure how to set the questions, or when a gap is worth a test? [Invisible Selling Channels](https://brinkeranalytics.com/guides/invisible-selling-channels) walks the two-question survey, how to read the answers against your channel mix, and when a gap is worth a test.

## Free reading on brinkeranalytics.com

- [How to measure CTV, TV and podcast ads without clicks](https://brinkeranalytics.com/insights/measure-ctv-podcast-no-click-media)
- [Why your Meta, Google, GA4, Shopify, and finance numbers disagree](https://brinkeranalytics.com/insights/why-marketing-numbers-disagree)
- [Attribution models: what first-touch, last-touch, and multi-touch rules can tell you](https://brinkeranalytics.com/insights/attribution-models-explained)
- [What is geo testing?](https://brinkeranalytics.com/insights/what-is-geo-testing): the next step when a survey signal is worth testing

## Files

```
survey_mix.py                    the script
example_data/                    made-up example data and how it was generated
example_output/                  results of the script on the example data (monthly)
scripts/make_example_data.py     seeded generator for the example data
tests/test_survey_mix.py         checks that shares add up and every answer is counted once
```

Run the tests with `python -m unittest discover -s tests`.

## License

The code is MIT licensed (see `LICENSE`). The documentation, including this README, is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (see `LICENSE-docs`). If you reuse it, please credit Eric Brinker at [Brinker Analytics](https://www.brinkeranalytics.com).
