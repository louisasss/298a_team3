import json
from pathlib import Path

import jsonschema
import pytest

COMMON = Path(__file__).parent.parent
SCHEMA_NAMES = ["analysis_output", "analysis_input"]
FIXTURES = COMMON / "fixtures" 


def cases(kind):
    return [
        (name, path)
        for name in SCHEMA_NAMES
        for path in sorted((FIXTURES / name / kind).glob("*.json"))
    ]

def load(path):
    """
    read the file and turn the JSON text into a Python dict
    """
    return json.loads(path.read_text())

def schema_path(name):
    return COMMON / "schemas" / f"{name}.schema.json"

@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_is_well_formed(name):
    """
    load the schema, then check it with Draft202012Validator.check_schema
    """
    schema = load(schema_path(name))
    jsonschema.Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize("name,path", cases("valid"), ids=[f"{n}/{p.name}" for n, p in cases("valid")])
def test_valid_examples_pass(name, path):
    """
    load schema + example, validate — no error means pass
    """
    schema = load(schema_path(name))
    example = load(path)
    jsonschema.validate(instance=example, schema=schema)
    

@pytest.mark.parametrize("name,path", cases("invalid"), ids=[f"{n}/{p.name}" for n, p in cases("invalid")])
def test_invalid_examples_fail(name, path):
    """    
    load schema + example, expect jsonschema.ValidationError
    """    
    schema = load(schema_path(name))
    example = load(path)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=example, schema=schema)