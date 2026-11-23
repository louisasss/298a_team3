import pytest 

from loop import run_loop, LoopResult
from llm import LLMResponse, FakeLLMClient, ToolCall

# fake tool function
def fake_rollout_status():
    return {"phase": "Paused"}

# test 
def test_answer_on_first_round():
    fake = FakeLLMClient([LLMResponse(text="promote", input_tokens=1000, output_tokens=100)])
    result = run_loop(
        client=fake,
        budget={},
        prices={"input": 2.0, "output": 10.0},
        tools={},
        tool_definitions=[],
        messages=["hi"],
    )
    assert result.stop_reason == "done"
    assert result.text == "promote"
    assert result.input_tokens == 1000
    assert result.output_tokens == 100
    assert result.cost_usd == pytest.approx(0.003)

# test: one tool request then an answer
def test_one_tool_request():
    fake = FakeLLMClient([
        LLMResponse(tool_calls=[ToolCall(name="rollout_status", arguments={})], input_tokens=500, output_tokens=20), 
        LLMResponse(text="promote", input_tokens=800, output_tokens=50)
    ])
    tools={"rollout_status": fake_rollout_status}
    messages =  ["hi"]
    result = run_loop(
            client=fake,
            budget={},
            prices={"input": 2.0, "output": 10.0},
            tools=tools,
            tool_definitions=[],
            messages=messages,
        )
    assert result.stop_reason == "done"
    assert result.tool_calls == 1
    assert result.input_tokens == 1300
    assert result.output_tokens == 70
    assert len(fake.calls) == 2
    assert fake.calls[1]["messages"][-1] == {"role": "tool", "name": "rollout_status", "content": {"phase": "Paused"}}
    assert messages == ["hi"]
