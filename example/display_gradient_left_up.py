import microbit


def draw_gradient2():
    offset = 0
    max_value = 9
    max_index = 5

    last_t = microbit.running_time()

    while True:
        for x in range(0, 5):
            for y in range(0, 5):
                pos = x + y
                offset_pos = (offset + pos) % max_index
                relative_pos = offset_pos / max_index
                value = round(relative_pos * max_value)
                microbit.display.set_pixel(x, y, value)

        t_now = microbit.running_time()
        delta_t = t_now - last_t
        offset += delta_t * 0.01
        last_t = t_now

        microbit.sleep(1)


draw_gradient2()
