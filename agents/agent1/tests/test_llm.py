import pytest
from llm import FakeLLMClient, LLMResponse


# responses come back in order
def test_reponses_order():
    fake = FakeLLMClient([LLMResponse(text='first'), LLMResponse(text='second')])
    first_result = fake.complete([],[])
    second_result = fake.complete([],[])
    assert first_result.text == "first"
    assert second_result.text == "second"

# scripted error is raised
def test_error_raised():
    fake = FakeLLMClient([RuntimeError("provider down")])
    with pytest.raises(RuntimeError, match="provider down"):
        fake.complete([],[])

# running out of script
def test_end_script():
    fake = FakeLLMClient([])
    with pytest.raises(RuntimeError, match="ran out"):
        fake.complete([],[])

# calls are recorded
def test_calls_recorder():
    fake = FakeLLMClient([LLMResponse(text='hi'), LLMResponse(text='again')])
    fake.complete(["hi"],[])
    fake.complete(["hi", "again"],[])
    assert len(fake.calls) == 2    
    assert fake.calls[1]["messages"] == ["hi", "again"]

# failed calls are recorded too
def test_failed_call_recorded():
    fake = FakeLLMClient([RuntimeError("provider down")])
    with pytest.raises(RuntimeError):
        fake.complete(["hi"], [])
    assert len(fake.calls) == 1

# recorded messages are a copy, so later changes don't rewrite history
def test_recorded_messages_are_copy():
    fake = FakeLLMClient([LLMResponse(text="ok")])
    messages = ["hi"]
    fake.complete(messages, [])
    messages.append("added later")
    assert fake.calls[0]["messages"] == ["hi"]

# LLMResponse defaults
def test_response_defaults():
    response = LLMResponse()
    assert response.text is None
    assert response.tool_calls == []
    assert response.input_tokens == 0
    assert response.output_tokens == 0