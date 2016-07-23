


def animate_sin(operation):
    brightness_max = 9
    half_brightness_max = brightness_max / 2
    two_pi = math.pi * 2

    origo_x, origo_y = 2, 2

    max_distance = hypot(origo_x, origo_y)
    double_max_distance = max_distance * 2
    offset = 0
    last_t = now()

    while True:
        for x in range(0, 5):
            dist_x = x - origo_x
            for y in range(0, 5):
                dist_y = y - origo_y

                distance = (math.fabs(hypot(dist_x, dist_y)) /
                            double_max_distance)
                distance = (distance + (offset / operation)) % 1

                sin = math.sin(distance * two_pi - math.pi)

                value = round(sin * half_brightness_max + half_brightness_max)

                display.set_pixel(x, y, value)

        t_now = now()
        delta_t = t_now - last_t
        offset += delta_t * 0.001
        last_t = t_now
        yield from sleep(10)
