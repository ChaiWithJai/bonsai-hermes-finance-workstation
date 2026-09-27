# Measured Slack run and next optimization test

The read-only Slack request on September 26, 2026 took 101.5 seconds from Hermes receiving the DM to preparing its reply. Hermes used the local `bonsai-ui-public-ternary-bonsai2` endpoint on this Mac. The active `llama-server` process served the Ternary Bonsai 2 27B PQ2_0 GGUF with a 65,536-token context, one parallel slot, GPU offload, Jinja templates, and a 512-token reasoning budget. These are the settings observed for this run, not a comparison against another configuration.

| Model call | Input tokens | Output tokens | Latency | Result |
| --- | ---: | ---: | ---: | --- |
| 1 | 2,659 | 330 | 20.3 s | Read portfolio and reports |
| 2 | 3,815 | 46 | 5.2 s | Compare scenarios |
| 3 | 4,450 | 549 | 23.0 s | Repeated the same comparison |
| 4 | 4,652 | 1,327 | 52.5 s | Final answer |

The finance tools themselves took at most 0.09 seconds each. The four model calls account for approximately 101.0 of the 101.5 seconds. The repeated comparison returned a byte-identical result, so it added a model round trip without adding data. The final response also contained 2,756 characters of explanation; a shorter requested format may reduce generation time, but that has not been tested under matched conditions.

The [reuse pilot below](#reusing-tool-results) tests an instruction intended to avoid redundant calls. Runtime comparisons remain separate work; this Slack recording alone establishes neither a speedup nor a cost saving.


## Comparison followed by a saved draft

The concise Slack comparison and follow-up save used five main model requests totaling 22,980 input tokens and 965 output tokens. A separate session-title request added 284 input tokens and 525 output tokens. The [per-request record](../evidence/sessions/slack-saved-draft-usage.json) includes both categories and raw exchange hashes. Repeated conversation context is included in those totals.

The saved draft was independently verified, but a human has not accepted its analysis. The run does not measure wall energy or establish a matched hosted cost comparison. Comparing its latency to the earlier comparison-only run would mix different tasks.

## Reusing tool results

A four-session development pilot compared the baseline instructions with one added rule to reuse successful read-only results. Each fresh session used the same request, portfolio and model process, in baseline, revised, revised, baseline order.

| Run | Instructions | Time | Repeated calls | Answer review |
| --- | --- | ---: | ---: | --- |
| 1 | Baseline | 39.80 s | 0 | Required comparison correct |
| 2 | Reuse rule | 67.32 s | 3 | Required comparison correct |
| 3 | Reuse rule | 42.78 s | 0 | Required comparison correct |
| 4 | Baseline | 35.99 s | 0 | Downside change misstated |

The reuse rule was not adopted. Two runs per variant do not establish a reliable timing effect, and the rule failed to prevent repeats in one run. The fastest answer gave the correct downside levels but described their 220-basis-point difference as roughly 100 basis points.

The comparison tool now returns signed changes in both percentage points and basis points. The instructions tell the agent to use those values. Unit tests verify the arithmetic. A [subsequent local replay](../evidence/scenario-deltas-20260927/review.json) reported the correct +0.90 and -2.20 percentage-point changes in 52.3 seconds. It verifies that development case, not a general reliability or latency improvement. [Raw answers, configuration hashes and review](../evidence/reuse-pilot-20260927/review.json) preserve the pilot. These are agent reviews of a development case, not human approvals or a held-out accuracy estimate.
