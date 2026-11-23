import pytest

from validate import is_valid

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


# test: a valid output passes the schema
def test_valid_output_passes(fallback_output):
    assert is_valid("analysis_output", fallback_output)

# test: a decision outside promote/abort/inconclusive fails the schema
def test_invalid_decision_fails(fallback_output):
    fallback_output["decision"] = "maybe"
    assert not is_valid("analysis_output", fallback_output)