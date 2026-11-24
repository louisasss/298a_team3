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
