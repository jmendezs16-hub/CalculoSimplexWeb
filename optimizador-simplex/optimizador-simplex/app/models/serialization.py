from datetime import date, datetime
from decimal import Decimal
from enum import Enum


def serialize_model(instance, exclude=None):
    """Serialize mapped columns while preserving decimal precision."""
    excluded = set(exclude or ())
    data = {}

    for column in instance.__table__.columns:
        if column.name in excluded:
            continue

        value = getattr(instance, column.name)
        if isinstance(value, Decimal):
            value = format(value, "f")
        elif isinstance(value, (datetime, date)):
            value = value.isoformat()
        elif isinstance(value, Enum):
            value = value.value
        data[column.name] = value

    return data
