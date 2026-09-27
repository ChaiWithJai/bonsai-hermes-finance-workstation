"""Check that a Hermes research answer cites sections present in extracted pages.

This is a source-presence check, not a judgment that the answer interprets a
contract correctly. Export a session with `hermes sessions export --format jsonl`
and review the answer and source after this check passes.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SECTION = re.compile(r"\bSection\s+(\d+(?:\.\d+)*)\b", re.IGNORECASE)


def extract_payload(text: str) -> dict | None:
    # A spillover preview is not the page the model read. Count it only if a
    # later tool result exposes the relevant text in the conversation.
    if "<persisted-output>" in text:
        return None
    start = text.find("{")
    end = text.rfind("</untrusted_tool_result>")
    if start < 0:
        return None
    try:
        return json.loads(text[start:end if end >= 0 else None].strip())
    except json.JSONDecodeError:
        return None


def review(session: dict, url: str, max_words: int) -> dict:
    messages = session.get("messages", [])
    calls = {}
    for message in messages:
        for call in message.get("tool_calls") or []:
            calls[call["id"]] = call.get("function", {}).get("name")
    extracted = []
    unreadable_extractions = 0
    for message in messages:
        if message.get("role") != "tool" or calls.get(message.get("tool_call_id")) != "web_extract":
            continue
        payload = extract_payload(message.get("content", ""))
        if payload is None:
            unreadable_extractions += 1
            continue
        for item in payload.get("results", []):
            if item.get("url", "").rstrip("/") == url.rstrip("/") and not item.get("error"):
                extracted.append(item.get("content", ""))
    answers = [message.get("content", "") for message in messages
               if message.get("role") == "assistant" and not message.get("tool_calls")]
    answer = answers[-1] if answers else ""
    sections = sorted(set(SECTION.findall(answer)))
    missing = []
    for section in sections:
        heading = re.compile(r"(?m)^\s*(?:#{1,6}\s*)?(?:\*\*)?" + re.escape(section) + r"\.")
        if not any(heading.search(page) for page in extracted):
            missing.append(section)
    words = len(answer.split())
    checks = {
        "source_page_extracted": bool(extracted),
        "answer_cites_source_url": url in answer,
        "cited_sections_in_extraction": bool(sections) and not missing,
        "within_word_limit": words <= max_words,
        "no_write_tool_called": not any(name in {"write_review_draft"} for name in calls.values()),
    }
    return {"session_id": session.get("id"), "source_url": url,
            "cited_sections": sections, "missing_sections": missing,
            "extractions": len(extracted), "unreadable_extractions": unreadable_extractions,
            "answer_words": words,
            "checks": checks, "passed": all(checks.values()),
            "scope": "Section presence and format only; human review of meaning is still required."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_export", type=Path)
    parser.add_argument("--url", required=True)
    parser.add_argument("--max-words", type=int, default=150)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    sessions = [json.loads(line) for line in args.session_export.read_text().split("\n") if line.strip()]
    if len(sessions) != 1:
        parser.error("Expected an export containing exactly one session")
    result = review(sessions[0], args.url, args.max_words)
    encoded = json.dumps(result, indent=2) + "\n"
    if args.report:
        args.report.write_text(encoded)
    print(encoded, end="")
    if not result["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
