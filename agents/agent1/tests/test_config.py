import pytest
from config import check_config, load_config


# correct config example
@pytest.fixture
def good_config():
    return {
        "model": {
            "provider": "TBD",
            "name": "TBD",
            "api_key_env": "API_KEY",
            "price_per_million_tokens":{
                "input": 2.00,
                "output": 10.00
            }
        },
        "budgets": {
            "ci_pr":{
                "max_seconds": 80,
                "max_tool_calls": 3,
                "max_tokens": 9000,
                "max_cost_usd": 0.035
            },
            "ci_release":{
                "max_seconds": 60,
                "max_tool_calls": 5,
                "max_tokens": 10000,
                "max_cost_usd": 0.035
            },
            "analysis":{
                "max_seconds": 10,
                "max_tool_calls": 7,
                "max_tokens": 9000,
                "max_cost_usd": 0.035
            }
        },
    }

#test: valid config passes
def test_valid_passes(good_config):
    check_config(good_config)

#test: real file loads
def test_file_load():
    load_config()

#test: 'model' value missing
def test_missing_model(good_config):
    del good_config["model"]
    with pytest.raises(ValueError, match="model"):
        check_config(good_config)

#test: 'model' key missing
def test_missing_model_key(good_config):
    del good_config["model"]["api_key_env"]
    with pytest.raises(ValueError, match="api_key_env"):
        check_config(good_config)

#test: 'model' key missing
def test_missing_mode(good_config):
    del good_config["budgets"]["ci_release"]
    with pytest.raises(ValueError, match="ci_release"):
        check_config(good_config)

#test: missing limit
def test_missing_limit(good_config):
    del good_config["budgets"]["analysis"]["max_seconds"]
    with pytest.raises(ValueError, match="max_seconds"):
        check_config(good_config)

#test: limit not a number
def test_limit_dtype(good_config):
    good_config["budgets"]["ci_pr"]["max_seconds"] = "80"
    with pytest.raises(ValueError, match="must be a number"):
        check_config(good_config)

#test: limit = 0
def test_zero_limit(good_config):
    good_config["budgets"]["ci_pr"]["max_seconds"] = 0
    with pytest.raises(ValueError, match="greater than 0"):
        check_config(good_config)

#test: limit is negative number
def test_negative_limit(good_config):
    good_config["budgets"]["ci_pr"]["max_seconds"] = -1
    with pytest.raises(ValueError, match="greater than 0"):
        check_config(good_config)