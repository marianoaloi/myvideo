import subprocess
import math
import ffmpeg
import os

from PyQt5.QtCore import QObject,  pyqtSignal,QRect

import re

from util import Util

from utilFileTimes import UtilFilesTimes
import logging

import sys
levelLog=[x.replace("--log=",'') for x in sys.argv if '--log=' in x]
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',filename='videos.log', encoding='utf-8', level=logging.ERROR if len(levelLog) == 0 else  getattr(logging,[x.replace("--log=",'') for x in sys.argv if '--log=' in x][0]))



class ManiopulateVideoFFMPEG(QObject):
    finishedFFSignal = pyqtSignal()
    progress = pyqtSignal(str)
    progressError = pyqtSignal(str)
    ignore_errors=False


    def __init__(self, fileIn,temps,ignore_errors:bool=False,staysamesize:bool=False,**kwargs):
        super().__init__()
        self.temps=temps
        if("!" in fileIn):
            os.rename(fileIn,fileIn.replace("!",""))
            os.rename(fileIn+".json",fileIn.replace("!","")+".json")
            fileIn=fileIn.replace("!","")
        self.fileInp=fileIn
        self.fileOut= fileIn.replace("'","") \
                        .replace('"',"") \
                        .replace(' ',"") \
                        +".mp4"
        self.fileOutArray=[]
        self.ignore_errors=ignore_errors
        self.staysamesize=staysamesize
        self.croppVideoInTRansformation=kwargs.get("crop")
        
        self.definedSize=kwargs.get("definedSize")
        self.definedRate=kwargs.get("definedRate")

        try:
            self.ffmpegOb = ffmpeg.probe(fileIn)#["streams"]
            audioObj = [x for x in self.ffmpegOb["streams"] if  'channels' in x ]
            self.hasAudio = len(audioObj) > 0
        except Exception as err:
            self.hasAudio = False

            logging.error(f"Error sound {err} {self.fileInp}") 

        rate=self.rateCalc()
        self.outputArgs = {
                        'vsync':'0' , 
                        'c:v':'h264_nvenc',
                        'crf': '28' , 
                        'c:a':'aac', 
                        'b:a':'128k' , 
                        #'strict':'-2' ,
                        # 's': dimention,
                        # 'vf':'hwupload,scale_npp={}'.format(dimention),
                        'b:v':str(rate)+'k', 
                        'maxrate':str(rate)+'k', 
                        'bufsize':'130M' ,
                        'pix_fmt':'yuv420p' 
                        }

    def rateCalc(self):

        if(self.definedRate):
            return str(self.definedRate)

        rate=Util.maxRateVideo
        try:
            videoObj = [x for x in self.ffmpegOb["streams"] if  'width' in x ][0]
            rate=math.trunc(int(videoObj['bit_rate'])/1000)
            if(rate>Util.maxRateVideo and not self.staysamesize):
                rate=Util.maxRateVideo
        except Exception as err:
            logging.error(f"Error rateCalc {err} {self.fileInp}") 
            rate=Util.maxRateVideo

        
        return rate


    def dimentionCalc(self):

        if(self.definedSize):
            return str(self.definedSize)

        if(self.croppVideoInTRansformation):
            return "{}x{}".format(self.croppVideoInTRansformation.width()-1 , self.croppVideoInTRansformation.height()-1)

        width = 640
        height = 360
        try:
            videoObj = [x for x in self.ffmpegOb["streams"] if  'width' in x ][0]
            width = videoObj['width']
            height = videoObj['height']

            if((width > 640 or height > 640) and not self.staysamesize):
                if(width >= height):
                    height = math.trunc((height*640)/width)
                    width = 640
                else:
                    width = math.trunc((width*640)/height)
                    height = 640
                if(os.getenv('invert')):
                    aux = height
                    height = width
                    width = aux

        except Exception as err:
            logging.error(f"Error in thread dimentionCalc {err} {self.fileInp}")            
            width = 640
            height = 360  

        return str(width-1)+"x"+str(height-1) 

    def input(self,fileInp,error:bool):
        parameters={
                    'hwaccel':'cuda',
                    'hwaccel_device':'0',
                    
                    'extra_hw_frames':'8'
                    }
        if(not error):
            parameters['loglevel']='error'
            parameters['hwaccel_output_format']='cuda'
        return ffmpeg.input(filename=fileInp,
                **parameters
                ) #,loglevel='fatal' 
    def copy(self,wid,copyFileName):
        gg = self.croppVideoInTRansformation
        #ffmpeg -i TqhxK5-J_Gabii15Soares.wmv -vf mpdecimate,setpts=N/FRAME_RATE/TB out.mp4
        output={}
        if(wid):
            start = int(wid.startPointText)
            diff = int(wid.duration)-int(wid.startPointText)
            output['ss'] = str(start)+'ms'
            output['t'] = str(diff)+'ms'
        if(gg):
            output['c:a'] = 'copy'
            output['filter:v'] = "crop=w={}:h={}:x={}:y={}".format(gg.width(),gg.height(),gg.x(),gg.y())
            output['c:v']='h264_nvenc';
        else:
            output['c'] = 'copy'
        
        cmd = self.input(self.fileInp,True).output(copyFileName,**output).overwrite_output()

        args = cmd.compile()

        self.logRunOutPut(args)


    def ffmpegCuts(self):
        try:
            # logging.info(f"Cuts ",self.fileInp,self.fileOut,len(self.temps))
            self.__ffmpegCuts(False)
        except:
            try:
                os.system("ls -lisa '{}'*".format(self.fileInp[:self.fileInp.rfind("/")+11]))
                self.__ffmpegCuts(True)
            except Exception as e:
                try:
                    os.system("ls -lisa '{}'*".format(self.fileInp[:self.fileInp.rfind("/")+11]))
                    self.progressError.emit(str(e))
                    self.ffmpegConcat(True)
                except Exception as e:
                    self.progressError.emit(str(e))




    def __ffmpegCuts(self,error:bool):
        
        extension = self.fileInp[self.fileInp.rfind('.'):]
        output = self.outputArgs

        if(not error):
            output['vf'] = 'hwupload,scale_npp={}'.format(self.dimentionCalc())
            # output['filter:v'] = '""'.format()
            del output['pix_fmt']
        for poss in range(0,len(self.temps)):
            wid = self.temps[poss]
            copyFileName='{}_copy{}{}'.format(self.fileInp,poss,extension)
            self.fileOut='{}{}.mp4'.format(self.fileInp,poss)
            self.fileOutArray.append(self.fileOut)
            self.copy(wid,copyFileName)


            cmd = self.input(copyFileName,error).output(self.fileOut,**output).overwrite_output()

            args = cmd.compile()

            self.logRunOutPut(args)

            os.remove(copyFileName)
        self.finishedFFSignal.emit()


    def prepare(self,m):
        gg = self.croppVideoInTRansformation
        if(gg):
            return '[0:v]scale_npp={0},crop={3}:{4}:{5}:{6},hwdownload,format=nv12[base{1}];[base{1}]{2}'.format(self.dimentionCalc()
                    ,m.group(2),m.group(1),gg.width()-1,gg.height()-1,gg.x(),gg.y())
        else:
            return '[0:v]scale_npp={0},hwdownload,format=nv12[base{1}];[base{1}]{2}'.format(self.dimentionCalc(),m.group(2),m.group(1))

    def ffmpegCutConcat(self):
        try:
            cuts=[]
            for poss in range(0,len(self.temps)):
                cuts.append(self.input('{}{}.mp4'.format(self.fileInp,poss),False))

            cmd = (
                    ffmpeg
                    .concat(
                        *cuts,
                        v=1,a=1 if self.hasAudio else 0
                    )
                    .filter('fps', fps=25)
                    # .filter("crop","w={}:h={}:x={}:y={}".format(gg.width(),gg.height(),gg.x(),gg.y()))                              
                    .output(self.fileOut, **self.outputArgs)
                    
                ).overwrite_output()

            args =  cmd.compile()

            self.logRunOutPut(args)

            for poss in range(0,len(self.temps)):
                os.remove('{}{}.mp4'.format(self.fileInp,poss))
            self.finishedFFSignal.emit()

        except Exception as e:
                        self.progressError.emit(str(e))

    def ffmpegConcat(self,turnOffCut=False):
        msgError="Concat problem in video não tem tamanho "+self.fileOut
        try:
            # logging.info(f"Concat       ",self.fileInp,self.fileOut,len(self.temps))
            self.__ffmpegConcat(False)
            if(not os.path.exists(self.fileOut) or os.path.getsize(self.fileOut)<1000):
                raise Exception(msgError)
        except:
            try:
                self.__ffmpegConcat(True)
                if(not os.path.exists(self.fileOut) or os.path.getsize(self.fileOut)<1000):
                    raise Exception(msgError)
            except Exception as e:
                try:
                    if(not os.path.exists(self.fileOut) or os.path.getsize(self.fileOut)<1000):
                        w,h=[int(x) for x in self.dimentionCalc().split("x")]
                        self.croppVideoInTRansformation = QRect(0,0,w,h)
                        self.__ffmpegConcat(True)
                except Exception as e:
                    try:
                        if(not turnOffCut):
                            self.ffmpegCuts()
                        self.ffmpegCutConcat()
                    except Exception as e:
                        msgError+=" "+str(e)
                        self.progressError.emit(msgError)
                        raise Exception(msgError)



                
    def __ffmpegConcat(self,error:bool):
        gg = self.croppVideoInTRansformation
        if(gg):
            extension = self.fileInp[self.fileInp.rfind('.'):]
            copyFileName='{}_copy{}{}'.format(self.fileInp,"0",extension)
            self.copy(None,copyFileName)
            in_file = self.input(copyFileName,error)
        else:
            in_file = self.input(self.fileInp,error)
        

        concatPartsAudio = lambda  start,finish:in_file.audio \
                                    .filter('atrim', start=start, end=finish) \
                                    .filter('asetpts', 'PTS-STARTPTS')  
        concatPartsVideo = lambda  start,finish: in_file.video \
                                    .trim(start=start, end=finish) \
                                    .setpts('PTS-STARTPTS') #.filter('format','nv12,hwupload')

        cuts=[]

        for poss in range(0,len(self.temps)):
            wid = self.temps[poss]
            pos = int(wid.startPointText)/1000
            end = int(wid.duration)/1000
            cuts.append(concatPartsVideo(pos,end))
            if(self.hasAudio):
                cuts.append(concatPartsAudio(pos,end))


        
        

        cmd = (
                ffmpeg
                .concat(
                    *cuts,
                    v=1,a=1 if self.hasAudio else 0
                )
                .filter('fps', fps=25)
                # .filter("crop","w={}:h={}:x={}:y={}".format(gg.width(),gg.height(),gg.x(),gg.y()))                              
                .output(self.fileOut, **self.outputArgs)
                
            ).overwrite_output()

        args =  cmd.compile()
        if(not error):
            args = list(map(lambda x:re.sub('\[0:v\]([^\]]+(\d)])',self.prepare,x), cmd.compile()))
        

        self.fileOutArray.append(self.fileOut)
        # # process = (
        # #     cmd
        # #     
        # #     .run_async(quiet=True)
        # # )
        self.logRunOutPut(args)

        if(gg):
            os.remove(copyFileName)
        self.finishedFFSignal.emit()

    def logRunOutPut(self,args):

        # logging.info(f" ".join(args), flush=True)
        commandRebuild=" ".join([x if not " " in x else '"{}"'.format(x) for x in args])
        self.progress.emit(commandRebuild)

        process=subprocess.Popen(args=args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        # shell=True,
        encoding='utf-8',
        errors='replace')


        while True:
            realtime_output = process.stdout.readline()

            if realtime_output == '' and process.poll() is not None:
                break

            if realtime_output and not self.ignore_errors:
                # logging.info(frealtime_output.strip(), flush=True)
                self.progressError.emit(realtime_output.strip())
                raise MaloiException
            logging.debug(realtime_output.replace("\n",""))
        try:
            endFileDelivery=args[len(args)-2]
            if(not os.path.exists(endFileDelivery) or os.path.getsize(endFileDelivery)<1000):
                raise Exception("video não tem tamanho command:"+commandRebuild)
            if(len([x for x in ffmpeg.probe(endFileDelivery)["streams"] if  'width' in x ])==0):
                w,h=[int(x) for x in self.dimentionCalc().split("x")]
                self.croppVideoInTRansformation = QRect(0,0,w,h)
                # logging.info(f"deu erro com {}".format(ffmpeg.probe(args[len(args)-2])))
                raise MaloiException
        except Exception as e:

                self.progressError.emit("Erro no processamento da saida de vídeo error:'{}' out file:'{}'".format(str(e),args[len(args)-2]))
                raise e

        

class MaloiException(Exception):
    pass

from PyQt5.QtWidgets import QGridLayout,QApplication
class FFInit:
    def __init__(self) -> None:
        super().__init__()
        label="/mnt/BACKUP/individual/teste/0qWNGIhLge_Gostosa dando pro amigo do marido.mp4"
        self.crop=None
        times=QGridLayout()
        UtilFilesTimes.openTimes(label+'.json',
                lambda time:times.addWidget(time),
                lambda crop:self.setCrop(crop),None,None)
        temps=[]
        for poss in range(0,times.count()):
            temps.append(times.itemAt(poss).widget())
        m=ManiopulateVideoFFMPEG(label,temps,ignore_errors=True)
        m.progress.connect(print)
        m.progressError.connect(print)
        # m.ffmpegConcat()
        m.ffmpegCuts()
    def setCrop(self,croppp):
            self.crop=croppp
if __name__ == "__main__":
    app = QApplication([])
    FFInit()

    