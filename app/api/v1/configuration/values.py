"""Parse and serialize configuration values by type."""

from app.core.exceptions import ValidationError


def serialize_value(value: object, value_type: str) -> str:
    if value_type == "boolean":
        if not isinstance(value, bool):
            raise ValidationError(f"Expected boolean value, got {type(value).__name__}")
        return "true" if value else "false"
    if value_type == "integer":
        return str(int(value))  # type: ignore[arg-type]
    if value_type == "string":
        return str(value)
    raise ValidationError(f"Unsupported configuration value_type: {value_type}")


def parse_value(raw: str, value_type: str) -> bool | int | str:
    if value_type == "boolean":
        return raw.lower() in {"true", "1", "yes"}
    if value_type == "integer":
        return int(raw)
    if value_type == "string":
        return raw
    raise ValidationError(f"Unsupported configuration value_type: {value_type}")
