import ffmpeg
import math
import sys
import os

from util import Util


if __name__ == "__main__":
        rate=Util.maxRateVideo
        try:
            ffmpegOb = ffmpeg.probe(sys.argv[1],cmd='/home/maloi/bin/ffprobe')#["streams"]
            videoObj = [x for x in ffmpegOb["streams"] if  'width' in x ][0]
            rate=math.trunc(int(videoObj['bit_rate'])/1000)
            if(rate>Util.maxRateVideo):
                rate=Util.maxRateVideo
        except Exception:
            rate=Util.maxRateVideo

        print(str(rate))