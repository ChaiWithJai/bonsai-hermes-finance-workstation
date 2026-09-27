# Portfolio allocation review

Compare a proposed allocation against the portfolio mandate, inspect the assumptions and save a candidate for a named reviewer. Review the assumed return alongside the downside.

## How it works

Python calculates scenario returns and checks the mandate. Hermes uses local Bonsai to explain the results and save the candidate you select for review.

The [recorded Slack review](docs/google-verification.md) compared the candidate and saved a draft for Anthony.

![Scenario comparison in Slack](evidence/screenshots/slack-short-comparison.png)

## Get started

With Python 3.10 or newer, compare the sample allocations. Expect 20 feasible candidates, with the selected candidate changing the assumed base return from 7.75% to 8.65% and the downside from -14.50% to -16.70%.

```sh
git clone https://github.com/ChaiWithJai/bonsai-hermes-finance-workstation.git
cd bonsai-hermes-finance-workstation
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m finance_workstation example
```

## Resources

| Resource | Use it to |
| --- | --- |
| [Setup](docs/setup.md) | Configure Bonsai and Hermes. |
| [Architecture](docs/architecture.md) | Follow the tools, records and failure handling. |
| [Model parameters](docs/parameter-guide.md) | Choose settings and inspect the supporting measurements. |
| [Configuration capture](docs/recorded-configuration.md) | See the model and Hermes settings used in the recorded run. |
| [Slack, Google and research](docs/integrations.md) | Connect Slack, import a Sheet snapshot and enable public research. |
| [Development](docs/development.md) | Find the implementation and run its tests. |
