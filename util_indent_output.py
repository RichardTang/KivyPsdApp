# coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

def INDENT_OUTPUT(depth, msg):
    return ''.join(['    ' for i in range(0, depth)]) + msg
