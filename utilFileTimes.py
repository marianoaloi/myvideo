

import json
import os
from TimeComponent import TimeComponent

from PyQt5.QtCore import QSize,  QPoint,QRect
from PyQt5.QtWidgets import QGridLayout

class UtilFilesTimes:
    def saveTimes(times,croppVideoInTRansformation,filename,posExecution="d",**kwargs):
        if(times.count() > 0):
            dumpObject=[]

            definedSize=kwargs.get("definedSize")
            definedRate=kwargs.get("definedRate")
            for i in range(0,times.count()):
                item = times.itemAt(i).widget()
                dumpObject.append({"st":item.startPointText,"du":item.duration})
            
            objectDefinition= \
            {'times':dumpObject,
                
                "posExecution":posExecution
                ,
                "definedSize":definedSize,
                "definedRate":definedRate
            }
            if(croppVideoInTRansformation):
                objectDefinition["crop"]={
                        "x":croppVideoInTRansformation.x(),
                        "y":croppVideoInTRansformation.y(),
                        "w":croppVideoInTRansformation.width(),
                        "h":croppVideoInTRansformation.height()
                    }
            with open(filename+'.json', 'w') as fp:
                json.dump(objectDefinition, fp)                                                          

    def processJson(objectFile,times,crop=None,size=None,rate=None,myVid=None):

        posExecution="d"
        def resolveTimeInFile(i):
            begin=int(i["st"])
            end=int(i["du"])
            if(begin<end):
                time = TimeComponent(begin,end,myVid)
            else:
                time = TimeComponent(end,begin,myVid)
            times(time)

        if(type(objectFile) == list):
            for i in   objectFile:
                resolveTimeInFile(i)
        else:
            for i in   objectFile["times"]:
                resolveTimeInFile(i)
            if("crop" in objectFile and crop):
                crop(QRect(QPoint(objectFile["crop"]["x"],objectFile["crop"]["y"]),
                                                        QSize(objectFile["crop"]["w"],objectFile["crop"]["h"])))
            if("definedSize" in objectFile and objectFile["definedSize"] and size)          :                                      
                size(objectFile["definedSize"])
            if("definedRate" in objectFile and objectFile["definedRate"] and rate)          :               
                rate(objectFile["definedRate"])
            posExecution=objectFile["posExecution"] if objectFile["posExecution"]  else  "d"
               
        return posExecution    
    def openJson(json):

        crop=None
        definedSize=None
        definedRate=None
        def setCrop(c):
            crop=c
        def setDefinedSize(val):
            definedSize=val
        def setDefinedRate(val):
            definedRate=val
        posExecution=times=QGridLayout();

        UtilFilesTimes.processJson(json,lambda time:times.addWidget(time),crop,definedSize,definedRate,myVid)

    def openTimes(filename,times,crop=None,size=None,rate=None,myVid=None):
         
        posExecution="d"
        if(os.path.exists(filename)):
            with open(filename, 'r') as fp:
             objectFile=json.load(fp)
             posExecution=UtilFilesTimes.processJson(objectFile,times,crop,size,rate,myVid)

        return posExecution      