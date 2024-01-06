def is_float(value) -> bool:
    if value is None:
        return False
    # noinspection PyBroadException
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

def check_isdigit(var) -> bool:
    try:
        int(var)
        return True
    except (ValueError, TypeError):
        return False
