import pytest
import json

from agent import run_agent
from config import load_config
from llm import LLMResponse, FakeLLMClient
from validate import is_valid

GOOD_INPUT = {
    'canary_pod_hash': 'abc', 
    'stable_pod_hash': 'def', 
    'rollout_name': 'parcelpost', 
    'namespace': 'default'
}
GOOD_ANSWER = '{"decision": "promote", "reason": "Healthy.", "confidence": 0.9, "fallback_used": false}'
CONFIG = load_config()


#test: invalid input
def test_invalid_input():
    fake = FakeLLMClient([])
    bad_input = {"rollout_name": "parcelpost"}  #missing required fields
    output, loop_result = run_agent(
        mode="analysis", 
        input_data=bad_input, 
        client=fake, 
        config=CONFIG, 
        tools={}, 
        tool_definitions=[]
    )
    assert output["fallback_reason"] == "invalid_input"
    assert loop_result is None
    assert len(fake.calls) == 0
    assert is_valid("analysis_output", output)

# test: loop fails
def test_loop_failure_uses_static_decision():
    fake = FakeLLMClient([RuntimeError("provider down")])
    output, loop_result = run_agent(
        mode="analysis", 
        input_data=GOOD_INPUT, 
        client=fake, 
        config=CONFIG, 
        tools={}, 
        tool_definitions=[],
        static_decision="abort"
    )
    assert output["fallback_reason"] == "model_error"
    assert loop_result.stop_reason == "model_error"
    assert output["decision"] == "abort"

# test: success
def test_good_answer_returned():
    fake = FakeLLMClient([LLMResponse(text=GOOD_ANSWER)])
    output, loop_result = run_agent(
        mode="analysis", 
        input_data=GOOD_INPUT, 
        client=fake, 
        config=CONFIG, 
        tools={}, 
        tool_definitions=[]
    )
    assert output["decision"] == "promote"
    assert output["fallback_used"] is False

#test: bad answer
def test_bad_answer_falls_back():
    fake = FakeLLMClient([LLMResponse(text="I think promote")])
    output, loop_result = run_agent(
        mode="analysis", 
        input_data=GOOD_INPUT, 
        client=fake, 
        config=CONFIG, 
        tools={}, 
        tool_definitions=[]
    )
    assert output["fallback_reason"] == "invalid_output"
    assert loop_result.stop_reason == "done"

# test: messages build right
def test_messages_built_from_input():
    fake = FakeLLMClient([LLMResponse(text=GOOD_ANSWER)])
    output, loop_result = run_agent(
        mode="analysis", 
        input_data=GOOD_INPUT, 
        client=fake, 
        config=CONFIG, 
        tools={}, 
        tool_definitions=[]
    )
    messages = fake.calls[0]["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1]["content"] == json.dumps(GOOD_INPUT)

# test: a successful run writes one log record
def test_success_is_logged(tmp_path):
    log_path = tmp_path / "log.jsonl"
    fake = FakeLLMClient([LLMResponse(text=GOOD_ANSWER, input_tokens=1000, output_tokens=100)])
    output, loop_result = run_agent(
        mode="analysis",
        input_data=GOOD_INPUT,
        client=fake,
        config=CONFIG,
        tools={},
        tool_definitions=[],
        log_path=log_path,
    )
    lines = log_path.read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["result"] == output["decision"]
    assert record["stop_reason"] == "done"
    assert record["input_tokens"] == 1000


# test: a fallback is logged too, with its reason and the static decision
def test_fallback_is_logged(tmp_path):
    log_path = tmp_path / "log.jsonl"
    fake = FakeLLMClient([RuntimeError("provider down")])
    output, loop_result = run_agent(
        mode="analysis",
        input_data=GOOD_INPUT,
        client=fake,
        config=CONFIG,
        tools={},
        tool_definitions=[],
        static_decision="abort",
        log_path=log_path,
    )
    lines = log_path.read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["result"] == "abort"
    assert record["fallback_reason"] == "model_error"
    assert record["static_decision"] == "abort"
