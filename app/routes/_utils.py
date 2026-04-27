"""Shared utilities for route modules."""

import json
import math
from datetime import date, datetime
from decimal import Decimal


class _SafeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


DecimalEncoder = _SafeEncoder


def _sanitize(obj):
    """Recursively replace NaN/Inf floats with None for JSON safety."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def df_to_records(df):
    records = _sanitize(df.to_dict("records"))
    return json.loads(json.dumps(records, cls=_SafeEncoder))


def serialize_project(proj):
    if proj is None:
        return None
    return json.loads(json.dumps(proj, cls=DecimalEncoder))
