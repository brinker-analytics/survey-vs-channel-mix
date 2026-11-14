# Example data

Everything in this folder is made up. `scripts/make_example_data.py` generated it with a fixed seed, so you can rebuild the same files. It comes from no store, client or ad account.

- `EXAMPLE_survey.csv`: 645 made-up post-purchase survey answers over 12 weeks (Aug 3 to Oct 25, 2026), one row per answer, with free text on the "Other" answers.
- `EXAMPLE_channels.csv`: made-up daily spend, impressions and attributed orders for three paid channels.
- `EXAMPLE_mapping.csv`: maps the survey labels a customer sees ("Facebook / Instagram") to the channel names in the spend data ("Meta").

The answer weights, spend levels and CPMs are settings in the script. Real stores vary, so don't read the example output as a benchmark.
