
import ffmpeg
import math
import sys
import os


if __name__ == "__main__":
    dimention="640X360"
    try:
        ffmpegOb = ffmpeg.probe(sys.argv[1],cmd='/home/maloi/bin/ffprobe')#["streams"]
        videoObj = [x for x in ffmpegOb["streams"] if  'width' in x ][0]
        width = videoObj['width']
        height = videoObj['height']

        if(width > 640 or height > 640):
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
        dimention=(str(width)+"X"+str(height))

    except Exception:
        dimention=("640X360")


    
    print(dimention)