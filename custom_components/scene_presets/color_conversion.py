from homeassistant.util.color import color_RGB_to_hs, color_xy_to_RGB


def xy_to_rgb(color):
    return tuple(color_xy_to_RGB(color[0], color[1]))


def xy_to_hs(color):
    red, green, blue = color_xy_to_RGB(color[0], color[1])
    return color_RGB_to_hs(red, green, blue)
