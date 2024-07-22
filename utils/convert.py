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

def convert_duration_long(duration):
    """
    Convert the duration in seconds to a human-readable format
    :param duration: int - duration in seconds
    :return: str - duration in human-readable format
    """
    # Define the duration units in seconds
    units = [
        ('year', 365 * 24 * 60 * 60, 'years'),
        ('month', 30 * 24 * 60 * 60, 'months'),
        ('day', 24 * 60 * 60, 'days'),
        ('hour', 60 * 60, 'hours'),
        ('minute', 60, 'minutes'),
        ('second', 1, 'seconds')
    ]

    if duration == 0:
        return '0 seconds'

    result = []
    # Loop through each unit, and calculate the quotient and remainder
    for unit_name, unit_seconds, unit_name_plural in units:
        unit_value, duration = divmod(duration, unit_seconds)

        if unit_value <= 0:
            continue

        if unit_value == 1:
            result.append(f"{unit_value} {unit_name}")
            continue

        result.append(f"{unit_value} {unit_name_plural}")

    return ' '.join(result)

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

def czech_to_ascii(text):
    diacritic_mapping = {
        'á': 'a', 'č': 'c', 'ď': 'd', 'é': 'e', 'ě': 'e',
        'í': 'i', 'ň': 'n', 'ó': 'o', 'ř': 'r', 'š': 's',
        'ť': 't', 'ú': 'u', 'ů': 'u', 'ý': 'y', 'ž': 'z',
        'Á': 'A', 'Č': 'C', 'Ď': 'D', 'É': 'E', 'Ě': 'E',
        'Í': 'I', 'Ň': 'N', 'Ó': 'O', 'Ř': 'R', 'Š': 'S',
        'Ť': 'T', 'Ú': 'U', 'Ů': 'U', 'Ý': 'Y', 'Ž': 'Z'
    }
    for diacritic, ascii_char in diacritic_mapping.items():
        text = text.replace(diacritic, ascii_char)
    return text
