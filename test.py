# -*- coding: utf-8 -*-
# encoding=utf8
from behave import *
import os
import rtutils
import pprint
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def mkdir_if(inDirName):
  if (os.path.isdir(inDirName) == False):
    os.mkdir(inDirName)

def searchJsonFileAndCreateImgInDir(exportDirPath):
  fullPngFile = exportDirPath + ".png"
  im = Image.open(fullPngFile)
  fullPngWidth, fullPngHeight = im.size  
  for singleJsonFile in searchJsonFileInDir(exportDirPath):
    jsonFile = singleJsonFile
    pngFile = singleJsonFile.replace(".json", ".png")
    pngBackgroudFile = singleJsonFile.replace(".json", "_bg.png")
    pngBackgroudLeftFile = singleJsonFile.replace(".json", "_left_bg.png")
    pngBackgroudRightFile = singleJsonFile.replace(".json", "_right_bg.png")
    if(os.path.isfile(pngFile)):
      continue
    if(os.path.isfile(pngBackgroudFile)):
      continue
    json_file = open(jsonFile)
    data = json.load(json_file)
    json_file.close()
    # 截取图片中一块
    x = data["bbox"]["left"]
    if (x<0): x=0
    y = data["bbox"]["top"]
    if (y<0): y=0
    x1 = data["bbox"]["right"]
    if (x1 > fullPngWidth):
      x1 = fullPngWidth
    y1 = data["bbox"]["bottom"]
    if (y1 > fullPngHeight):
      y1 = fullPngHeight
    region = im.crop((x, y, x1, y1))
    region.save(pngBackgroudFile)
    if(x>0):
      region = im.crop((0, y, x, y1))
      region.save(pngBackgroudLeftFile)
    if(x1<fullPngWidth):
      region = im.crop((x1, y, fullPngWidth, y1))
      region.save(pngBackgroudRightFile)


def exportPsdLayers(layers, destDir):
  mkdir_if(destDir)
  layerIndex = 0
  for l in layers:
    if l.visible:
      clipIndex = 0
      for clip in l.clip_layers:
#        if clip.visible:
#          #print(((' ' * indent) + "/{}").format(clip), **kwargs)
#          pngFilePath = '%s_clip_%03d.png'%(destDir, clipIndex)
#          jsonFilePath = '%s_clip_%03d.json'%(destDir, clipIndex)
#
#          if(os.path.isfile(pngFilePath)==False):
#            merged_image = l.as_pymaging()
#            if hasattr(merged_image, 'save_to_path'):
#              merged_image.save_to_path(pngFilePath)
#          #if(os.path.isfile(jsonFilePath)==True):
#          #  os.remove(jsonFilePath)
#          if(os.path.isfile(jsonFilePath)==False):
#            layerData = getLayerData(clip)
#            with open(jsonFilePath, 'w') as outfile:  
#              json.dump(layerData, outfile, indent=2)
#          pass
        clipIndex = clipIndex + 1
      #print(((' ' * indent) + "{}").format(l), **kwargs)
      if l.is_group():
        exportPsdLayers(l.layers, os.path.join(destDir, "%03d"%layerIndex))
        pass
      pngFilePath = '%s/%03d.png'%(destDir,layerIndex)
      if(os.path.isfile(pngFilePath)==False):
        merged_image = l.as_pymaging()
        if hasattr(merged_image, 'save_to_path'):
          merged_image.save_to_path(pngFilePath)
      jsonFilePath = '%s/%03d.json'%(destDir,layerIndex)
      #if(os.path.isfile(jsonFilePath)==True):
      #  os.remove(jsonFilePath)
      if(os.path.isfile(jsonFilePath)==False):
        layerData = getLayerData(l)
        with open(jsonFilePath, 'w') as outfile:  
          json.dump(layerData, outfile, indent=2)
      if hasattr(l, 'text'):
        jsonFilePath = '%s/%03d_text.json'%(destDir,layerIndex)
        #if(os.path.isfile(jsonFilePath)==True):
        #  os.remove(jsonFilePath)
        if(os.path.isfile(jsonFilePath)==False):
          layerData = getLayerData(l)
          with open(jsonFilePath, 'w') as outfile:  
            json.dump(layerData, outfile, indent=2)
    layerIndex = layerIndex + 1
  if len(os.listdir(destDir)) == 0:
    os.rmdir(destDir)


def test_001():
    psd = PSDImage.load('../psd/006.psd')
    merged_image = psd.as_pymaging()
    merged_image.save_to_path('images/006.png')
    exportPsdLayers(psd.layers, "images/006")
    searchJsonFileAndCreateImgInDir("images/006")  
if __name__ == "__main__":
  print("hello")
  test_001()

