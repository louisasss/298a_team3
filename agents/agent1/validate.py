from pathlib import Path
import json
import jsonschema

SCHEMA_DIR = Path(__file__).parent.parent / "common" / "schemas"

INPUT_SCHEMAS = {"analysis": "analysis_input", "ci_pr": "ci_input", "ci_release": "ci_input"}
OUTPUT_SCHEMAS = {"analysis": "analysis_output", "ci_pr": "ci_output", "ci_release": "release_brief"}

def load_schema(name):
    with open(SCHEMA_DIR / f"{name}.schema.json", "r", encoding="utf-8") as file:
        schema = json.load(file)
        return schema


def is_valid(schema_name, data):
    try:
        schema = load_schema(schema_name)
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError:
        return False
    return True

def parse_output(mode, text):
    pass

def build_fallback(mode, reason, static_decision, input_data):
    pass
