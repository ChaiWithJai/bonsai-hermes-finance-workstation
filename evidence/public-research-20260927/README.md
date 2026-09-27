# Public research integration

Hermes uses Exa search and Firecrawl page extraction in the optional research profile. The [latest run](firecrawl/run.json) retrieved the relevant Cloudflare SLA sections and returned a 140-word answer identifying a formula available only as an image.

The [answer](firecrawl/answer.txt) still needs a wording correction. It summarizes the cap as "six months of annual fees"; section 9.3 specifies cumulative Monthly Fees actually paid during the annual billing period. The [review](firecrawl/review.json) separates retrieval verification from that precision issue. No portfolio or draft write tool was called.

The original Exa extraction stopped during section 2.1. Both the [first answer](answer.txt) and [retry](retry/answer.txt) asserted terms from later sections using search snippets. Increasing the requested character limit did not change the returned text. Those failed runs are preserved with their tool calls, configuration hashes and reviews.

These are repeated development runs of one CLI request, not a reliability estimate or a Slack research test. The full retrieved pages remain in the private review records; public artifacts include their hashes.

A later [source-grounding review](followup-review.json) tested four more local Bonsai runs. Each failed the publication check: the model either added an unsupported adjacent claim or cited a section absent from the extracted page. The last answer's Section 5.2 claim is correct on Cloudflare's official page, but the Hermes extraction was truncated before that section. The optional research answer should not be presented as verified until the tool or publication gate enforces a full-source read.

The [citation check](../../scripts/check_research_citations.py) now fails three of those four sessions because their cited section is absent from the extract or the answer exceeds the word limit. The second run passes the mechanical check but fails meaning review because of its added SLA claim. The [fourth run's check](full-source-replay/citation-check.json) is a reproducible example of the rejection.
