from pathlib import Path
import yaml

DEFAULT_PATH = Path(__file__).parent / "config.yaml"

MODES = ("ci_pr", "ci_release", "analysis")
LIMITS = ("max_seconds", "max_tool_calls", "max_tokens", "max_cost_usd")

def load_config(path=DEFAULT_PATH):
    with open(path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
        check_config(config)
        return config

def check_config(config):
    if "model" not in config:
        raise ValueError("config is missing the 'model' section.")
    for key in ("name", "api_key_env"):
        if key not in config["model"]:
            raise ValueError(f"model is missing '{key}' (required: name, api_key_env).")
    if "budgets" not in config:
        raise ValueError("config is missing the 'budgets' section.")
    for mode in MODES:
        if mode not in config["budgets"]:
            raise ValueError(f"budgets is missing mode '{mode}' (required: {', '.join(MODES)}).")
        budget = config["budgets"][mode]

        for limit in LIMITS:
            if limit not in budget:
                raise ValueError(f"budgets.{mode} is missing '{limit}' (required: {', '.join(LIMITS)}).")

            value = budget[limit]

            if not isinstance(value, (int, float)):
                raise ValueError(f"budgets.{mode}.{limit} must be a number, got {value!r} ({type(value).__name__}).")
            if value <= 0:
                raise ValueError(f"budgets.{mode}.{limit} must be greater than 0, got {value}.") 