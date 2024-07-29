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

def heatmap_to_svg_lines(data_points: list[dict], duration: int) -> str:
    """
    Converts a list of data points to an SVG path
    :param data_points: list of data points {'start_time': int, 'end_time': int, 'value': int}
    :param duration: int - duration of the song in seconds
    :return: str - SVG path
    """
    width = 1000
    height = 100

    def map_to_svg_coords(end_time, value):
        x = round((end_time / duration) * width, 2)
        y = round(height - value * height, 2)
        return x, y

    path = []
    for point in data_points:
        x, y = map_to_svg_coords(point['end_time'], point['value'])
        if not path:
            path.append(f'M {x},{y}')
            continue

        path.append(f'L {x},{y}')

    path.append(f"L {width},{height}")  # Draw a line to make it a rectangle
    path.append(f"L 0,{height}")  # Draw a line to make it a rectangle
    return ' '.join(path)

def heatmap_to_svg_curves(data_points: list[dict], duration: int):
    width = 1000
    height = 100

    def map_to_svg_coords(start_time, value):
        x = round((start_time / duration) * width, 2)
        y = round(height - value * height, 2)
        return x, y

    path = []
    for i in range(len(data_points)):
        x1, y1 = map_to_svg_coords(data_points[i]['end_time'], data_points[i]['value'])
        if not path:
            path.append(f'M {x1},{y1}')
            continue

        x2, y2 = map_to_svg_coords(data_points[i - 1]['end_time'], data_points[i - 1]['value'])
        cp1_x = round(x1 + (x2 - x1) / 3, 2)
        cp2_x = round(x2 - (x2 - x1) / 3, 2)

        path.append(f'C {cp1_x},{y1} {cp2_x},{y2} {x2},{y2}')

    path.append(f"L {width},{height}")
    path.append(f"L 0,{height}")
    path_str = ' '.join(path)

    return path_str

    # exp = f'<svg version="1.2" viewBox="0 0 1000 100"><path d="{path_str}" fill="white"/></svg>'
    # return exp

def heatmap_to_svg_curves_improved(data_points: list[dict], duration: int):
    len_points = len(data_points)
    width = 1000
    height = 100

    def calculate_tangent(point_1, point_2):
        """ Calculate the slope (a) and intercept (b) of the line between two points. """
        a = (point_2[1] - point_1[1]) / (point_2[0] - point_1[0])
        b = point_1[1] - a * point_1[0]
        return a, b

    def influence(xj, xi, xk):
        """ Calculate the influence of the tangents at xi and xk on the point xj. """
        Fi = (1 + math.cos(math.pi * (xj - xi) / (xk - xi))) / 2
        Fk = 1 - Fi
        return Fi, Fk

    def point(t, value):
        """ Convert a (time, value) point into SVG (x, y) coordinates. """
        return t / duration * width, (1 - value) * height

    points = [point(d['start_time'], d['value']) for d in data_points]
    points.append(point(data_points[-1]['end_time'], data_points[-1]['value']))

    svg_path = f"M {points[0][0]},{points[0][1]} "

    for i in range(len_points - 1):
        p0, p1 = points[i], points[i + 1]
        if i == 0:
            a0, b0 = calculate_tangent(p0, p1)
        else:
            a0, b0 = calculate_tangent(points[i - 1], p1)

        if i == len_points - 2:
            a1, b1 = calculate_tangent(p0, p1)
        else:
            a1, b1 = calculate_tangent(p0, points[i + 2])

        for j in range(1, len_points + 1):
            xj = p0[0] + (p1[0] - p0[0]) * j / len_points
            Fi, Fk = influence(xj, p0[0], p1[0])
            yj = Fi * (a0 * xj + b0) + Fk * (a1 * xj + b1)
            svg_path += f"L{round(xj, 2)},{round(yj, 2)} "

    svg_path.append(f"L {width},{height}")  # Draw a line to make it a rectangle
    svg_path.append(f"L 0,{height}")  # Draw a line to make it a rectangle

    return svg_path

    # exp = f'<svg version="1.2" viewBox="0 0 1000 100"><path d="{svg_path}" fill="white"/></svg>'
    # return exp

def heatmap_to_svg_crtb(data_points: list[dict], duration: int):
    width = 1000
    height = 100

    def rl(ll, dec=2):
        return [round(p, dec) for p in ll]

    def catmull_rom_to_bezier(p0, p1, p2, p3):
        """Convert Catmull-Rom points to Bezier control points."""
        c1 = 1 / 6
        b1 = [p1[0] + c1 * (p2[0] - p0[0]), p1[1] + c1 * (p2[1] - p0[1])]
        b2 = [p2[0] - c1 * (p3[0] - p1[0]), p2[1] - c1 * (p3[1] - p1[1])]

        return rl(p1, 2), rl(b1, 2), rl(b2, 2), rl(p2, 2)

    def create_svg_path(points):
        """Create an SVG path string for a set of points using Catmull-Rom to Bezier conversion."""
        n = len(points)
        path = []

        for i in range(n - 1):
            if i == 0:
                p0 = points[0]
                p1 = points[0]
                p2 = points[1]
                p3 = points[2]
            elif i == n - 2:
                p0 = points[i - 1]
                p1 = points[i]
                p2 = points[i + 1]
                p3 = points[i + 1]
            else:
                p0 = points[i - 1]
                p1 = points[i]
                p2 = points[i + 1]
                p3 = points[i + 2]

            b0, b1, b2, b3 = catmull_rom_to_bezier(p0, p1, p2, p3)
            if i == 0:
                path.append(f'M {b0[0]},{b0[1]}')
            path.append(f'C {b1[0]},{b1[1]} {b2[0]},{b2[1]} {b3[0]},{b3[1]}')

        path.append(f"L {width},{height}")  # Draw a line to make it a rectangle
        path.append(f"L 0,{height}")  # Draw a line to make it a rectangle

        return ' '.join(path)

    # Convert intensity values to points
    points = []
    for value in data_points:
        mid_time = (value['start_time'] + value['end_time']) / 2
        points.append([mid_time, value['value']])

    # Scale y-coordinates to fit within the SVG height and invert to match SVG coordinate system
    scaled_points = []
    for point in points:
        scaled_points.append([(point[0] / duration) * width, height - (point[1] * height)])

    # Generate SVG
    svg_path = create_svg_path(scaled_points)

    return svg_path

    # exp = f'<svg version="1.2" viewBox="0 0 1000 100"><path d="{svg_path}" fill="white"/></svg>'
    # return exp

def heatmap_to_svg(data_points: list[dict], duration: int):
    try:
        duration = int(duration)
    except ValueError:
        duration = int(data_points[-1]['end_time'])

    return heatmap_to_svg_crtb(data_points, duration)