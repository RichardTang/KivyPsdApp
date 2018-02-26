# coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

"""
Header mode field meanings

number of channels

Channel information. Six bytes per channel, consisting of:

2 bytes for Channel ID: 0 = red, 1 = green, etc.;

-1 = transparency mask; -2 = user supplied layer mask, -3 real user supplied layer mask (when both a user mask and a vector mask are present)


"""
CHANNEL_SUFFIXES = {
    -3: 'real layer mask',
    -2: 'layer mask',
    -1: 'A',
    0: 'R',
    1: 'G',
    2: 'B',
    3: 'RGB',
    4: 'CMYK', 5: 'HSL', 6: 'HSB',
    9: 'Lab', 11: 'RGB',
    12: 'Lab', 13: 'CMYK',
}
