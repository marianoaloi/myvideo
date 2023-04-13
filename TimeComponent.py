import os
from PyQt5.QtWidgets import QWidget

from PyQt5 import uic

from util import Util

class TimeComponent(QWidget):
    
    def __init__(self):
        super().__init__()

    def initial(self):
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__)),"TimeComponent.ui"),self)

        # self.maximumHeight =  \
        # self.height = 60


        self.remove.clicked.connect(self.removeA)

    def __init__(self,startPoint:int,duration:int,parent):
        super().__init__()
        if(parent):
            self.parent = parent
            self.initial()

            self.begindureation.setText(Util.convertMillis(startPoint))
            self.endduration.setText(Util.convertMillis(duration))
            self.time.setText(Util.convertMillis(duration-startPoint))

        self.startPointText=startPoint
        self.duration=duration

    def removeA(self):
        self.parent.removeTime(self)