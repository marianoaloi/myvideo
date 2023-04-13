

import getopt
import math
import os
import sys
from PyQt5.QtWidgets import QDialog,QStyle,QApplication,QGridLayout, QShortcut 
from PyQt5.QtCore import QObject,pyqtSignal,Qt,QThread,QRect
from PyQt5.QtGui import QKeySequence,QIcon

from datetime import datetime
import hashlib , pathlib
import time
import pymongo
import ffmpeg


from PyQt5 import uic
import subprocess
from send2trash import send2trash
from time import sleep
import TimeComponent
from ffmpegTranformation import MaloiException, ManiopulateVideoFFMPEG as ManiopulateVideoFFMPEG


uploadString=" /usr/lib/jvm/jdk1.8.0_281/bin/java -Dlogback.configurationFile=/opt/maloi/eclipse/git/4shared_Java/src/logback.xml -Dlog4j.configurationFile=/opt/maloi/eclipse/git/4shared_Java/src/log4j2.xml  -cp ~/Desktop/see.jar br.com.aloi.upload.Upload4Shared  "
x24String=" /usr/lib/jvm/jdk1.8.0_281/bin/java -Dlogback.configurationFile=/opt/maloi/eclipse/git/4shared_Java/src/logback.xml -Dlog4j.configurationFile=/opt/maloi/eclipse/git/4shared_Java/src/log4j2.xml  -cp ~/Desktop/see.jar br.com.aloi.upload.XVideo24Shared  "
class loggerM(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str)

    def __init__(self,command,concat=True):
        super().__init__()
        self.command=command
        self.concat=concat

    textCol=[]
    def logger(self):
        process= subprocess.Popen(self.command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                encoding='utf-8',
                                errors='replace',
                                shell=True)
        while True:
            realtime_output = process.stdout.readline()

            if realtime_output == '' and process.poll() is not None:
                break

            if realtime_output:
                if(self.concat):
                    self.textCol.append(realtime_output.strip())
                    self.progress.emit("<br>".join(self.textCol))
                else:
                     self.progress.emit(realtime_output.strip())

        self.finished.emit()

