"""A small deterministic JSON Schema validator for reviewed operation schemas."""

from __future__ import annotations

import re
from typing import Any, Mapping

from .errors import SchemaValidationError


def validate_json_schema(value: Any, schema: Mapping[str, Any], path: str = "$") -> None:
    """Validate the supported JSON Schema subset and raise one stable error.

    Schemas are reviewed operation metadata, not executable user code.  The
    implementation intentionally supports declarative validation keywords only.
    """

    if not isinstance(schema, Mapping):
        raise SchemaValidationError(f"{path}: schema must be an object")
    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(f"{path}: must equal the schema constant")
    if "enum" in schema:
        choices = schema["enum"]
        if not isinstance(choices, list) or value not in choices:
            raise SchemaValidationError(f"{path}: must be one of the schema enum values")
    for keyword, matcher in (("allOf", all), ("anyOf", any), ("oneOf", None)):
        if keyword not in schema:
            continue
        alternatives = schema[keyword]
        if not isinstance(alternatives, list) or not alternatives:
            raise SchemaValidationError(f"{path}: {keyword} must be a non-empty list")
        matches = sum(_matches(value, candidate, path) for candidate in alternatives)
        valid = matches == len(alternatives) if matcher is all else matches >= 1 if matcher is any else matches == 1
        if not valid:
            raise SchemaValidationError(f"{path}: does not satisfy {keyword}")
    expected = schema.get("type")
    if expected is not None and not _is_type(value, expected):
        raise SchemaValidationError(f"{path}: must be of type {_type_label(expected)}")
    if isinstance(value, Mapping):
        _validate_object(value, schema, path)
    elif isinstance(value, list):
        _validate_array(value, schema, path)
    elif isinstance(value, str):
        _validate_string(value, schema, path)
    elif _is_number(value):
        _validate_number(value, schema, path)


def _matches(value: Any, schema: Any, path: str) -> bool:
    try:
        validate_json_schema(value, schema, path)
    except SchemaValidationError:
        return False
    return True


def _is_type(value: Any, expected: Any) -> bool:
    choices = expected if isinstance(expected, list) else [expected]
    return any({"null": value is None, "boolean": isinstance(value, bool), "object": isinstance(value, Mapping), "array": isinstance(value, list), "string": isinstance(value, str), "number": _is_number(value), "integer": isinstance(value, int) and not isinstance(value, bool)}.get(name, False) for name in choices)


def _type_label(expected: Any) -> str:
    return ", ".join(expected) if isinstance(expected, list) else str(expected)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_object(value: Mapping[str, Any], schema: Mapping[str, Any], path: str) -> None:
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise SchemaValidationError(f"{path}: required must be a list")
    for name in required:
        if not isinstance(name, str) or name not in value:
            raise SchemaValidationError(f"{path}: missing required property {name!r}")
    properties = schema.get("properties", {})
    if not isinstance(properties, Mapping):
        raise SchemaValidationError(f"{path}: properties must be an object")
    additional = schema.get("additionalProperties", True)
    for name in sorted(value):
        child_path = f"{path}.{name}"
        if name in properties:
            validate_json_schema(value[name], properties[name], child_path)
        elif additional is False:
            raise SchemaValidationError(f"{child_path}: additional properties are not allowed")
        elif isinstance(additional, Mapping):
            validate_json_schema(value[name], additional, child_path)


def _validate_array(value: list[Any], schema: Mapping[str, Any], path: str) -> None:
    for keyword, comparator in (("minItems", lambda actual, bound: actual < bound), ("maxItems", lambda actual, bound: actual > bound)):
        if keyword in schema and (not isinstance(schema[keyword], int) or comparator(len(value), schema[keyword])):
            raise SchemaValidationError(f"{path}: violates {keyword}")
    if "items" in schema:
        for index, item in enumerate(value):
            validate_json_schema(item, schema["items"], f"{path}[{index}]")


def _validate_string(value: str, schema: Mapping[str, Any], path: str) -> None:
    for keyword, comparator in (("minLength", lambda actual, bound: actual < bound), ("maxLength", lambda actual, bound: actual > bound)):
        if keyword in schema and (not isinstance(schema[keyword], int) or comparator(len(value), schema[keyword])):
            raise SchemaValidationError(f"{path}: violates {keyword}")
    if "pattern" in schema:
        pattern = schema["pattern"]
        if not isinstance(pattern, str) or re.search(pattern, value) is None:
            raise SchemaValidationError(f"{path}: does not match pattern")


def _validate_number(value: int | float, schema: Mapping[str, Any], path: str) -> None:
    for keyword, comparator in (("minimum", lambda actual, bound: actual < bound), ("maximum", lambda actual, bound: actual > bound)):
        if keyword in schema and (not _is_number(schema[keyword]) or comparator(value, schema[keyword])):
            raise SchemaValidationError(f"{path}: violates {keyword}")
