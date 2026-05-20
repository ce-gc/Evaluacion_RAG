import json
from validator import validate_output, validate_output_with_id


def test_fenced_json_parses():
    raw = "```json\n{\"ok\": true, \"data\": {\"answer\": \"hi\", \"confidence\": 0.9, \"actions\": [\"a\"], \"error\": null}}\n```"
    ok, err, parsed = validate_output(raw)
    assert ok is True
    assert parsed is not None


def test_escaped_json_string_parses():
    # JSON returned as a quoted string with escaped quotes
    inner = '{"ok": true, "data": {"answer": "ok", "confidence": 0.5, "actions": ["run"], "error": null}}'
    raw = '"' + inner.replace('"', '\\"') + '"'
    ok, err, parsed = validate_output(raw)
    assert ok is True
    assert parsed["ok"] is True


def test_validate_with_id_accepts_fenced():
    raw = "```\n{\"ok\": true, \"data\": {\"answer\": \"x\", \"confidence\": 0.1, \"actions\": [], \"error\": null}}\n```"
    ok, parsed, err = validate_output_with_id(raw, "test-1")
    assert ok is True
    assert parsed is not None


def test_metadata_wrapper_with_response_field():
    inner = '{"ok": true, "data": {"answer": "inner", "confidence": 0.2, "actions": [], "error": null}}'
    wrapped = json.dumps({"model": "gemma2:2b", "response": "```json\n" + inner.replace('"', '\\"') + "\n```"})
    ok, parsed, err = validate_output_with_id(wrapped, "test-2")
    assert ok is True
    assert parsed is not None
    assert parsed.get("data", {}).get("answer") == "inner"