class DialogResume(QDialog):

    closeVideoSignal = pyqtSignal()

    def initial(self):
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)),"dialog.ui"),self)
        if(self.byChoice and self.posExecution):
            return
        self.concatTemps.stateChanged        .connect(self.showCommands)
        self.removeOriginal.stateChanged     .connect(self.showCommands)
        self.IgnoreError.stateChanged        .connect(self.showCommands)
        self.sendTo4.stateChanged            .connect(self.showCommands)
        self.execute.clicked                 .connect(self.CopySendExecute)
        self.closeButton.clicked             .connect(self.closeFinal)


        self.log.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.closeButton.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserStop))
        
        

        QShortcut(QKeySequence(Qt.Key.Key_F), self).activated.connect(self.CopySendExecute)
        QShortcut(QKeySequence(Qt.Key.Key_3), self).activated.connect(self.CopySendExecute)
        QShortcut(QKeySequence(Qt.Key.Key_D), self).activated.connect(self.ConcatExecute)
        QShortcut(QKeySequence(Qt.Key.Key_6), self).activated.connect(self.ConcatExecute)
        
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self).activated.connect(self.closeFinal)

        self.showCommands()
    
    def __init__(self,label:str,times,**kwargs):

        if(times.count()==0):
            return

        super().__init__()
        self.posExecution = kwargs.get("posExecution")

        self.byChoice = kwargs.get("byChoice")
        self.label = label
        self.md5=""
        self.outputfile = self \
                        .label.replace("'","") \
                        .replace('"',"") \
                        .replace(' ',"") \
                        .replace('(',"") \
                        .replace(')',"") \
                        +".mp4"
        try:
            self.times = times
            
            self.croppVideoInTRansformation=kwargs.get("crop")
            
            self.definedSize=kwargs.get("definedSize")
            self.definedRate=kwargs.get("definedRate")
        except Exception as e :
            print("Error at Dialog ",str(e))
        self.initial()
        
        

        if(self.posExecution and self.posExecution == "d"):
            self.CopySendExecute()
        elif(self.posExecution and self.posExecution == "f"):
            self.ConcatExecute()
        elif(self.posExecution and self.posExecution == "e"):
            self.CopyNOTSendExecute()

    def closeFinal(self) -> bool:
        self.closeVideoSignal.emit()
        return self.close()

    def ConcatExecute(self):
        # self.concatTemps = QCheckBox()
        self.concatTemps.setChecked(True)
        self.CopySendExecute()

    def CopyNOTSendExecute(self):         
        self.sendTo4.setChecked(False)
        self.CopySendExecute()

    def CopySendExecute(self):
        timecount = self.times.count()
        # self.execute=QPushButton()

        if(self.byChoice):
            if(self.posExecution):
                return
            else:
                return self.close()
        if(not self.execute.isEnabled):
            return
        self.execute.setEnabled(False)

        if timecount <= 0 :
            return

        ''' Lambda '''
        concatFiles       = lambda  a:"'"+self.label+'_'+str(a)+".mp4'"        
        ''' Lambda '''
        temps=[]
        for poss in range(0,timecount):
            temps.append(self.times.itemAt(poss).widget())

        self.threadConversion = QThread()
        ffm = ManiopulateVideoFFMPEG(self.label,temps , \
             self.IgnoreError.isChecked() , \
             staysamesize=self.sameSize.isChecked(), \
             crop=self.croppVideoInTRansformation \
            ,definedSize=self.definedSize \
            ,definedRate=self.definedRate )
        ffm.moveToThread(self.threadConversion)
        

        if(not self.concatTemps.isChecked()):
            self.threadConversion.started.connect(ffm.ffmpegCuts)
        else:
            self.threadConversion.started.connect(ffm.ffmpegConcat)

        try:
            
            ffm.finishedFFSignal.connect(self.threadConversion.quit)
            ffm.finishedFFSignal.connect(ffm.deleteLater)
            self.threadConversion.finished.connect(self.threadConversion.deleteLater)
            ffm.progress.connect(self.putLog)
            ffm.progressError.connect(self.putLogError)

            self.threadConversion.finished.connect(self.finishCmd)
            time.sleep(.6)

            self.threadConversion.start()
            time.sleep(.6)
        except MaloiException as e:
            self.threadConversion.terminate()
            print(e)
            pass

    textCol=[]
    def putLogError(self,i):
        msg="Occur an error in FFMPEG "+str(i)
        self.execute.setEnabled(self.threadConversion.isFinished() )
        self.putLog(msg)
        if(str(i).find('No such file or directory') >= 0):
            self.closeVideoSignal.emit()
            self.close()

        # raise MaloiException(msg);
    def putLog(self,i):
        # print(i)
        self.textCol.append(i)
        self.log.setText("<br>".join(self.textCol));
        x = self.scrollArea.verticalScrollBar().maximum()
        self.scrollArea.verticalScrollBar().setValue(x)

    def finishCmd(self):
        print("Finish Command")
        self.thread2 = QThread()
        lg=loggerM(self.textAreaCommand.toPlainText())
        lg.moveToThread(self.thread2)
        self.thread2.started.connect(lg.logger)
        lg.finished.connect(self.thread2.quit)
        lg.finished.connect(lg.deleteLater)
        self.thread2.finished.connect(self.thread2.deleteLater)
        lg.progress.connect(self.putLog)

        self.thread2.finished.connect(self.finishExec)


        time.sleep(.6)
        self.thread2.start()
        time.sleep(.6)

    def getMD5(self)->str:
        try:
            return hashlib.md5(pathlib.Path(self.label).read_bytes()).hexdigest()
        except Exception as e:
            print(e)
            return ''
            
    
    def finishExec(self):
        print("Finish All")
        self.execute.setEnabled(True)
        if(self.removeOriginal.isChecked()):
            self.deleteFile(self.getMD5(),self.label)

        self.putLog("FINISH HIM")
        if(self.closeSystem.isChecked()):
            self.closeFinal()

    def deleteFile(self,md5,label):
        try:
            pymongo.MongoClient(
                'mongodb://maloi:J4v4P0w3r@192.168.25.42:27017/?authSource=admin&readPreference=primary&appname=MaloyPython&directConnection=true&ssl=false'
                )["4shared"]["posts"].update_many({'md5':md5},{'$set':{'deleted':datetime.now()},'$unset':{'statustransition':"deleted"}})
            
            send2trash(label);
            send2trash(label+".json");
        except Exception as e:
            print(e)

    def showCommands(self):
        cmd=self.command(timecount=self.times.count(),inputfile=self.label,outputfile=self.outputfile,md5=self.getMD5(),
                    concatTemps=self.concatTemps.isChecked(),sendTo4=self.sendTo4.isChecked())
        if(not cmd):
            return
        self.textAreaCommand.setPlainText(cmd+ " echo Finish")

    def command(self,timecount,inputfile,outputfile,md5="",concatTemps=True,sendTo4=True)->str:
        command = 'echo Start && '
        
        if timecount <= 0 :
            return
        
        ''' Lambda '''
        concatFiles       = lambda  a:"'"+inputfile+str(a)+".mp4'" 
        ''' Lambda '''
            
        if(sendTo4 ):
            filesString=(' '.join(map(concatFiles,range(0,timecount)))
                            if not concatTemps else f"'{outputfile}'" )+" && \\\n"
            command +="md5="+md5
            command +=(uploadString     +filesString)
            command +=(x24String        +filesString)

        return command
# QtWidgets.QDialog(self)
#             self._dialog.resize(800, 600)
#             vbox = QVBoxLayout(self._dialog)
#             text = QPlainTextEdit(self._dialog)
#             text.insertPlainText(command)
#             vbox.addWidget(text)

if __name__ == "__main__":
    app = QApplication([])
    app.setWindowIcon(QIcon('/usr/share/icons/Yaru/256x256/apps/jockey.png'))

    try:
            opts, args = getopt.getopt(sys.argv[1:],"h:f:s:")
            file = [x for x in opts if x[0] == '-f']
            position = [x for x in opts if x[0] == '-s']

            if(file and position):
                video=file[0][1]
                start=position[0][1]
                ffmpegOb = ffmpeg.probe(video)
                videoObj = [x for x in ffmpegOb["streams"] if  'width' in x ][0]
                times=QGridLayout()
                end=str(math.trunc(float(videoObj['duration'])))*1000
                times.addWidget(TimeComponent(start,end,None))
    except getopt.GetoptError as e:
        print("DialogResume -f <file> -s <milisecond to start> . "+str(e))
            
    window = DialogResume()
    window.show()
    sys.exit(app.exec())