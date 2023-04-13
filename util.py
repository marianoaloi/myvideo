




class Util:

    def convertMillis(millis:int):
        seconds=(millis/1000)%60
        minutes=(millis/(1000*60))%60
        hours=(millis/(1000*60*60))%24
        return '{0:02d}:{1:02d}:{2:02d}'.format(int(hours),int(minutes), int(seconds))

    def formatSize(b:int)->str:
        if b< 1024:
            return '{:.2f}B'.format(b)
        if b< 1024*1024:
            return '{:.2f}K'.format(b/1024)
        if b< 1024*1024*1024:
            return '{:.2f}M'.format(b/1024/1024)
        if b< 1024*1024*1024*1024:
            return '{:.2f}G'.format(b/1024/1024/1024)

        return '{}B'.format(b)  
    
    maxRateVideo=500
    