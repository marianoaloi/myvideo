import sys, getopt,os
from PyQt5.QtCore import Qt,QUrl,pyqtSignal
from PyQt5.QtGui import QKeySequence,QIcon,QGuiApplication , QMouseEvent
from PyQt5.QtWidgets import QMainWindow,QStyle,QVBoxLayout,QFileDialog \
    ,QLabel,QGridLayout,QApplication,QLineEdit,QWidget,QSizePolicy, QShortcut 
from PyQt5.QtMultimedia import QMediaPlayer,QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5 import uic
from TimeComponent import TimeComponent
from DialogResume import DialogResume
from util import Util
from utilFileTimes import UtilFilesTimes
import datetime
import pytz
import math
from PyQt5 import sip

import re

import ffmpeg


os.environ.update({"QT_QPA_PLATFORM_PLUGIN_PATH": os.getenv('mediaproject')+"/venv_mediaproject/lib/python3.10/site-packages/PyQt5/Qt5/plugins/xcbglintegrations/libqxcb-glx-integration.so"})
class MaloiLineEdit(QLineEdit):
    def __init__(self,parent):
        super(MaloiLineEdit,self).__init__(parent)
    
    def focusOutEvent(self, a0) -> None:
        # print(self.toolTip(),"Teste")
        self.setStyleSheet('background-color:aliceblue')
        return super().focusOutEvent(a0)

