import json

from config import load_config
from log import build_record, write_record
from loop import LoopResult

CONFIG = load_config()
LOOP = LoopResult(stop_reason="done", text="...", tool_calls=2, input_tokens=1500, output_tokens=80, cost_usd=0.0038, seconds=4.2)


# test: a normal analysis decision
def test_record_from_analysis_answer():
    output = {"decision": "promote", "reason": "Healthy.", "confidence": 0.9, "fallback_used": False}
    record = build_record("analysis", CONFIG, output, LOOP)
    assert record["result"] == "promote"
    assert record["fallback_reason"] is None
    assert record["stop_reason"] == "done"
    assert record["tool_calls"] == 2

# test: invalid input (no loop)
def test_invalid_input():
    output = {"decision": "inconclusive", "reason": "Agent fell back (invalid_input).", "confidence": None, "fallback_used": True, "fallback_reason": "invalid_input"}
    record = build_record(mode="analysis", config=CONFIG, output=output, loop_result=None)
    assert record["stop_reason"] is None
    assert record["tool_calls"] is None
    assert record["fallback_reason"] == "invalid_input"

# test: CI mode
def test_ci_mode():
    output = {"risk_level": "medium", "endpoints_touched": [], "watch": "Max time budget", "fallback_used": False}
    record = build_record(mode="ci_pr", config=CONFIG, output=output, loop_result=LOOP)
    assert record["result"] == output["risk_level"]

# test: extra fields from the scoring harness are added to the record
def test_extra_fields_merged():
    output = {"decision": "promote", "reason": "Healthy.", "confidence": 0.9, "fallback_used": False}
    extra = {"scenario": "latency_spike", "expected": "abort"}
    record = build_record("analysis", CONFIG, output, LOOP, extra=extra)
    assert record["scenario"] == "latency_spike"
    assert record["expected"] == "abort"
    assert record["result"] == "promote"

# test: each record is appended as one JSON line, and reads back unchanged
def test_write_record_appends_lines(tmp_path):
    path = tmp_path / "decisions.jsonl"
    first = build_record(
        "analysis", CONFIG,
        {"decision": "promote", "reason": "Healthy.", "confidence": 0.9, "fallback_used": False},
        LOOP,
    )
    second = build_record(
        "analysis", CONFIG,
        {"decision": "inconclusive", "reason": "Agent fell back (invalid_input); static check had no data, paused for human review.",
         "confidence": None, "fallback_used": True, "fallback_reason": "invalid_input"},
        None,
    )
    write_record(path, first)
    write_record(path, second)

    lines = path.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == first
    assert json.loads(lines[1]) == second
