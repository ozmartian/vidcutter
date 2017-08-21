#!/usr/bin/env python2

import os
import subprocess
from subprocess import Popen
from datetime import timedelta
import re
import fcntl
from time import sleep
import logging


class Logger():
    HomeDir = os.path.dirname(__file__)
    UserPath=os.path.expanduser("~")
    DataDir=os.path.join(HomeDir,"data")
    
    LogPath= None
    

    def __init__(self):
        self.__setupDirectories()
       
        
    def __setupDirectories(self):
        OSTools().ensureDirectory(self.DataDir,None)
        self.setupLogging()
        
    def setupLogging(self): 
        path = os.path.join(self.DataDir,"VC.log")
        logging.basicConfig(filename=path,level=logging.DEBUG,format='%(asctime)s %(message)s')  
        self.LogPath = path         

    def logInfo(self,aString):
        logging.log(logging.INFO,aString)

    def logError(self,aString):
        logging.log(logging.ERROR,aString)
    
    def logClose(self):
        logging.shutdown() 

    def logException(self,text):
         logging.exception(text)
  


#TODO join them with the OSTools class and create an import in ant
class OSTools():
    
    def getPathWithoutExtension(self,aPath):
        if aPath:
            #rawPath = os.path.splitext(str(aPath))[0]
            rawPath = os.path.splitext(aPath)[0]
        else:
            rawPath=""
        return rawPath

    def getWorkingDirectory(self):
        abspath = os.path.abspath(__file__)
        dname = os.path.dirname(abspath)
        return dname               

    def getHomeDirectory(self):
        return os.path.expanduser("~")

    def setCurrentWorkingDirectory(self):
        os.chdir(self.getWorkingDirectory())
        
    def getFileNameOnly(self,path):
        return os.path.basename(path)
    
    def fileExists(self,path):
        return os.path.isfile(path)
    
    def removeFile(self,path):
        if self.fileExists(path):
            os.remove(path)

    def ensureDirectory(self,path,tail):
        #make sure the target dir is present
        if tail is not None:
            path = os.path.join(path,tail)
        if not os.access(path, os.F_OK):
            try:
                os.makedirs(path)
                os.chmod(path,0o777) 
            except OSError as osError:
                logging.log(logging.ERROR,"target not created:"+path)
                logging.log(logging.ERROR,"Error: "+ str(osError.strerror))
    
    def ensureFile(self,path,tail):
        fn = os.path.join(path,tail)
        ensureDirectory(path, None)
        with open(fn, 'a'):
            os.utime(fn, None)
        return fn




BIN = "ffmpeg"
Log = Logger()

def timedeltaToFFMPEGString(deltaTime):
    ms=deltaTime.microseconds/1000
    s = deltaTime.seconds
    hours, remainder = divmod(s, 3600)
    minutes, seconds = divmod(remainder, 60)
    so = str(seconds).rjust(2,'0')
    mo=str(minutes).rjust(2,'0')
    ho=str(hours).rjust(2,'0')
    mso=str(ms).rjust(3,'0')
    return '%s:%s:%s.%s' % (ho, mo, so, mso)

def log(*messages):
    #Hook for logger...
    #cnt = len(messages)
    #print "{0} {1}".format(*messages)
    Log.logInfo("{0} {1}".format(*messages))


