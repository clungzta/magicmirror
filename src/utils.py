import math
import random
from colorsys import hsv_to_rgb

def pretty_colours(how_many):
    """uses golden ratio to create pleasant/pretty colours
    returns in rgb form"""
    golden_ratio_conjugate = (1 + math.sqrt(5)) / 2
    hue = random.random()  # use random start value
    final_colours = []
    for tmp in range(how_many):
        hue += golden_ratio_conjugate * (tmp / (5 * random.random()))
        hue = hue % 1
        temp_c = [int(x * 256) for x in hsv_to_rgb(hue, 0.5, 0.95)]
        final_colours.append(tuple(temp_c))
    return final_colours