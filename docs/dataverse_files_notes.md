# Good Judgment Project Data Files
_Note: AI generated, Gatlen edited_

The dataset can be found here: https://dataverse.harvard.edu/dataverse/gjp

Download it and move it to `$PROJ_ROOT/data/dataverse_files`

Sources: [readme.txt](../data/dataverse_files/readme.txt), [readme_1.txt](../data/dataverse_files/readme_1.txt) (prediction markets), [all_individual_differences.README.md](../data/dataverse_files/all_individual_differences.README.md)

## Core Files

- `ifps.csv` — Individual Forecasting Problems (questions). Contains question text, resolution criteria, dates, outcomes, and metadata. See [readme.txt](../data/dataverse_files/readme.txt) for field definitions.
- `all_individual_differences.csv` — Participant survey data: demographics, cognitive tests (Raven's, CRT, numeracy), personality scales (grit, AOMT, need for cognition), political knowledge, and more. See [all_individual_differences.README.md](../data/dataverse_files/all_individual_differences.README.md) for full variable codebook.

## Survey Forecasts (Traditional)

Forecasts made by individuals in survey-based conditions (not prediction markets). Field definitions in [readme.txt](../data/dataverse_files/readme.txt):

- `survey_fcasts.yr1.csv` — Year 1 forecasts
- `survey_fcasts.yr2.csv` — Year 2 forecasts
- `survey_fcasts.yr3.csv` — Year 3 forecasts
- `survey_fcasts.yr4.csv` — Year 4 forecasts

## Prediction Market Transactions

Continuous double auction (CDA) prediction markets (PMs) run by [Lumenogic](https://www.hypermind.com/about-us) (yr2-3) and logarithmic market scoring rule (LMSR) markets run by [Inkling](https://blog.inklingmarkets.com/2014/04/so-you-think-youre-smarter-than-cia.html) (yr3-4). See [readme_1.txt](../data/dataverse_files/readme_1.txt) for market details and column definitions:

- `pm_transactions.lum1.yr3.csv` — Lumenogic market, US citizens only, individuals
- `pm_transactions.lum2.yr2.csv` — Lumenogic market yr2, with training
- `pm_transactions.lum2.yr3.csv` — Lumenogic market yr3, teams (after Jan 2014)
- `pm_transactions.lum2a.yr3.csv` — Lumenogic market yr3, individuals (before Jan 2014)
- `pm_transactions.inkling.yr3.csv` — Inkling LMSR market, individuals
- `pm_transactions.control.yr4.csv` — Inkling control market (no training, no batch auction)
- `pm_transactions.batch.train.yr4.csv` — Inkling with training + batch auction
- `pm_transactions.batch.notrain.yr4.csv` — Inkling without training + batch auction
- `pm_transactions.supers.yr4.csv` — Superforecasters market
- `pm_transactions.teams.yr4.csv` — Teams market

## Batch Auction Orders (Year 4 only)

Initial price-setting auctions for Inkling markets. See [readme_1.txt](../data/dataverse_files/readme_1.txt):

- `pm_batch_orders.batch.train.yr4.csv`
- `pm_batch_orders.batch.notrain.yr4.csv`
- `pm_batch_orders.supers.yr4.csv`
- `pm_batch_orders.teams.yr4.csv`
