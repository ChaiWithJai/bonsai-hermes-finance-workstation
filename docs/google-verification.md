# Sheet import and Slack review verification

On September 26, the importer authenticated to the demonstration Google workbook and downloaded the Portfolio and Analyst Reports tabs. Validation accepted the snapshot, and the deterministic calculation reproduced 20 feasible allocations, with base return changing from 7.75% to 8.65% and downside from -14.50% to -16.70%.

The Slack profile was configured to use the downloaded snapshot and its gateway restarted. Session `20260926_165557_3ce6c6e4` then used that snapshot for a portfolio review. Its answer identified Orbit's low-confidence report, the scenario tradeoff and the matching snapshot hash. Slack API readback confirmed delivery. No draft or order was requested.

The gateway recorded 61.8 seconds to prepare the response over three model calls. That is one observation, not a latency distribution or an optimization comparison. The wording still needs editorial review.

The [import record](../evidence/sessions/google-import-verification.json) identifies the snapshot. The tools read a downloaded copy, not the live workbook on each question. The importer must run again to incorporate later Sheet edits. Authentication and a successful calculation do not establish investment quality or human acceptance.


## Concise comparison and saved review draft

A later Slack conversation read the downloaded Google Sheets snapshot and compared its allocation against the mandate. The two-sentence response preserved the base-case improvement from 7.75% to 8.65%, the worse downside from -14.50% to -16.70%, and the low-confidence Orbit assumption. A follow-up request saved the candidate for Anthony. An independent local file read confirmed the reviewer, candidate weights and pending-review status, matching the tool's readback hash.

The [conversation record](../evidence/sessions/slack-saved-draft.json), [comparison capture](../evidence/screenshots/slack-short-comparison.png) and [saved-draft capture](../evidence/screenshots/slack-saved-draft.png) preserve the result. The draft was saved locally; it did not update Google Sheets or place an order. Anthony's acceptance has not been recorded.

The [request usage](../evidence/sessions/slack-saved-draft-usage.json) includes both conversation turns and auxiliary requests, with raw exchange hashes. Session summary token counts are not used as request totals. The [MLflow record](../evidence/sessions/slack-saved-draft-mlflow.json) points to the artifact review, separately from model or tool tracing.
