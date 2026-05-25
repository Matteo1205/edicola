# conversione di stringe in numeri interi con gestione degli errori
def parse_int(val, default=None):
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return default

# conversione di stringhe in numeri decimali con gestione degli errori
def parse_float(val, default=None):
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return default