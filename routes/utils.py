def parse_int(val, default=None):
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return default

def parse_float(val, default=None):
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return default