class FFStreamProbe():
    def __init__(self,video_file):
        self._setupConversionTable()
        self.path=video_file
        self._readData()
        
    def _readData(self):
        result = Popen(["ffprobe","-show_format","-show_streams",self.path,"-v","quiet"],stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
        if len(result[0])==0:
            raise IOError('No such media file '+self.path)
        self.streams=[]
        datalines=[]
        self.video=[]
        self.audio=[]
        self.formatInfo = None
    

        lines = result[0].split('\n')
        for a in lines:
            if re.match('\[STREAM\]',a):
                datalines=[]
            elif re.match('\[\/STREAM\]',a):
                self.streams.append(VideoStreamInfo(datalines))
                datalines=[]

            elif re.match('\[FORMAT\]',a):
                datalines=[]
            elif re.match('\[\/FORMAT\]',a):
                self.formatInfo = VideoFormatInfo(datalines)
                datalines=[]
            else:
                datalines.append(a)
        for a in self.streams:
            if a.isAudio():
                self.audio.append(a)
            if a.isVideo():
                self.video.append(a)
    
    def _setupConversionTable(self):
        self._convTable={}
        self._convTable["mpeg2video"]="mpg"
        self._convTable["mpeg1video"]="mpg"
        self._convTable["h264"]="mp4"
        self._convTable["msmpeg4v1"]="avi"
        self._convTable["msmpeg4v2"]="avi"
        self._convTable["msmpeg4v3"]="avi"
        self._convTable["rawvideo"]="swf"
        self._convTable["vp6f"]="flv"
        self._convTable["matroska"]="mkv"
        self._convTable["webm"]="mkv"
        self._convTable["mpeg4"]="mp4" #or mov,m4a,3gp,3g2,mj2
        
        

        #self._convTable["ansi"]="txt"
        #--more to come
        '''
        Container  Audio formats supported
        MKV/MKA    Vorbis, MP2, MP3, LC-AAC, HE-AAC, WMAv1, WMAv2, AC3, eAC3, Opus
        MP4/M4A    MP2, MP3, LC-AAC, HE-AAC, AC3
        FLV/F4V    MP3, LC-AAC, HE-AAC
        3GP/3G2    LC-AAC, HE-AAC
        MPG        MP2, MP3
        PS/TS Stream    MP2, MP3, LC-AAC, HE-AAC, AC3
        M2TS       AC3, eAC3
        VOB        MP2, AC3
        RMVB       Vorbis, HE-AAC
        WebM       Vorbis, Opus
        OGG        Vorbis, Opus 
        '''

                
    def getVideoStream(self):
        if len(self.video)==0:
            return None
        return self.video[0]
    
    def getAudioStream(self):
        for stream in self.audio:
            if stream.getBitRate()>0:
                return stream     
        return None
    
    def getTargetExtension(self):
        codec = self.getVideoStream().getCodec()
        if codec in self._convTable:
            return self._convTable[codec]
        return ""
    
    def getAspectRatio(self):
        ratio = self.getVideoStream().getAspectRatio()
        if ratio == 1.0:
            ratio = float(self.getVideoStream().getWidth())/float(self.getVideoStream().getHeight())
        return ratio
    '''
    This filter is required for copying an AAC stream from 
    a raw ADTS AAC or an MPEG-TS container to MP4A-LATM.
    '''
    
    def needsAudioADTSFilter(self):
        if self.getAudioStream() is None:
            return False
        return self.getAudioStream().getCodec() =="aac" and (self.isH264() or self.isMP4())
    
    '''
    check if needs the h264_mp4toannexb filter-
    Used on mp4 or h264, for converting INTO transport streams
    '''
    def needsH264Filter(self):
        if self.isTransportStream():
            return False;
        return self.isMP4() or self.isH264()
    
    #VideoFormat is format info....
    def getFormatNames(self):
        return self.formatInfo.formatNames()
    
    def hasFormat(self,formatName):
        return formatName in self.getFormatNames() 
    
    def isKnownVideoFormat(self):
        codec = self.getVideoStream().getCodec()
        return codec in self._convTable
    
    def isTransportStream(self):
        return self.hasFormat("mpegts")
    
    '''
    is MP4? Since its a formatcheck it can't be mp4-TS
    '''
    def isMP4(self): 
        return self.hasFormat("mp4")
    
    def isMPEG2(self):
        return "mpeg" in self.getVideoStream().getCodec()
        
    def isH264(self):
        return "h264" == self.getVideoStream().getCodec()
    
    def printCodecInfo(self):
        print "-------- Video -------------"
        s = self.getVideoStream()
        print "Index:",s.getStreamIndex()
        print "codec",s.getCodec()
        print "getCodecTimeBase: ",s.getCodecTimeBase()
        print "getTimeBase: ",s.getTimeBase()
        print "getAspect ",s.getAspectRatio()
        print "getFrameRate: ",s.getFrameRate()
        print "getCMFRameRate: ",s.frameRate() #Common denominator
        print "getDuration: ",s.duration()
        print "getWidth: ",s.getWidth()
        print "getHeight: ",s.getHeight()
        print "isAudio: ",s.isAudio()
        print "isVideo: ",s.isVideo()
        
        print "-------- Audio -------------"
        s = self.getAudioStream()  
        if not s:
            print "No audio"
            exit(0)  
        print "Index:",s.getStreamIndex()
        print "getCodec:",s.getCodec()
        print "bitrate(kb)",s.getBitRate()
        print "getCodecTimeBase: ",s.getCodecTimeBase()
        print "getTimeBase: ",s.getTimeBase()
        print "getDuration: ",s.duration()
        print "isAudio: ",s.isAudio()
        print "isVideo: ",s.isVideo()
        print "-----------EOF---------------"
        


    '''
[FORMAT]
filename=../Path/test.mp4
nb_streams=2
nb_programs=0
format_name=mov,mp4,m4a,3gp,3g2,mj2
format_long_name=QuickTime / MOV
start_time=0.000000
duration=62.484000
size=136068832
bit_rate=17421270
probe_score=100
TAG:major_brand=mp42
TAG:minor_version=0
TAG:compatible_brands=isommp42
TAG:creation_time=2016-08-29 09:55:41
TAG:com.android.version=6.0.1
[/FORMAT]

    '''
class VideoFormatInfo():
    NA="N/A"
    TAG="TAG:"
    def __init__(self,dataArray):
        self.dataDict={}
        self.tagDict={}
        self._parse(dataArray)

    def _parse(self,dataArray):
        for entry in dataArray:
            try:
                (key,val)=entry.strip().split('=')
            except:
                log("Error in entry:",entry)
            if self.NA!=val:
                if self.TAG in key:
                    key=key.split(':')[1]
                    self.tagDict[key]=val
                else:
                    self.dataDict[key]=val

    def _print(self):
        print "***format data***"
        for key,value in self.dataDict.items():
            print key,"->",value
        
        print "***tag data***"
        for key,value in self.tagDict.items():
            print key,"->",value
    
    
    def getDuration(self):
        if "duration" in self.dataDict:
            return float(self.dataDict['duration'])
        return 0.0
    
    def getBitRate(self):
        if "bit_rate" in self.dataDict:
            kbit= int(self.dataDict["bit_rate"])/float(1024)
            return round(kbit)
        return 0
    
    def formatNames(self):
        if "format_name" in self.dataDict:
            values = self.dataDict['format_name']
            return values.split(',')
        return [self.NA]
            
    def getSizeKB(self):
        if "size" in self.dataDict:
            kbyte= int(self.dataDict["size"])/float(1024)
            return round(kbyte)
        return 0.0
         

class VideoStreamInfo():
    #int values
    NA="N/A"
#     keys = ["index","width", "height","avg_frame_rate","duration","sample_rate"]
#     stringKeys =["codec_type","codec_name"]
#     divKeys =["display_aspect_ratio"]        
    
    def __init__(self,dataArray):
        self.dataDict={}
        self._parse(dataArray)
    
    def _parse(self,dataArray):
        for entry in dataArray:
            try:
                (key,val)=entry.strip().split('=')
            except:
                log("Error in entry:",entry)
            if self.NA!=val:
                self.dataDict[key]=val
        
    def getStreamIndex(self):
        if 'index' in self.dataDict:
            return int(self.dataDict['index'])
    
    def getAspectRatio(self):
        if 'display_aspect_ratio' in self.dataDict:
            z,n= self.dataDict['display_aspect_ratio'].split(':')
            if z!='0' and n!='0':
                div = round(float(z+".0")/float(n+".0")*100.0)
                return div/100.0
        return 1.0



    def getFrameRate(self):
        if 'avg_frame_rate' in self.dataDict:
            z,n= self.dataDict['avg_frame_rate'].split('/')
            if int(n) !=0:
                return float(z)/int(n)
        return 1.0

    '''
    Smallest framerate in float
    r_frame_rate is NOT the average frame rate, it is the smallest frame rate that can accurately represent all timestamps. 
    So no, it is not wrong if it is larger than the average! For example, if you have mixed 25 and 30 fps content, 
    then r_frame_rate will be 150 (it is the least common multiple).
    '''
    def frameRate(self):
        if "r_frame_rate" in self.dataDict:
            (n,z)=self.dataDict["r_frame_rate"].split("/")
            if int(z)!=0:
                return float(n)/float(z) 
        return 1.0

    def getCodec(self):
        if 'codec_name' in self.dataDict:
            return self.dataDict['codec_name']
        return self.NA
    
    def hasAACCodec(self):
        return self.getCodec()=="aac"
    
    def getWidth(self):
        if 'width' in self.dataDict:
            return self.dataDict['width']
        return self.NA
    def getHeight(self):
        if 'height' in self.dataDict:
            return self.dataDict['height']
        return self.NA       
    
    def isAVC(self):#MOV, h264
        if 'is_avc' in self.dataDict:
            return "true" == self.dataDict['is_avc']
        return False
    
    def getCodecTimeBase(self):
        if 'codec_time_base' in self.dataDict:
            return self.dataDict['codec_time_base']
        return self.NA

    def getTimeBase(self):
        if 'time_base' in self.dataDict:
            return self.dataDict['time_base']
        return self.NA
      
 
    '''
    bitrate in kb (int)-Audio only
    '''
    def getBitRate(self):
        if "bit_rate" in self.dataDict:
            kbit= int(self.dataDict["bit_rate"])/float(1024)
            return round(kbit)
        return 0

    '''
    length in seconds (float)
    '''            
    def duration(self):
        if "duration" in self.dataDict:
            return float(self.dataDict["duration"])
        return 0.0 
   

    
    def isAudio(self):
        #Is this stream labeled as an audio stream?
        if 'codec_type' in self.dataDict:
            if str(self.dataDict['codec_type']) == 'audio':
                return True
        return False

    def isVideo(self):
        """
        Is the stream labeled as a video stream.
        """
        if 'codec_type' in self.dataDict:
            if str(self.dataDict['codec_type']) == 'video':
                return True
        return False


class FFFrameProbe():
    def __init__(self,video_file):
        self.frames = []
        self.path=video_file
        #self._readDataByLines()
        self._readData()
        
    
    def _readDataByLines(self):
        p = subprocess.Popen(["ffprobe","-select_streams","v:0","-show_frames",self.path,"-v","quiet"], stdout=subprocess.PIPE)
        proc =0;
        while True:
            line = p.stdout.readline()
            if not line:
                break
            if re.match('\[\/FRAME\]',line):
                proc+=1
                log("p ",proc)
                
#             dataBucket = self.__processLine(line,dataBucket)
#             if len(dataBucket)==0:
#                 proc+=1
#                 print "p ",proc
            
    def __processLine(self,aString,dataBucket):
        if re.match('\[FRAME\]',aString):
            dataBucket=[]
        elif re.match('\[\/FRAME\]',aString):
            self.frames.append(VideoFrameInfo(dataBucket))
            dataBucket=[]
        else:
            dataBucket.append(aString)
        return dataBucket

   
    def _readData(self):
        result = Popen(["ffprobe","-select_streams","v:0","-show_frames",self.path,"-v","quiet"],stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
        if len(result[0])==0:
            raise IOError('No such media file '+self.path)
        self.frames=[]
        datalines=[]
        
        lines = result[0].split('\n')
        for a in lines:
            if re.match('\[FRAME\]',a):
                datalines=[]
            elif re.match('\[\/FRAME\]',a):
                self.frames.append(VideoFrameInfo(datalines))
                datalines=[]
            else:
                datalines.append(a)

#TODO: sublcass the init. Only accessor methods
class VideoFrameInfo():
    '''
    [FRAME]
    media_type=video
    +key_frame=0
    pkt_pts=143730
    +pkt_pts_time=1.597000
    pkt_dts=143730
    pkt_dts_time=1.597000
    best_effort_timestamp=143730
    best_effort_timestamp_time=1.597000
    pkt_duration=1800

    pkt_duration_time=0.020000
    pkt_pos=1787538
    pkt_size=12425
    width=1280
    height=720
    pix_fmt=yuv420p
    sample_aspect_ratio=1:1
    +pict_type=B
    +coded_picture_number=62
    display_picture_number=0
    interlaced_frame=0
    top_field_first=0
    repeat_pict=0
    [/FRAME]
    '''
    
    NA="N/A"
    validKeys = ["key_frame","pkt_pts_time","pict_type","coded_picture_number"]
    def __init__(self,dataArray):
        self.dataDict={}
        self._parse(dataArray)
    
    def _parse(self,dataArray):
        for entry in dataArray:
            result = entry.strip().split('=')
            if len(result)==2:
                key = result[0]
                val = result[1]
                if self.NA!=val and key in self.validKeys:
                    self.dataDict[key]=val
    
    '''
    Usually an I-Frame
    '''
    def isKeyFrame(self):
        if self.dataDict["key_frame"]:
            return self.dataDict["key_frame"] =="1"
        return False
    
    '''
    Frame time in millisconds (float)
    '''
    def frameTime(self):
        if self.dataDict["pkt_pts_time"]:
            return float(self.dataDict["pkt_pts_time"])*1000.0
        return 0.0
    
    '''
    either P, B or I
    '''
    def frameType(self):
        if self.dataDict["pict_type"]:
            return self.dataDict["pict_type"]
        return self.NA
    
    '''
    Index of frame (int)
    '''
    def frameIndex(self):
        if self.dataDict["coded_picture_number"]:
            return int(self.dataDict["coded_picture_number"])
        
class CuttingConfig():
    def __init__(self,srcfilePath,targetPath):
        ''' Sets an object that understands say(aText)'''
        self.messenger = None
        self.reencode = False
        self.streamData = None
        self.srcfilePath=srcfilePath
        self.targetPath=targetPath
        
    

class FFMPEGCutter():
    MODE_JOIN =1;
    MODE_CUT = 2;
    def __init__(self,cutConfig):
        self._config = cutConfig
        self._tempDir ='/tmp'
        self._tmpCutList=self._getTempPath()+"cut.txt"
        self._fragmentCount=1;   
  
    
    '''
    cuts a part of the film, saves it an returns the temp filename for later concatination
    index = if more than one part of the film is cut
    * Basically that does not work - or makes the audio go async.*
    '''
#     def cutPart(self,startTimedelta,endTimedelta,index=0,nbrOfFragments=1):
#         self._fragmentCount = nbrOfFragments
#         scanTime = timedelta(seconds=20)
#         prefetchTime = (startTimedelta - scanTime)
#         if prefetchTime < scanTime:
#             prefetchTime = timedelta(0)
#             scanTime = startTimedelta
# 
#         prefetchString = timedeltaToFFMPEGString(prefetchTime)
#         seekString = timedeltaToFFMPEGString(scanTime)
#         
#         deltaMillis = (endTimedelta - startTimedelta).microseconds
#         deltaSeconds = (endTimedelta - startTimedelta).seconds 
#         durString=timedeltaToFFMPEGString(timedelta(seconds=deltaSeconds,microseconds=deltaMillis))
# 
#         #fast search - then slow search
#         log(prefetchString,"+",seekString,">>",durString)
#         if nbrOfFragments is 1:
#             fragment = self.targetPath()
#         else:
#             fragment = self._getTempPath()+str(index)+".m2t"
#         log("generate file:",fragment)
#         self.say("Cutting part:"+str(index))
#         
#         cmdExt = self._videoMode(self.MODE_CUT)
#         audioMode = self._audioMode(self.MODE_CUT)
#         
#         #the prefetch time finds a keyframe closest. The seek time is the cut. TODO-encode that as Iframes only
#         
#         cmd =[BIN,"-hide_banner","-y","-ss",prefetchString,"-i",self.filePath(),"-ss",seekString,"-t",durString]
#         cmdExt.extend(audioMode)
#         cmdExt.extend(["-avoid_negative_ts","1",fragment])
#         cmd.extend(cmdExt)
#         log("cut:",cmd)
#         #reencode:         pFFmpeg = subprocess.Popen([BIN,"-hide_banner","-y","-ss",prefetchString,"-i",self.filePath,"-ss",seekString,"-t",durString,"-vcodec",encodeMode,"-acodec","copy",fragment], stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
#         pFFmpeg = subprocess.Popen(cmd , stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
#          
#         while pFFmpeg.poll() is None:
#             #?sleep(0.2)   
#             if not self.non_block_read("Cut part "+str(index)+":",pFFmpeg.stdout):
#                 self.say("Cutting part %s failed"%(str(index)))
#                 return False
#         
#         self.say("Cutting done")
#         return True

    '''
    current limitation:
    Basically, if you specify "second 157" and there is no key frame until 
    second 159, it will include two seconds of audio (with no video) at the start, 
    then will start from the first key frame. 
    So be careful when splitting and doing codec copy
    '''

    def cutPart(self,startTimedelta,endTimedelta,index=0,nbrOfFragments=1):
        self._fragmentCount = nbrOfFragments
        
        prefetchTime = startTimedelta #comp

        prefetchString = timedeltaToFFMPEGString(prefetchTime)
        
        deltaMillis = (endTimedelta - startTimedelta).microseconds
        deltaSeconds = (endTimedelta - startTimedelta).seconds 
        durString=timedeltaToFFMPEGString(timedelta(seconds=deltaSeconds,microseconds=deltaMillis))

        #fast search - which is key search
        log('Prefetch seek/dur: ',prefetchString,">>",durString)
        if nbrOfFragments is 1:
            fragment = self.targetPath()
        else:
            fragment = self._getTempPath()+str(index)+".m2t"
        log("generate file:",fragment)
        self.say("Cutting part:"+str(index))
        
        cmdExt = self._videoMode(self.MODE_CUT)
        audioMode = self._audioMode(self.MODE_CUT)
        
        #the prefetch time finds a keyframe closest. post seek does not improve the result 
        
        cmd =[BIN,"-hide_banner","-y","-ss",prefetchString,"-i",self.filePath(),"-t",durString]
        cmdExt.extend(audioMode)
        cmdExt.extend(["-avoid_negative_ts","1","-shortest",fragment])
        cmd.extend(cmdExt)
        log("cut:",cmd)
        pFFmpeg = subprocess.Popen(cmd , stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
         
        while pFFmpeg.poll() is None:
            #?sleep(0.2)   
            if not self.non_block_read("Cut part "+str(index)+":",pFFmpeg.stdout):
                self.say("Cutting part %s failed"%(str(index)))
                return False
        
        self.say("Cutting done")
        return True

    
    '''
    Rules:
    aac_adtstoasc only in an mp4/mov container
    ac3 to aac should optional and only if mp4 container
    reencode must change the container(.extension) to mp4
    test: AC-3 problems
    Test mp2: good
    Base problem: AC-3 should be replaced by either mp2 or aac in mp4 container (AVC Video)
    '''
    def _audioMode(self,mode):
        #streamData is FFStreamProbe
        if self._config.streamData.getAudioStream() is None:
            return []
        log("audio:",self._config.streamData.getAudioStream().getCodec())
        if self._config.streamData.needsAudioADTSFilter():            
            return ["-c:a","copy","-bsf:a","aac_adtstoasc"]

        if self._config.streamData.isMPEG2() and (self._fragmentCount ==1 or mode==self.MODE_JOIN):
            return ["-c:a","copy","-f","dvd"]

        #This must be configurable - at least for tests. mp2 seems to work for kodi+mp4
#        if self._config.streamData.getVideoStream().getCodec()=="h264" and self._config.streamData.getAudioStream().getCodec()=="ac3":
#            return ["-c:a","mp2"] #test for kodi or aac?       
#             elif (codec == "ac3"): #TDO and avc /mp4 video codec.
#                 return ["-c:a","aac"]

        return ["-c:a","copy"]
    
    
    def _videoMode(self,mode=None):
        videoStream = self._config.streamData.getVideoStream() 
        
        log("video:",videoStream.getCodec())
        if self._config.reencode:
            return ["-c:v","libx264","-preset","faster"]  #-preset slow -crf 22
        
        if self._config.streamData.needsH264Filter():
            if self._fragmentCount==1:#CUT ONLY -NOT JOIN!
                return ["-c:v","copy","-bsf:v","h264_mp4toannexb"] 
            else:
                return ["-c:v","copy","-bsf:v","h264_mp4toannexb","-f","mpegts"]
                
        return ["-c:v","copy"]

    
    def _getTempPath(self):
        return self._tempDir+'/vc_'
    
    
    def filePath(self):
        return self._config.srcfilePath
    
    def targetPath(self):
        return self._config.targetPath
    
    def join(self):
        
        #add all files into a catlist: file '/tmp/vc_tmp0.m2t' ..etc
        #ffmpeg -f concat -i catlist.txt  -c copy concat.mp4
        #reencoding takes place in the cut - NOT here.
        if self._fragmentCount is 1:
            return

        self.say("Joining files...")
        
        with open(self._tmpCutList, 'w') as cutList:
            for index in range(0,self._fragmentCount):
                tmp = self._getTempPath()+str(index)+".m2t"
                cutList.write("file '"+tmp+"'\n")


        base = [BIN,"-hide_banner","-y","-f","concat","-safe","0","-i",self._tmpCutList,"-c:v","copy"]
        cmd=base+self._audioMode(self.MODE_JOIN)+[self.targetPath()]
        log("join:",cmd)
        pFFmpeg = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
       
        while pFFmpeg.poll() is None:
            sleep(0.2)
            if not self.non_block_read("Join:",pFFmpeg.stdout):
                return False
              
        self.say("Films joined")
        self._cleanup()
        return True

    def say(self,text):
        if self._config.messenger is not None:
            self._config.messenger.say(text) 
            
    #reading non blocking
    def non_block_read(self,prefix,output):
        fd = output.fileno()
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        text = "."
        try:
            text = output.read()
            m = re.search('frame=[ ]*[0-9]+',text)
            p1 = m.group(0)
            m = re.search('time=[ ]*[0-9:.]+',text)
            p2 = m.group(0)
            self.say(prefix+" "+p1+" - "+p2)
            log(prefix,'frame %s time %s'%(p1,p2))
        except:
            if len(text)>5:
                print "<"+text   
        if "failed" in text:
            #TODO needs to be logged
            print "?????"+text
            self.say(prefix+" !Conversion failed!")
            return False
        else:
            return True 
    

    def ensureAvailableSpace(self):
        if not self._hasEnoughAvailableSpace(self._tempDir):
            path=os.path.expanduser("~")
            self.ensureDirectory(path,".vc_temp")

    def _hasEnoughAvailableSpace(self,tmpDir):
        result = Popen(["df","--output=avail",tmpDir],stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
        if len(result[1])>0:
            print "Error using df:"+result[1]
            return False
        
        rows = result[0].split('\n')
        if len(rows) > 1:
            #Filesystem      Size  Used Avail Use% Mounted on
            avail = int(rows[1])*1024

        needed = os.path.getsize(self.filePath())
        print "file size:",needed, " avail:",avail, "has enough:",needed <= avail
        return needed <= avail

    
    def _cleanup(self):
        for index in range(self._fragmentCount):
            fragment = self._getTempPath()+str(index)+".m2t"
            os.remove(fragment)   

    def ensureDirectory(self,path,tail):
        #make sure the target dir is present
        if tail is not None:
            path = os.path.join(path,tail)
        if not os.access(path, os.F_OK):
            try:
                os.makedirs(path)
                os.chmod(path,0o777)
            except OSError:
                print "Error creating directory"
                return
        self._tempDir=path    
