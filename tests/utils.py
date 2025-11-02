from jsonschema import validate

RESPONSE_SCHEMA_MIN = {
    "type": "object",
    "required": ["class", "confidence"],
    "properties": {
        "class": {"type": ["string", "null"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "explanations": {"type": "array"},
        "warnings": {"type": "array"},
    },
}


def assert_min_response(body: dict):
    """Validate that the response contains at least the minimum expected schema."""
    validate(instance=body, schema=RESPONSE_SCHEMA_MIN)
