import pytest 

from loop import run_loop, LoopResult
from llm import LLMResponse, FakeLLMClient

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

    