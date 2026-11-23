from dataclasses import dataclass
import time

@dataclass
class LoopResult:
    stop_reason: str
    text: str | None = None
    tool_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    seconds: float = 0.0


def run_loop(client, budget, prices, tools, tool_definitions, messages):
    start = time.monotonic()
    input_tokens = 0
    output_tokens = 0

    response = client.complete(messages, tool_definitions)
    input_tokens += response.input_tokens
    output_tokens += response.output_tokens
    cost_usd = input_tokens / 1000000 * prices["input"]  +  output_tokens / 1000000 * prices["output"]
    seconds = time.monotonic() - start
    if response.text is not None and not response.tool_calls:
        return LoopResult(stop_reason="done", text=response.text, input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=cost_usd, seconds=seconds)


