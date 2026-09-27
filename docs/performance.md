# Measured Slack run and next optimization test

The read-only Slack request on September 26, 2026 took 101.5 seconds from Hermes receiving the DM to preparing its reply. Hermes used the local `bonsai-ui-public-ternary-bonsai2` endpoint on this Mac. The active `llama-server` process served the Ternary Bonsai 2 27B PQ2_0 GGUF with a 65,536-token context, one parallel slot, GPU offload, Jinja templates, and a 512-token reasoning budget. These are the settings observed for this run, not a comparison against another configuration.

| Model call | Input tokens | Output tokens | Latency | Result |
| --- | ---: | ---: | ---: | --- |
| 1 | 2,659 | 330 | 20.3 s | Read portfolio and reports |
| 2 | 3,815 | 46 | 5.2 s | Compare scenarios |
| 3 | 4,450 | 549 | 23.0 s | Repeated the same comparison |
| 4 | 4,652 | 1,327 | 52.5 s | Final answer |

The finance tools themselves took at most 0.09 seconds each. The four model calls account for approximately 101.0 of the 101.5 seconds. The repeated comparison returned a byte-identical result, so it added a model round trip without adding data. The final response also contained 2,756 characters of explanation; a shorter requested format may reduce generation time, but that has not been tested under matched conditions.

The next harness test should keep the same model process, fixture hash, user request, tool set, and answer checks. Change only the finance instruction to forbid repeating a read-only tool with identical arguments during one turn, then run several fresh sessions and compare median total latency, model calls, output tokens, and check results. A matched runtime test can vary one serving setting at a time and record time to first token, total latency, token throughput, and active power. This single run does not establish a speedup or a cost saving.


## Comparison followed by a saved draft

The concise Slack comparison and follow-up save used five main model requests totaling 22,980 input tokens and 965 output tokens. A separate session-title request added 284 input tokens and 525 output tokens. The [per-request record](../evidence/sessions/slack-saved-draft-usage.json) includes both categories and raw exchange hashes. Repeated conversation context is included in those totals.

The saved draft was independently verified, but a human has not accepted its analysis. The run does not measure wall energy or establish a matched hosted cost comparison. Comparing its latency to the earlier comparison-only run would mix different tasks.
