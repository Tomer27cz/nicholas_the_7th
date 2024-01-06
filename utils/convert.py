from time import gmtime, strftime

def struct_to_time(struct_time, first='date') -> str:
    """
    Converts struct_time to time string
    :param struct_time: int == struct_time
    :param first: ('date', 'time') == (01/01/1970 00:00:00, 00:00:00 01/01/1970)
    :return: str
    """
    if not isinstance(struct_time, int):
        try:
            struct_time = int(struct_time)
        except (ValueError, TypeError):
            return struct_time

    if first == 'date':
        return strftime("%d/%m/%Y %H:%M:%S", gmtime(struct_time))

    if first == 'time':
        return strftime("%H:%M:%S %d/%m/%Y", gmtime(struct_time))

    if first == 'discord':
        return strftime("%d %b %Y", gmtime(struct_time))

    return strftime("%H:%M:%S %d/%m/%Y", gmtime(struct_time))

def convert_duration(duration) -> str or None:
    """
    Converts duration(in sec) to HH:MM:SS format
    or returns 'Stream' if duration is None or 0
    if can't convert returns duration as str
    :param duration: duration in sec
    :return: str - duration in HH:MM:SS format
    """
    if duration is None or duration == 0 or duration == '0':
        return 'Stream'

    try:
        duration = int(duration)

        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60

        if hours:
            return f'{hours}:{minutes:02}:{seconds:02}'
        else:
            return f'{minutes}:{seconds:02}'
    except (ValueError, TypeError):
        return str(duration)

def to_bool(text_bool: str) -> bool or None:
    """
    Converts text_bool to bool
    if can't convert returns None
    :param text_bool: str
    :return: bool or None
    """
    bool_list_t = ['True', 'true', '1']
    bool_list_f = ['False', 'false', '0']

    if text_bool in bool_list_t:
        return True
    elif text_bool in bool_list_f:
        return False
    else:
        return None

def ascii_nospace(string: str):
    if type(string) is not str:
        raise TypeError(f"string must be str not {type(string)}")

    if not string.isascii():
        return False

    return string.replace(" ", "_")
