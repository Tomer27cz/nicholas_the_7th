def sort_guilds(_guilds: list, _allowed: list) -> list:
    """
    Separates guilds into 4 lists:
    1. allowed and connected
    2. not allowed but connected
    3. allowed but not connected
    4. not allowed and not connected

    Then sorts each list alphabetically by name
    and returns a combined list

    Can be used to sort guilds by any list of guild IDs (user's guilds, allowed guilds, etc.) - for admin panel

    :param _guilds: list of guilds
    :param _allowed: list of allowed guild IDs
    """

    acl = []  # allowed and connected
    ncl = []  # not allowed but connected

    al = []  # allowed but not connected
    nl = []  # not allowed and not connected

    for g_obj in _guilds:
        if g_obj.connected:
            if g_obj.id in _allowed:
                # is allowed and connected
                acl.append(g_obj)
                continue
            # is not allowed but connected
            ncl.append(g_obj)
            continue

        if g_obj.id in _allowed:
            # is allowed but not connected
            al.append(g_obj)
            continue

        # is not allowed and not connected
        nl.append(g_obj)

    acl.sort(key=lambda x: x.data.name)
    ncl.sort(key=lambda x: x.data.name)
    al.sort(key=lambda x: x.data.name)
    nl.sort(key=lambda x: x.data.name)

    return acl + ncl + al + nl

def sort_radios(radio_dict: dict) -> list:
    """
    Sorts radios by listened count
    :param radio_dict: dict of radios
    :return: list of radios
    """
    return sorted(list(list(radio_dict.values())[:-1]), key=lambda x: int(x['listened']), reverse=True)
