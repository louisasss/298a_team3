import json
from datetime import datetime, timezone

LOOP_FIELDS = ("stop_reason", "tool_calls", "input_tokens", "output_tokens", "cost_usd", "seconds")

def build_record(mode, config, output, loop_result, static_decision=None, extra=None):
    if mode == "analysis":
        result = output["decision"]
    else:
        result = output["risk_level"]

    record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mode": mode,
                "model": config["model"]["name"],
                "result": result,
                "fallback_used": output["fallback_used"],
                "fallback_reason": output.get("fallback_reason"),
                "static_decision": static_decision,
                "output": output
    }

    for field in LOOP_FIELDS:
        record[field] = None if loop_result is None else getattr(loop_result, field)

    if extra:
        record.update(extra)
    return record

def write_record(path, record):
    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")
        