class MyVideos(QMainWindow):
    byChoiceSignal = pyqtSignal(DialogResume)
    def __init__(self,videoChoice=None,possitionCut=None):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)),"main.ui"),self)

        self._dialog = None
        self._cropp = None
        self.posExecution = None
        self.croppVideoInTRansformation= None
        self.setAcceptDrops(True)

        self.actionOpen_File.triggered.connect(self.openFile)
        self.actionSave_Times.triggered.connect(self.saveTimes)
        self.actionOpen_Times.triggered.connect(self.openTimes)

        #create button for playing
        self.playBtn.setEnabled(False)
        self.playBtn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.playBtn.clicked.connect(self.play_video)

        #create button for description
        self.descrMedia.setEnabled(False)
        self.descrMedia.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView))

        #create slider
        self.slider.setRange(0,0)
        self.slider.sliderMoved.connect(self.set_position)

        #create my startPoint
        # self.startPoint = QLineEdit()
        self.startPoint.textEdited.connect(self.set_positionT)

        self.split.textEdited.connect(self.splitTimes)
        #self.startPoint.mouseDoubleClickEvent()

        #create my duration
        # self.duration = QLineEdit()
        self.duration.textEdited.connect(self.set_positionT)
        #self.duration.mouseDoubleClickEvent()

    

        #self.addTime = QPushButton()
        self.addTime.clicked.connect(self.addTimef)

        # self.actionLibera_os_times = QAction()
        self.actionLibera_os_times.triggered.connect(self.presentTimes)
        self.actionCropVideo.triggered.connect(self.actionCropVideoMet)
        QShortcut(QKeySequence(Qt.Modifier.SHIFT | Qt.Modifier.CTRL | Qt.Key.Key_S), self).activated.connect(self.actionCropVideoMet)
        self.descrMedia.clicked.connect(self.presentTimes)

        #create my oplayer
        self.mediaPlayer = QMediaPlayer()

        self.volume = 50
        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)

        QShortcut(QKeySequence(Qt.Key.Key_Up), self).activated.connect(lambda:self.acceleration(5))
        QShortcut(QKeySequence(Qt.Key.Key_Down), self).activated.connect(lambda:self.reducePos(5))

        QShortcut(QKeySequence(Qt.Modifier.SHIFT | Qt.Modifier.CTRL | Qt.Key.Key_7), self).activated.connect(lambda:self.reducePos(.01))
        QShortcut(QKeySequence(Qt.Modifier.SHIFT | Qt.Modifier.CTRL | Qt.Key.Key_8), self).activated.connect(lambda:self.acceleration(.01))
        QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_7), self).activated.connect(lambda:self.reducePos(.1))
        QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_8), self).activated.connect(lambda:self.acceleration(.1))
        QShortcut(QKeySequence(Qt.Key.Key_7), self).activated.connect(lambda:self.reducePos(.5))
        QShortcut(QKeySequence(Qt.Key.Key_8), self).activated.connect(lambda:self.acceleration(.5))
        QShortcut(QKeySequence(Qt.Key.Key_4), self).activated.connect(lambda:self.reducePos(5))
        QShortcut(QKeySequence(Qt.Key.Key_5), self).activated.connect(lambda:self.acceleration(5))
        QShortcut(QKeySequence(Qt.Key.Key_1), self).activated.connect(lambda:self.reducePos(10))
        QShortcut(QKeySequence(Qt.Key.Key_2), self).activated.connect(lambda:self.acceleration(10))
        QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_1), self).activated.connect(lambda:self.reducePos(30))
        QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_2), self).activated.connect(lambda:self.acceleration(30))
        QShortcut(QKeySequence(Qt.Modifier.SHIFT | Qt.Modifier.CTRL | Qt.Key.Key_1), self).activated.connect(lambda:self.reducePos(60))
        QShortcut(QKeySequence(Qt.Modifier.SHIFT | Qt.Modifier.CTRL | Qt.Key.Key_2), self).activated.connect(lambda:self.acceleration(60))

        QShortcut(QKeySequence(Qt.Key.Key_S), self).activated.connect(self.play_video)
        QShortcut(QKeySequence(Qt.Key.Key_Q), self).activated.connect(self.addTimef)

        QShortcut(QKeySequence(Qt.Key.Key_D), self).activated.connect(lambda:self.presentTimesForce('d'))
        QShortcut(QKeySequence(Qt.Key.Key_F), self).activated.connect(lambda:self.presentTimesForce('f'))
        QShortcut(QKeySequence(Qt.Key.Key_E), self).activated.connect(lambda:self.presentTimesForce('e'))

        QShortcut(QKeySequence(Qt.Key.Key_9), self).activated.connect(self.play_video)
        QShortcut(QKeySequence(Qt.Key.Key_6), self).activated.connect(self.addTimef)
        QShortcut(QKeySequence(Qt.Key.Key_3), self).activated.connect(lambda:self.presentTimesForce('d'))
        QShortcut(QKeySequence(Qt.Key.Key_F8),self).activated.connect(self.openVLC)
        

        # QShortcut(QKeySequence(Qt.Modifier.SHIFT | Qt.Modifier.CTRL | Qt.Key.Key_D), self).activated.connect(self.presentSuperTimes)
        QShortcut(QKeySequence(Qt.Modifier.SHIFT | Qt.Modifier.CTRL | Qt.Key.Key_D), self).activated.connect(lambda:self.presentSuperTimes('d'))
        QShortcut(QKeySequence(Qt.Modifier.SHIFT | Qt.Modifier.CTRL | Qt.Key.Key_F), self).activated.connect(lambda:self.presentSuperTimes('f'))
        QShortcut(QKeySequence(Qt.Modifier.SHIFT | Qt.Modifier.CTRL | Qt.Key.Key_E), self).activated.connect(lambda:self.presentSuperTimes('e'))
        QShortcut(QKeySequence(Qt.Modifier.SHIFT | Qt.Modifier.CTRL | Qt.Key.Key_A), self).activated.connect(self.actionRegognition)

        QShortcut(QKeySequence(Qt.Key.Key_Left), self).activated.connect(self.diminuirSom)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self).activated.connect(self.aumentarSom)
        QShortcut(QKeySequence(Qt.Key.Key_End), self).activated.connect(self.minimumSound)


        QShortcut(QKeySequence(Qt.Key.Key_Escape), self).activated.connect(self.close)


        self.videoWidget.wheelEvent = lambda event:self.getWheelEvent(event,lambda:self.acceleration(5),lambda:self.reducePos(5))
        self.videoWidget.mouseMoveEvent = lambda event:self.getMoveFilmEvent(event)
        self.slider     .wheelEvent = lambda event:self.getWheelEvent(event,lambda:self.acceleration(5),lambda:self.reducePos(5))

        self.setSound()
        self.sound.wheelEvent = lambda event:self.getWheelEvent(event,self.aumentarSom,self.diminuirSom)


        self.video = QVideoWidget()
        self.mediaPlayer.setVideoOutput(self.video)
        vbox = QVBoxLayout()
        vbox.addWidget(self.video)
        self.videoWidget.setLayout(vbox)
        self.video.show()
        self.byChoice=False

        try:
            opts, args = getopt.getopt(sys.argv[1:],"h:f:s:")
            file = [x for x in opts if x[0] == '-f']
            position = [x for x in opts if x[0] == '-s']

            if((file and os.path.exists(file[0][1])) or videoChoice):
                video= videoChoice if videoChoice else file[0][1]
                self.openFileVideo(video)
                self.byChoice=True if videoChoice else False
                self.mediaPlayerPause()
                if position :
                    position=position[0][1]
                    self.maxDuration=int(math.trunc(float([x for x in ffmpeg.probe(video)["streams"] if  'width' in x ][0]['duration'])))*1000
                    self.startPoint.setText(position)
                    self.set_positionT(position)
                    self.position_changed(int(position))
                    self.addTimef()
                    self.splitTimes("1")
                    self.play_video()
                    self.presentTimesForce('f')
        except getopt.GetoptError:
            print("moviesplit -f <file> -s <starttime> ({}) ".format(str(sys.argv)))

        if(possitionCut):
                    self.set_positionT(str(possitionCut))
                    self.position_changed(possitionCut)
                    self.mediaPlayer.pause()
                    # self.actionCropVideoMet()

        qtRectangle = self.frameGeometry()
        centerPoint = QGuiApplication.primaryScreen().availableGeometry().topRight()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    def openVLC(self):
        self.mediaPlayerPause();
        self.timer.stop()
        try:
            subprocess.Popen(
            ["/usr/bin/vlc",self.label.text()]);
        except :
            pass
    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for video in files:
            self.openFileVideo(video)


    def getMoveFilmEvent(self,event: QMouseEvent):
        x=event.x()
        delta=(x/self.videoWidget.size().width())
        if(delta < 0 or delta > 1):
            return
        newPossition = delta*self.maxDuration
        self.set_position(newPossition)

    def getWheelEvent(self, event,pluss,minus):
        steps = event.angleDelta().y() // 120
        vector = steps and steps // abs(steps) # 0, 1, or -1
        for step in range(1, abs(steps) + 1):
            if(vector>0):
                pluss()
            elif(vector<0):
                minus()
            
    def aumentarSom(self):
        self.volume = self.mediaPlayer.volume();
        self.volume+=10 if self.volume >= 10 else 1
        self.mediaPlayer.setVolume(self.volume)
        self.setSound()

    def diminuirSom(self):
        self.volume = self.mediaPlayer.volume();
        self.volume-=10 if self.volume >= 10 else 1
        self.mediaPlayer.setVolume(self.volume)
        self.setSound()

    def minimumSound(self):
        self.mediaPlayer.setVolume(10)
        self.setSound()

    def splitTimes(self,parts):
        splits = re.search("(\d+)",parts)

        try:
            
            if(splits):
                splits = splits.group(1)
            if(len(splits) != len(parts)):
                self.descrMedia.setFocus()
            if(splits):
                if(self.times.count() > 0):
                    for i in range(self.times.count(),-1,-1):
                        if(self.times.itemAt(i)):
                            self.removeTime(self.times.itemAt(i).widget())
                splits = int(splits)
                if(splits > 0):
                    start=0 if not self.startPoint.text() else int(self.startPoint.text())
                    maxval=self.maxDuration
                    step=math.trunc((maxval-start)/splits)

                    for init in range(start ,maxval-step+1,step):
                        time = TimeComponent(init,init+step if init+step+step <= maxval else maxval,self)
                        self.times.addWidget(time)
        except Exception as e:
            self.label.setText(str(e))

    def setSound(self):
        self.sound.setText(str(int(self.mediaPlayer.volume()))+"%")

    def saveTimes(self):
        UtilFilesTimes.saveTimes(self.times,self.croppVideoInTRansformation,self.label.text(),self.posExecution,
        definedSize=self.getValueText("size"),
        definedRate=self.getValueText("rateVideo")
        )

    def openTimes(self):
        UtilFilesTimes.openTimes(self.label.text()+'.json',
            lambda time:self.times.addWidget(time),
            lambda crop:self.setCrop(crop),
            lambda size:self.setValueText("size",size),
            lambda rate:self.setValueText("rateVideo",rate),
            self)

    def setCrop(self,crop):
        self.croppVideoInTRansformation=crop

    def mediaPlayerPause(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()

    def presentSuperTimes(self,option):
        self.posExecution=option
        self.mediaPlayerPause()
        self.addTimef()
        self.position_changed(self.maxDuration)
        self.addTimef()

        self.presentTimes();

    def presentTimesForce(self,type:str):
        self.posExecution=type
        self.presentTimes();

    def close(self) -> bool:
        
        self.mediaPlayerPause()
        if self.byChoice and self.times.count() == 0:
            self.byChoice=False
            self.byChoiceSignal.emit(None)
        return super().close()

    def presentTimes(self):
        if(self.times.count() == 0):
            return;
        self.saveTimes()
        self.mediaPlayerPause()
        if self._dialog is None:
            self._dialog = DialogResume(self.label.text(),self.times,posExecution=self.posExecution \
                , byChoice=self.byChoice ,crop=self.croppVideoInTRansformation
                ,definedSize=self.getValueText("size")
                ,definedRate=self.getValueText("rateVideo"))
        self._dialog.label=self.label.text();
        if self.byChoice:
            if(not self.posExecution):
                self._dialog.exec()
            self.byChoiceSignal.emit(self._dialog )
        else:
            self._dialog.closeVideoSignal.connect(self.close)
            self._dialog.exec()

    def getValueText(self,name):
            wid = self.findChild(QWidget, name)
            if(wid and "aliceblue" in wid.styleSheet() and wid.text()):
                return wid.text()
            else:
                return None

    def setValueText(self,name,value):
        countSize = self.description.count()
        for poss in range(0,countSize):
            wid = self.description.itemAt(poss).widget()
            tip = wid.toolTip()
            if(tip == name):
                try:
                    wid.setText(value)
                    wid.setStyleSheet('background-color:aliceblue')
                except Exception as e:
                    print(str(e))

    def reducePos(self,mult):        
        self.alterVideoTime(mult,-1)

    def acceleration(self,mult):
        self.alterVideoTime(mult,+1)

    def alterVideoTime(self,mult,dif):
        poss = self.get_position()
        # delta = ((mult*1000)/self.maxDuration)
        delta = mult * 1000 *dif
        if(poss+delta>=self.maxDuration):
            delta=0
        self.set_position(poss + delta)

    def removeTime(self,time):
        # self.times = QWidget()
        self.duration.setText('')
        self.startPoint.setText(str(time.startPointText))
        self.set_position(int(time.startPointText))
        self.position_changed(int(time.startPointText))
        self.times.removeWidget(time)
        sip.delete(time)
        self.times_2.repaint()


    def addTimef(self):
        #self.times = QWidget()
        if(len(self.duration.text()) == 0):
            self.duration.setText(self.startPoint.text())
        else:
            str=int(self.startPoint.text())
            end=int(self.duration.text())
            if(end>str):
                time = TimeComponent(str,end,self)
            else:
                time = TimeComponent(end,str,self)
            self.times.addWidget(time)
            self.startPoint.setText(self.duration.text())
            self.duration.setText('')

    def openFile(self):
        fileName = QFileDialog.getOpenFileName(self,
            "Open Video", "/home/maloi/Videos", "Video Files (*.mp4 *.avi *.m4v *.3gp *.wmv *.mkv *.mpv)");
        

        if fileName[0] != '':
            self.openFileVideo(fileName[0])

    def openFileVideo(self,video):
        #connect(player, SIGNAL(positionChanged(qint64)), this, SLOT(positionChanged(qint64)));
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(video)))
            self.mediaPlayer.setVolume(50);
            self.mediaPlayer.setPosition(0) # to start at the beginning of the video every time
            self.mediaPlayer.play();
            self.playBtn.setEnabled(True)
            self.descrMedia.setEnabled(True)
            self.label.setText(video)
            values = []
            try:       
                ffmpegOb = ffmpeg.probe(video)
                videoObj = [x for x in ffmpegOb["streams"] if  'width' in x ][0]


                if('codec_name' in videoObj):
                    values.append({'label':'codec','text':videoObj['codec_name'],
                
                            'style':''})
                avgrate=25
                if('avg_frame_rate' in videoObj):
                    frame = str(videoObj['avg_frame_rate']).split("/")
                    if(int(frame[1])>0):
                        avgrate=math.trunc(int(frame[0])/int(frame[1]))
                        values.append({'label':'avgrate','text':avgrate,
                    
                                'style':'background-color:{}'
                                .format('lightgreen' if avgrate > 25 else 'yellow' if avgrate > 20 
                                    else 'red')})
                else:
                    values.append({'label':'avgrate','text':avgrate,  'style':''})         
                
                if('duration' in videoObj):
                    durationSize=int(math.trunc(float(videoObj['duration'])))
                    durationTime = datetime.datetime.fromtimestamp(
                                    durationSize
                                    , tz=pytz.utc
                                ).strftime('%H:%M:%S')
                    values.append({'label':'durationTime','text':durationTime,
                    
                                'style':'background-color:{}'
                                .format('lightgreen' if durationSize < 60*1000 else 'yellow' if durationSize < 600 * 1000
                                    else 'red')})

                
                if('width' in videoObj):
                    values.append({'label':'size','text':str(videoObj['width'])+"x"+str(videoObj['height']),
                    
                                'style':'background-color:{}'
                                .format( 'red' if videoObj['width'] > 1000 else 'yellow' if videoObj['width'] > Util.maxRateVideo 
                                    else 'lightgreen')})
                else:
                    values.append({'label':'size','text':'639x359',  'style':''})      

                
                if('bit_rate' in videoObj):
                    rateVideo=math.trunc(int(videoObj['bit_rate'])/1000)
                    values.append({'label':'rateVideo','text':rateVideo,
                    
                                'style':'background-color:{}'
                                .format('red' if rateVideo > 1000 else 'yellow' if rateVideo > Util.maxRateVideo 
                                    else 'lightgreen')})
                else:
                    values.append({'label':'rateVideo','text':Util.maxRateVideo,  'style':''})                              

                fileSize=os.path.getsize(video)
                values.append({'label':'fileSize','text':Util.formatSize(fileSize),

                                'style':'background-color:{}'
                                .format('lightgreen' if fileSize < 50 * 1024 * 1024 else 'yellow' if fileSize < 130 * 1024 * 1024 
                                    else 'red')
                                    
                                    })
                

                # self.description.setText(" | ".join([str(x) for x in values]))
                for poss in range(self.description.count()):
                        txtLabel=self.description.itemAt(poss).widget()
                        txtLabel.setStyleSheet("")
                        txtLabel.setText("")

                for poss,labelVal in enumerate(values):
                    labelT = str(labelVal["label"])
                    if(self.description.itemAt(poss)):
                        txtLabel=self.description.itemAt(poss).widget()
                    else:
                        if labelT == 'avgrate' or  labelT == 'size' or  labelT == 'rateVideo' :
                            txtLabel=MaloiLineEdit(self)
                            # txtLabel.editingFinished.connect(lambda:self.paintBlueTextEdited())
                        else :
                            txtLabel=QLabel(self) 
                        txtLabel.setToolTip(labelT)
                    if("style" in labelVal):
                        txtLabel.setStyleSheet(labelVal["style"])

                    txtLabel.setText(str(labelVal["text"]))
                    txtLabel.setMaximumHeight(30)
                    txtLabel.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum)

                    if(not self.description.itemAt(poss)):
                        self.description.addWidget(txtLabel)                
            except Exception as e:
                if(self.description.itemAt(0)):
                    txtLabel=self.description.itemAt(0).widget()
                else:
                    txtLabel=QLabel(self)
                    txtLabel.setText("Valor ruim "+str(e))
                self.description.addWidget(txtLabel) 
            
            #self.times_2.removeWidget(self.times)
            sip.delete(self.times)
            self.times=QGridLayout();
            self.times_2.setLayout(self.times)

            self._dialog = None
            self.openTimes()

    def mediastate_changed(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)

            )

        else:
            self.playBtn.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)

            )
    def position_changed(self, position=None):
        if(not position ):
            position=self.get_position() 
        self.slider.setValue(position)
        self.durationtime.setText(Util.convertMillis(position))
        if(len(self.duration.text()) == 0):
            self.startPoint.setText(str(position))
            self.cuttime.setText('')
        else:
            self.duration.setText(str(position))
            startEnd=int(self.startPoint.text())
            if(startEnd>position):
                startEnd=position
                position=int(self.startPoint.text())
            self.cuttime.setText(Util.convertMillis(position-startEnd))



    def duration_changed(self, duration):
        self.slider.setRange(0, duration)
        self.maxDuration=duration


    def set_position(self, position):
        self.mediaPlayer.setPosition(int(position))

    def get_position(self)->int:
        # return self.mediaPlayer.get_position() * 1000
        return self.mediaPlayer.position()

    def set_positionT(self,position):
        search = re.search("(\d+)",position)
        if(not search):
            return
        position = search.group(1)
        if(position and int(position) > 1000):
            self.set_position(int(position,base=10))

    def handle_errors(self):
        self.playBtn.setEnabled(False)
        self.descrMedia.setEnabled(False)
        self.label.setText("Error: " + self.mediaPlayer.errorString())

    def play_video(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()





if __name__ == "__main__":
    app = QApplication([])
    app.setWindowIcon(QIcon('/usr/share/icons/Yaru/256x256/apps/jockey.png'))
    window = MyVideos()
    window.show()
    sys.exit(app.exec())
