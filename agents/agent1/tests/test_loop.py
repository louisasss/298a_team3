import pytest 

from loop import run_loop, LoopResult
from llm import LLMResponse, FakeLLMClient, ToolCall

# fake tool function
def fake_rollout_status():
    return {"phase": "Paused"}

# fake failing tool function
def broken_tool():
    raise RuntimeError("prometheus down")

# test: answer on first round 
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

# test: the model call fails
def test_model_error_stops_loop():
    fake = FakeLLMClient([RuntimeError("provider down")])
    result = run_loop(
        client=fake,
        budget={},
        prices={"input": 2.0, "output": 10.0},
        tools={},
        tool_definitions=[],
        messages=["hi"],
    )
    assert result.stop_reason == "model_error"
    assert result.text is None
    assert len(fake.calls) == 1

# test: the model call fails after a tool round
def test_model_error_after_tool_round():
    fake = FakeLLMClient([
        LLMResponse(tool_calls=[ToolCall(name="rollout_status", arguments={})], input_tokens=500, output_tokens=20),
        RuntimeError("provider down"),
    ])
    result = run_loop(
        client=fake,
        budget={},
        prices={"input": 2.0, "output": 10.0},
        tools={"rollout_status": fake_rollout_status},
        tool_definitions=[],
        messages=["hi"],
    )
    assert result.stop_reason == "model_error"
    assert result.tool_calls == 1
    assert result.input_tokens == 500
    assert len(fake.calls) == 2

# test: unknown tool gets "invalid_output"
def test_unknown_tool_response():
    fake = FakeLLMClient([LLMResponse(tool_calls=[ToolCall(name="made_up_tool", arguments={})], input_tokens=500, output_tokens=20)])
    result = run_loop(
        client=fake,
        budget={},
        prices={"input": 2.0, "output": 10.0},
        tools={},
        tool_definitions=[],
        messages=["hi"],
    )
    assert result.stop_reason == "invalid_output"
    assert result.tool_calls == 1
    assert len(fake.calls) == 1

# test: request tool that exists but breaks
def test_existing_tool_broken():
    fake = FakeLLMClient([LLMResponse(tool_calls=[ToolCall(name="prometheus_query", arguments={})], input_tokens=500, output_tokens=20)])
    result = run_loop(
        client=fake,
        budget={},
        prices={"input": 2.0, "output": 10.0},
        tools={"prometheus_query": broken_tool},
        tool_definitions=[],
        messages=["hi"],
    )
    assert result.stop_reason == "tool_error"
    assert len(fake.calls) == 1