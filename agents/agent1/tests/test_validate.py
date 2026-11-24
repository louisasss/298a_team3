import pytest
import json

from validate import is_valid, parse_output, build_fallback

# a valid analysis fallback output (from fixtures/analysis_output/valid/fallback_timeout.json)
@pytest.fixture
def fallback_output():
    return {
        "decision": "inconclusive",
        "reason": "Agent exceeded its time budget; static check had no data.",
        "confidence": None,
        "fallback_used": True,
        "fallback_reason": "timeout",
    }

# a valid normal answer, as text, exactly as the model would send it
GOOD_ANSWER = '{"decision": "promote", "reason": "Canary error rate matches stable.", "confidence": 0.9, "fallback_used": false}'


# test: a valid output passes the schema
def test_valid_output_passes(fallback_output):
    assert is_valid("analysis_output", fallback_output)

# test: a decision outside promote/abort/inconclusive fails the schema
def test_invalid_decision_fails(fallback_output):
    fallback_output["decision"] = "maybe"
    assert not is_valid("analysis_output", fallback_output)

# test: a good answer is turned into a dictionary
def test_parse_good_answer():
    data = parse_output("analysis", GOOD_ANSWER)
    assert data["decision"] == "promote"
    assert data["fallback_used"] is False


# test: text that isn't JSON is rejected
def test_parse_not_json():
    assert parse_output("analysis", "I think we should promote") is None


# test: JSON that doesn't match the schema is rejected
def test_parse_wrong_shape():
    text = GOOD_ANSWER.replace('"promote"', '"maybe"')
    assert parse_output("analysis", text) is None


# test: the model may not declare a fallback itself
def test_parse_rejects_model_fallback(fallback_output):
    text = json.dumps(fallback_output)
    assert parse_output("analysis", text) is None

# test: static check has data → fallback copies its decision
def test_fallback_uses_static_abort():
    result = build_fallback("analysis", "timeout", "abort")
    assert result["decision"] == "abort"
    assert result["fallback_reason"] == "timeout"
    assert is_valid("analysis_output", result)

def test_static_promote():
    result = build_fallback("analysis", "tool_error", "promote")
    assert result["decision"] == "promote"
    assert is_valid("analysis_output", result)

def test_no_static_data():
    result = build_fallback("analysis", "model_error")
    assert result["decision"] == "inconclusive"
    assert is_valid("analysis_output", result)