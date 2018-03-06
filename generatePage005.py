# coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from struct import unpack, calcsize
from PIL import Image
import os
import json

dirPath = 'images/005'

for singleFile in os.listdir(dirPath):
    singleFilePath = os.path.join(dirPath, singleFile)
    if singleFile.find(".json")>0:
        json_file = open(singleFilePath)
        data = json.load(json_file)
        json_file.close()
        print singleFilePath
        print data["bbox"]["left"]
print 'hello'
