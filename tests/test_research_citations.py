import importlib.util
from pathlib import Path
import unittest


path = Path(__file__).resolve().parents[1] / "scripts/check_research_citations.py"
spec = importlib.util.spec_from_file_location("check_research_citations", path)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def session(extracted_section: str, answer_section: str) -> dict:
    url = "https://example.com/terms/"
    payload = '{"results":[{"url":"' + url + '","content":"**' + extracted_section + '. Renewal.** Notice is required.","error":null}]}'
    return {"id": "sample", "messages": [
        {"role": "assistant", "tool_calls": [{"id": "call-1", "function": {"name": "web_extract"}}]},
        {"role": "tool", "tool_call_id": "call-1", "content": '<untrusted_tool_result source="web_extract">\n' + payload + '\n</untrusted_tool_result>'},
        {"role": "assistant", "content": url + " Section " + answer_section + " requires notice."},
    ]}


class ResearchCitationTests(unittest.TestCase):
    def test_accepts_section_present_in_extracted_page(self):
        result = checker.review(session("11.2", "11.2"), "https://example.com/terms/", 150)
        self.assertTrue(result["passed"])

    def test_rejects_section_visible_only_outside_extraction(self):
        result = checker.review(session("2.3", "11.2"), "https://example.com/terms/", 150)
        self.assertFalse(result["passed"])
        self.assertEqual(result["missing_sections"], ["11.2"])

    def test_rejects_answer_over_requested_length(self):
        record = session("11.2", "11.2")
        record["messages"][-1]["content"] += " extra" * 160
        self.assertFalse(checker.review(record, "https://example.com/terms/", 150)["checks"]["within_word_limit"])

    def test_ignores_spillover_preview_but_uses_visible_retry(self):
        record = session("2.3", "2.3")
        record["messages"].insert(1, {"role": "tool", "tool_call_id": "call-1",
            "content": '<untrusted_tool_result source="web_extract">\n<persisted-output>Preview: {"results": [truncated]\n</persisted-output>\n</untrusted_tool_result>'})
        result = checker.review(record, "https://example.com/terms/", 150)
        self.assertTrue(result["passed"])
        self.assertEqual(result["unreadable_extractions"], 1)


if __name__ == "__main__":
    unittest.main()
