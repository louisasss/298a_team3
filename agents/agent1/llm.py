from dataclasses import dataclass, field


@dataclass
class ToolCall:
    name: str
    arguments: dict
    id: str = ""

@dataclass
class LLMResponse:
    text: str | None = None
    tool_calls: list = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


class FakeLLMClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def complete(self, messages, tools):
        self.calls.append({"messages": list(messages), "tools": tools})
        if not self.responses:
            raise RuntimeError("FakeLLMClient ran out of scripted responses.")
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item