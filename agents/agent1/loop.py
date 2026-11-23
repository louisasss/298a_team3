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
    tool_calls = 0
    messages = list(messages)
    cost_usd = 0.0

    def finish(stop_reason, text=None):
        seconds = time.monotonic() - start
        return LoopResult(
            stop_reason=stop_reason,
            text=text, 
            tool_calls=tool_calls, 
            input_tokens=input_tokens, 
            output_tokens=output_tokens, 
            cost_usd=cost_usd, 
            seconds=seconds
        )

    while True:
        if (time.monotonic() - start) > budget["max_seconds"]:
            return finish("timeout")
        try:
            response = client.complete(messages, tool_definitions)
        except Exception:
            return finish("model_error")
        
        input_tokens += response.input_tokens
        output_tokens += response.output_tokens
        cost_usd = input_tokens / 1000000 * prices["input"]  +  output_tokens / 1000000 * prices["output"]

        if (input_tokens + output_tokens) > budget["max_tokens"] or cost_usd > budget["max_cost_usd"]:
            return finish("budget_exceeded")
        
        if response.text is not None and not response.tool_calls:
            return finish("done", text=response.text)

        if not response.tool_calls:
            return finish("invalid_output")
        
        messages.append({"role": "assistant", "tool_calls": response.tool_calls})
        for call in response.tool_calls:
            tool_calls += 1
            if tool_calls > budget["max_tool_calls"]:
                return finish("budget_exceeded")
            if call.name not in tools:
                return finish("invalid_output")
            function = tools[call.name]
            try:
                result  = function(**call.arguments)
            except Exception:
                return finish("tool_error")
            messages.append({"role": "tool", "name": call.name, "content": result})
        



