# Sheet import and Slack review verification

On September 26, the importer authenticated to the demonstration Google workbook and downloaded the Portfolio and Analyst Reports tabs. Validation accepted the snapshot, and the deterministic calculation reproduced 20 feasible allocations, with base return changing from 7.75% to 8.65% and downside from -14.50% to -16.70%.

The Slack profile was configured to use the downloaded snapshot and its gateway restarted. Session `20260926_165557_3ce6c6e4` then used that snapshot for a portfolio review. Its answer identified Orbit's low-confidence report, the scenario tradeoff and the matching snapshot hash. Slack API readback confirmed delivery. No draft or order was requested.

The gateway recorded 61.8 seconds to prepare the response over three model calls. That is one observation, not a latency distribution or an optimization comparison. The wording still needs editorial review.

The [import record](../evidence/sessions/google-import-verification.json) identifies the snapshot. The tools read a downloaded copy, not the live workbook on each question. The importer must run again to incorporate later Sheet edits. Authentication and a successful calculation do not establish investment quality or human acceptance.
