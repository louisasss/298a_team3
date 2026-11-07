import json
from pathlib import Path

import jsonschema
import pytest

COMMON = Path(__file__).parent.parent
SCHEMA_PATH = COMMON / "schemas" / "analysis_output.schema.json"
FIXTURES = COMMON / "fixtures" / "analysis_output"


def load(path):
    """
    read the file and turn the JSON text into a Python dict
    """
    return json.loads(path.read_text())


def test_schema_is_well_formed():
    """
    load the schema, then check it with Draft202012Validator.check_schema
    """
    schema = load(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize("path", sorted((FIXTURES / "valid").glob("*.json")), ids=lambda p: p.name)
def test_valid_examples_pass(path):
    """
    load schema + example, validate — no error means pass
    """
    schema = load(SCHEMA_PATH)
    example = load(path)
    jsonschema.validate(instance=example, schema=schema)
    

@pytest.mark.parametrize("path", sorted((FIXTURES / "invalid").glob("*.json")), ids=lambda p: p.name)
def test_invalid_examples_fail(path):
    """    
    load schema + example, expect jsonschema.ValidationError
    """    
    schema = load(SCHEMA_PATH)
    example = load(path)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=example, schema=schema)
