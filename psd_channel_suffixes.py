# coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

"""
Header mode field meanings
"""
CHANNEL_SUFFIXES = {
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
