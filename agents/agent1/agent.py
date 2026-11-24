import json

from loop import run_loop
from validate import INPUT_SCHEMAS, is_valid, parse_output, build_fallback

SYSTEM_PROMPTS = {
    "analysis": "You judge canary releases. Use the tools to check the canary, then answer with JSON matching the analysis_output schema.",
    "ci_pr": "You review every pull request. Use the tools to check the PR's code changes and test results, then answer with an advisory PR comment that does not block merging in JSON format matching the ci_output schema.",
    "ci_release": "You summarize all changes between the last deploy and the release commit. Use the tools to investigate all changes since the last deploy, then answer with JSON matching the release_brief schema",
}

def run_agent(mode, input_data, client, config, tools, tool_definitions, static_decision=None):
    if not is_valid(INPUT_SCHEMAS[mode], input_data):
        return build_fallback(mode, "invalid_input", static_decision, input_data), None

    budget = config["budgets"][mode]
    prices = config["model"]["price_per_million_tokens"]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS[mode]},
        {"role": "user", "content": json.dumps(input_data)},
    ]
    
    loop_result = run_loop(client, budget, prices, tools, tool_definitions, messages)
    if loop_result.stop_reason != "done":
        return build_fallback(mode, loop_result.stop_reason, static_decision, input_data), loop_result

    output = parse_output(mode, loop_result.text)
    if output is None:
        return build_fallback(mode, "invalid_output", static_decision, input_data), loop_result
    return output, loop_result
    