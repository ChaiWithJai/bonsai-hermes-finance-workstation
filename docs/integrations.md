# Google Sheets, Slack and public research

The local run in the [README](../README.md) uses the bundled portfolio and analyst reports. The connections below are optional. Google Sheets downloads a validated input snapshot for the finance tools. Slack lets an authorized user ask Hermes to use those tools through a bot.

## Read a Google Sheet into the local tools

Create a workbook that your Google account can read. Name its tabs `Portfolio` and `Analyst Reports`, and use the column headers in [portfolio.csv](../src/finance_workstation/sample_data/portfolio.csv) and [analyst_reports.csv](../src/finance_workstation/sample_data/analyst_reports.csv). The importer accepts a title row above either header. It copies the repository's [mandate](../src/finance_workstation/sample_data/mandate.json) into the snapshot, so the workbook changes the holdings and report inputs but does not change the allocation rules.

The current validator expects the example's `FCT-` asset IDs and `FIC-` report IDs, positive integer units and prices, and dates matching the mandate. Start by importing the supplied rows. To adapt the example to another data model, update the validation in [tools.py](../src/finance_workstation/tools.py) and the mandate together.

For a manual test, obtain an access token through Google's [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/). Authorize `https://www.googleapis.com/auth/spreadsheets.readonly` with the account that can read the workbook, exchange the authorization code, and copy the access token. Access tokens expire, so repeat authorization or implement Google's [installed-app OAuth flow](https://developers.google.com/identity/protocols/oauth2/native-app) for a persistent integration. Organization policies may require an approved OAuth client.

In the activated project environment, provide the workbook ID and access token. For example, on macOS with zsh:

```sh
export FINANCE_SPREADSHEET_ID='your-spreadsheet-id'
read -rs 'FINANCE_GOOGLE_TOKEN?Google Sheets access token: '
export FINANCE_GOOGLE_TOKEN
export FINANCE_DATA_DIR="$PWD/sheets_snapshot"
python -m finance_workstation.sheets
```

The command downloads the two tabs through the Sheets API, checks their headers and values, and writes `portfolio.csv`, `analyst_reports.csv`, `mandate.json`, and `source.json` under `sheets_snapshot/`. The access token is used by the importer and is not written to the snapshot. Check the recorded source before connecting Hermes:

```sh
python -c 'from finance_workstation.tools import snapshot; s = snapshot(); print(s["source"]); print(s["snapshot_sha256"])'
```

The source should report `integration: google_sheets_download`, the workbook ID, and `synced_at`. The hash identifies the validated local snapshot. If the first import fails, run `unset FINANCE_DATA_DIR` to return to the bundled sample. Do not configure Hermes to read an incomplete download. Stop the gateway before refreshing a snapshot in place because the importer replaces the files sequentially.

With `FINANCE_DATA_DIR` still exported, run `python scripts/setup_profile.py --profile finance-workstation`. Setup saves the absolute snapshot path in the MCP environment. It also preserves `FINANCE_DRAFT_DIR` when supplied, so saved drafts have a stable location independent of the gateway's working directory. Google credentials are not copied into the profile.

For an existing profile, add the absolute snapshot directory as `FINANCE_DATA_DIR` in `mcp_servers.finance.env` in its `config.yaml`.

Keep any existing `FINANCE_MLFLOW_TRACE` value if you use local MLflow tracing. The `FINANCE_DATA_DIR` value must point to the directory, not a CSV file. A new `hermes --profile finance-workstation chat ...` process will read the changed profile. If a gateway is already serving that profile, restart it with `hermes --profile finance-workstation gateway restart` so its MCP process loads the new environment and data. Then ask Hermes to call `read_portfolio` and report the source integration, sync time, and snapshot hash. Verify those fields against `source.json` and the direct `snapshot()` read above before treating the answer as a Sheet-backed review.

The tools read the downloaded snapshot, not the live workbook on every question. Run the importer again when the workbook changes, and restart a running gateway before relying on the new snapshot. This importer does not write to Google Sheets.

## Chat with the agent in Slack

First complete the local Hermes run in [setup](setup.md), using the `finance-workstation` profile. Create a new Slack app from [config/slack-manifest.json](../config/slack-manifest.json) in Slack's app management page. The manifest enables Socket Mode, the bot's Messages tab, required events and bot scopes. In the new app's **Basic Information**, create an app-level token with `connections:write`; its value starts with `xapp-`. Install the app to the workspace and copy its bot token, which starts with `xoxb-`. Copy the Slack Member ID of each person allowed to DM the bot.

Copy the profile's generated `.env.example` to `.env`, then fill these three fields in `~/.hermes/profiles/finance-workstation/.env`:

```text
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_ALLOWED_USERS=U01ABC2DEF3
```

Use comma-separated Member IDs for more than one allowed user. Keep the two tokens in the profile's `.env`, outside the repository. A separate Slack app and tokens are needed when another Hermes profile already serves a bot; two profiles should not connect with the same bot token.

Check the gateway state and start this profile's gateway in a terminal if no service is running:

```sh
hermes --profile finance-workstation gateway status
hermes --profile finance-workstation gateway run
```

Leave the foreground gateway running while testing. If this profile already has an installed gateway service, use `hermes --profile finance-workstation gateway restart` after changing its `.env` or tool configuration, then check `gateway status` again. Do not start a second forced gateway on the same bot token.

Open the bot's Messages tab in Slack and send the same portfolio question used in the local run. The reply should give the current and candidate weights, explain the base and downside change, identify the analyst reports, and state whether the source was the bundled sample data or a downloaded Sheet snapshot. The bot can save a local review draft when asked; it cannot place an order. The [recorded Slack review](google-verification.md) used a downloaded Sheet snapshot and saved a candidate for Anthony. It used the existing demo bot, so it does not verify installation of a separate Slack app.

## Add public research

Create a separate profile with Hermes' native search and page-reading tools:

```sh
python scripts/setup_profile.py --profile portfolio-research --web-research
hermes --profile portfolio-research chat
```

The option adds the `web` toolset to CLI and Slack and selects Exa's free search provider and Firecrawl's free page extraction provider. It uses the [Hermes web tools](https://github.com/NousResearch/hermes-agent/blob/59004a62356f3a4697ab0fe8ad5086d2b405e2a6/tools/web_tools.py) supported by the recorded installation. Provider availability and free-tier limits can change; `hermes --profile portfolio-research tools` lets you choose another provider.

Ask for a primary-source page about a public issuer's service commitments, then ask which assumption an analyst should investigate. The agent should read the selected page and cite its URL. Search queries go to the selected provider, so the [research instructions](../config/research.md) keep holdings, weights and internal analyst text out of queries.

Public sources provide context for the reviewer. They do not change the sample return assumptions or saved candidate; update and validate the input snapshot before recalculating. The profile created without `--web-research` keeps its original tool access.

The [recorded research runs](../evidence/public-research-20260927/README.md) show the provider change and a source-grounding failure. Firecrawl returned the relevant SLA sections in the first run, but the fee-cap wording was imprecise. Follow-up runs cited sections that were absent from truncated extractions. Review retrieved sections before using a research answer; the optional CLI path has not passed that check.

After a research run, export its Hermes session and check that every cited section was in the extracted page. Use the session ID printed by Hermes and the URL in its answer:

```sh
hermes --profile portfolio-research sessions export --format jsonl --session-id SESSION_ID /tmp/finance-research.jsonl --yes
python3 scripts/check_research_citations.py /tmp/finance-research.jsonl --url https://www.cloudflare.com/enterpriseterms/
```

The command exits with status 2 if the source page, section text, URL, word limit or no-write condition fails. Passing only establishes section presence. Read the cited clause yourself before publishing: the [follow-up evaluation](../evidence/public-research-20260927/followup-review.json) contains a run that passed this mechanical check but added an unsupported claim about the SLA.
