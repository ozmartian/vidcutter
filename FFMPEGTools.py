'''
Created on Oct 4, 2014
FFMPG Wrapper - AVCONV will follow
@author: matze
'''

import os
import subprocess
from subprocess import Popen
from datetime import timedelta
import re
import fcntl
from time import sleep
import shutil

BIN = "ffmpeg"


def timedeltaToFFMPEGString(deltaTime):
    ms = deltaTime.microseconds / 1000
    s = deltaTime.seconds
    hours, remainder = divmod(s, 3600)
    minutes, seconds = divmod(remainder, 60)
    so = str(seconds).rjust(2, '0')
    mo = str(minutes).rjust(2, '0')
    ho = str(hours).rjust(2, '0')
    mso = str(ms).rjust(3, '0')
    return '%s:%s:%s.%s' % (ho, mo, so, mso)


class FFStreamProbe():
    def __init__(self, video_file):
        self._setupConversionTable()
        self.path = video_file
        self._readData()

    def _readData(self):
        result = Popen(["ffprobe", "-show_streams", self.path, "-v", "quiet"], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE).communicate()
        if len(result[0]) == 0:
            raise IOError('No such media file ' + self.path)
        self.streams = []
        datalines = []
        self.video = []
        self.audio = []

        # for a in str(a.decode(sys.stdout.encoding)).split('\n'):
        lines = result[0].split('\n')
        for a in lines:
            if re.match('\[STREAM\]', a):
                datalines = []
            elif re.match('\[\/STREAM\]', a):
                self.streams.append(VideoStreamInfo(datalines))
                datalines = []
            else:
                datalines.append(a)
        for a in self.streams:
            if a.isAudio():
                self.audio.append(a)
            if a.isVideo():
                self.video.append(a)

    def _setupConversionTable(self):
        self._convTable = {}
        self._convTable["mpeg2video"] = "mpg"
        self._convTable["h264"] = "mp4"
        self._convTable["msmpeg4v2"] = "avi"
        # self._convTable["ansi"]="txt"
        # --more to come

    def getVideoStream(self):
        if len(self.video) == 0:
            return None
        return self.video[0]

    def getAudioStream(self):
        if len(self.audio) == 0:
            return None
        return self.audio[0]

    def getTargetExtension(self):
        codec = self.getVideoStream().getCodec()
        if codec in self._convTable:
            return self._convTable[codec]
        return ""

    def isKnownVideoFormat(self):
        codec = self.getVideoStream().getCodec()
        return codec in self._convTable


class VideoStreamInfo():
    # int values
    NA = "N/A"

    #     keys = ["index","width", "height","avg_frame_rate","duration","sample_rate"]
    #     stringKeys =["codec_type","codec_name"]
    #     divKeys =["display_aspect_ratio"]

    def __init__(self, dataArray):
        self.dataDict = {}
        self._parse(dataArray)

    def _parse(self, dataArray):
        for entry in dataArray:
            try:
                (key, val) = entry.strip().split('=')
            except:
                print
                "Error in entry:", entry
            if self.NA != val:
                # print ">>",key,"->",val
                self.dataDict[key] = val

    def getStreamIndex(self):
        if 'index' in self.dataDict:
            return int(self.dataDict['index'])

    def getAspectRatio(self):
        if 'display_aspect_ratio' in self.dataDict:
            z, n = self.dataDict['display_aspect_ratio'].split(':')
            div = round(float(z + ".0") / float(n + ".0") * 100.0)
            return div / 100.0
        return 1.0

    def getFrameRate(self):
        if 'avg_frame_rate' in self.dataDict:
            z, n = self.dataDict['avg_frame_rate'].split('/')
            return float(z)
        return 1.0

    def getCodec(self):
        if 'codec_name' in self.dataDict:
            return self.dataDict['codec_name']
        return self.NA

    def getWidth(self):
        if 'width' in self.dataDict:
            return self.dataDict['width']
        return self.NA

    def getHeight(self):
        if 'height' in self.dataDict:
            return self.dataDict['height']
        return self.NA

    def getCodecTimeBase(self):
        if 'codec_time_base' in self.dataDict:
            return self.dataDict['codec_time_base']
        return self.NA

    def getTimeBase(self):
        if 'time_base' in self.dataDict:
            return self.dataDict['time_base']
        return self.NA

    '''
    bitrate in kb (int)
    '''

    def bitRate(self):
        if "bit_rate" in self.dataDict:
            return int(self.dataDict["bit_rate"]) / 1000
        return 0

    '''
    length in seconds (float)
    '''

    def duration(self):
        if "duration" in self.dataDict:
            return float(self.dataDict["duration"])
        return 0.0

    '''
    FPS in float
    '''

    def frameRate(self):
        if "r_frame_rate" in self.dataDict:
            (n, z) = self.dataDict["r_frame_rate"].split("/")
            if int(z) != 0:
                return float(n) / float(z)
        return 0.0

    def isAudio(self):
        # Is this stream labelled as an audio stream?
        val = False
        if 'codec_type' in self.dataDict:
            if str(self.dataDict['codec_type']) == 'audio':
                val = True
        return val

    def isVideo(self):
        """
        Is the stream labelled as a video stream.
        """
        val = False
        if 'codec_type' in self.dataDict:
            if str(self.dataDict['codec_type']) == 'video':
                val = True
        return val


class FFFrameProbe():
    def __init__(self, video_file):
        self.frames = []
        self.path = video_file
        # self._readDataByLines()
        self._readData()

    def _readDataByLines(self):
        p = subprocess.Popen(["ffprobe", "-select_streams", "v:0", "-show_frames", self.path, "-v", "quiet"],
                             stdout=subprocess.PIPE)
        dataBucket = []
        proc = 0;
        while True:
            line = p.stdout.readline()
            if not line:
                break
            if re.match('\[\/FRAME\]', line):
                proc += 1
                print
                "p ", proc

            #             dataBucket = self.__processLine(line,dataBucket)
            #             if len(dataBucket)==0:
            #                 proc+=1
            #                 print "p ",proc

    def __processLine(self, aString, dataBucket):
        if re.match('\[FRAME\]', aString):
            dataBucket = []
        elif re.match('\[\/FRAME\]', aString):
            self.frames.append(VideoFrameInfo(dataBucket))
            dataBucket = []
        else:
            dataBucket.append(aString)
        return dataBucket

    def _readData(self):
        result = Popen(["ffprobe", "-select_streams", "v:0", "-show_frames", self.path, "-v", "quiet"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if len(result[0]) == 0:
            raise IOError('No such media file ' + self.path)
        self.frames = []
        datalines = []

        lines = result[0].split('\n')
        for a in lines:
            if re.match('\[FRAME\]', a):
                datalines = []
            elif re.match('\[\/FRAME\]', a):
                self.frames.append(VideoFrameInfo(datalines))
                datalines = []
            else:
                datalines.append(a)


# TODO: sublcass the init. Only accessor methods
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

    NA = "N/A"
    validKeys = ["key_frame", "pkt_pts_time", "pict_type", "coded_picture_number"]

    def __init__(self, dataArray):
        self.dataDict = {}
        self._parse(dataArray)

    def _parse(self, dataArray):
        for entry in dataArray:
            result = entry.strip().split('=')
            if len(result) == 2:
                key = result[0]
                val = result[1]
                if self.NA != val and key in self.validKeys:
                    self.dataDict[key] = val

    '''
    Usually an I-Frame
    '''

    def isKeyFrame(self):
        if self.dataDict["key_frame"]:
            return self.dataDict["key_frame"] == "1"
        return False

    '''
    Frame time in millisconds (float)
    '''

    def frameTime(self):
        if self.dataDict["pkt_pts_time"]:
            return float(self.dataDict["pkt_pts_time"]) * 1000.0
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


class FFMPEGCutter():
    def __init__(self, srcfilePath, targetPath):
        self.filePath = srcfilePath
        self.targetPath = targetPath
        self._tempDir = '/tmp'
        self._tmpCutList = self._getTempPath() + "cut.txt"
        self._fragmentCount = 1;
        self._messenger = None

    '''
    cuts a part of the film, saves it an returns the temp filename vor later concatintaion
    index = if more than one part of the film is cut
    '''

    def cutPart(self, startTimedelta, endTimedelta, index=0, nbrOfFragments=1):
        self._fragmentCount = nbrOfFragments
        scanTime = timedelta(seconds=20)
        prefetchTime = (startTimedelta - scanTime)
        if prefetchTime < scanTime:
            prefetchTime = timedelta(0)
            scanTime = startTimedelta

        prefetchString = timedeltaToFFMPEGString(prefetchTime)
        seekString = timedeltaToFFMPEGString(scanTime)

        deltaMillis = (endTimedelta - startTimedelta).microseconds
        deltaSeconds = (endTimedelta - startTimedelta).seconds
        durString = timedeltaToFFMPEGString(timedelta(seconds=deltaSeconds, microseconds=deltaMillis))
        # startString=timedeltaToFFMPEGString(startTimedelta)
        # ffmpeg -i in.m2t -ss 00:05:30.00 -t 00:29:00 -vcodec copy  -acodec copy out.mp4
        # ffmpeg -ss 00:05:00 -i in.m2t -ss 00:00:30.00 -t 00:29:00 -vcodec copy  -acodec copy out.mp4
        # print "ffmpeg -ss",prefetchString,"-i",self.filePath,"-ss",seekString,"-t",durString,"-vcodec","copy","-acodec","copy",self.targetPath
        # fast search - then slow search
        print
        prefetchString, "+", seekString, ">>", durString
        if nbrOfFragments is 1:
            fragment = self.targetPath
        else:
            fragment = self._getTempPath() + str(index) + ".m2t"
        print
        "generate file:", fragment
        self.say("Cutting part:" + str(index))
        pFFmpeg = subprocess.Popen(
            [BIN, "-hide_banner", "-y", "-ss", prefetchString, "-i", self.filePath, "-ss", seekString, "-t", durString,
             "-vcodec", "copy", "-acodec", "copy", fragment], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        while pFFmpeg.poll() is None:
            sleep(0.2)
            if not self.non_block_read("Cut part " + str(index) + ":", pFFmpeg.stdout):
                self.say("Cutting part %s failed" % (str(index)))
                return False

        self.say("Cutting done")
        return True

    def _getTempPath(self):
        return self._tempDir + '/vc_'

    def join(self):
        # add all files into a catlist: file '/tmp/mat_tmp0.m2t' ..etc
        # ffmpeg -f concat -i catlist.txt  -c copy concat.mp4
        if self._fragmentCount is 1:
            return

        self.say("Joining files...")

        with open(self._tmpCutList, 'w') as cutList:
            for index in range(0, self._fragmentCount):
                tmp = self._getTempPath() + str(index) + ".m2t"
                cutList.write("file '" + tmp + "'\n")

        pFFmpeg = subprocess.Popen(
            [BIN, "-hide_banner", "-y", "-f", "concat", "-i", self._tmpCutList, "-c", "copy", self.targetPath],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        while pFFmpeg.poll() is None:
            sleep(0.2)
            if not self.non_block_read("Join:", pFFmpeg.stdout):
                return False

        self.say("Films joined")
        self._cleanup()
        return True

    ''' Sets an object that understands say(aText)'''

    def setMessageDelegator(self, delegator):
        self._messenger = delegator

    def say(self, text):
        if self._messenger is not None:
            self._messenger.say(text)

            # reading non blocking

    def non_block_read(self, prefix, output):
        fd = output.fileno()
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        text = "."
        try:
            text = output.read()
            # print ">",text
            m = re.search('frame=[ ]*[0-9]+', text)
            p1 = m.group(0)
            m = re.search('time=[ ]*[0-9:.]+', text)
            p2 = m.group(0)
            self.say(prefix + " " + p1 + " - " + p2)
        except:
            if len(text) > 5:
                print
                "<" + text
        if "failed" in text:
            # Place to trigger message
            self.say(prefix + " >>>> Error:", text)
            return False
        else:
            return True

    def ensureAvailableSpace(self):
        if not self._hasEnoughAvailableSpace(self._tempDir):
            path = os.path.expanduser("~")
            self.ensureDirectory(path, "vc_temp")

    def _hasEnoughAvailableSpace(self, tmpDir):
        result = Popen(["df", "--output=avail", tmpDir], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        print
        "data:" + result[0]
        if len(result[1]) > 0:
            print
            "Error using df:" + result[1]
            return False

        rows = result[0].split('\n')
        if len(rows) > 1:
            # Filesystem      Size  Used Avail Use% Mounted on
            avail = int(rows[1]) * 1024

        needed = os.path.getsize(self.filePath)
        print
        "file size:", needed, " avail:", avail
        return needed <= avail

    def _cleanup(self):
        for index in range(self._fragmentCount):
            fragment = self._getTempPath() + str(index) + ".m2t"
            os.remove(fragment)

    def ensureDirectory(self, path, tail):
        # make sure the target dir is present
        if tail is not None:
            path = os.path.join(path, tail)
        if not os.access(path, os.F_OK):
            try:
                os.makedirs(path)
                os.chmod(path, 0o777)
            except OSError:
                print
                "Error creating directory"
                return
        self._tempDir = path

    def convertToTs(self, convertedFileName):
        # MOV files need to be converted:
        # ffmpeg -y -i big_buck_bunny_1080p_h264.mov -vcodec copy -bsf:v h264_mp4toannexb -acodec ac3 OUTPUT.ts
        print
        "TODO"


'''
if __name__ == "__main__":
    m = FFMPEGCutter("/home/matze/Videos/T3.m2t","/home/matze/Videos/T3x.mp4")
    starttd = timedelta(seconds=5)
    endtd = timedelta(seconds=700)
    m.cutPart(starttd, endtd, 0)
               

'''
if __name__ == "__main__":
    m = FFStreamProbe("/home/matze/Videos/kabel_eins/07_02_23_04-Batman & Robin.m2t")
    # m=FFStreamProbe("/home/matze/Videos/handbrake.txt")
    # m=FFStreamProbe("/home/matze/Videos/CT.m2t")
    # m=FFStreamProbe("/home/matze/Videos/big_buck_bunny_1080p_h264.mov")
    print
    "-------- Prim video -------------"
    s = m.getVideoStream()
    print
    "Index:", s.getStreamIndex()
    print
    "codec", s.getCodec()
    print
    "getCodecTimeBase: ", s.getCodecTimeBase()
    print
    "getTimeBase: ", s.getTimeBase()
    print
    "getAspect ", s.getAspectRatio()
    print
    "getFrameRate: ", s.getFrameRate()
    print
    "getFrameRate?: ", s.frameRate()
    print
    "getDuration: ", s.duration()
    print
    "getWidth: ", s.getWidth()
    print
    "getHeight: ", s.getHeight()
    print
    "isAudio: ", s.isAudio()
    print
    "isVideo: ", s.isVideo()

    print
    "-------- Prim audio -------------"
    s = m.getAudioStream()
    if not s:
        print
        "No audio"
        exit(0)
    print
    "Index:", s.getStreamIndex()
    print
    "getCodec:", s.getCodec()
    print
    "getCodecTimeBase: ", s.getCodecTimeBase()
    print
    "getTimeBase: ", s.getTimeBase()
    print
    "getFrameRate: ", s.getFrameRate()
    print
    "getFrameRate?: ", s.frameRate()
    print
    "getDuration: ", s.duration()
    print
    "isAudio: ", s.isAudio()
    print
    "isVideo: ", s.isVideo()

    print
    "-------- all streams -------------"
    for s in m.streams:
        print
        "Index:", s.getStreamIndex()
        print
        "getCodec:", s.getCodec()
        print
        "getCodecTimeBase: ", s.getCodecTimeBase()
        print
        "getTimeBase: ", s.getTimeBase()
        print
        "getAspect ", s.getAspectRatio()
        print
        "getFrameRate: ", s.getFrameRate()
        print
        "getDuration: ", s.duration()
        print
        "getWidth: ", s.getWidth()
        print
        "getHeight: ", s.getHeight()
        print
        "isAudio: ", s.isAudio()
        print
        "isVideo: ", s.isVideo()

    cutter = FFMPEGCutter("/home/matze/Videos/kabel_eins/07_02_23_04-Batman & Robin.m2t", "/home/matze/Videos/x.mp4")
    cutter.ensureAvailableSpace()
''' 
    #Very slow!!!
    f = FFFrameProbe("/home/matze/Videos/09_21_13_33-Indiana Jones und der Tempel des Todes.m2t")
    print len(f.frames)
'''
# ----------- documatation -------------

'''
>> Header info very fast
ffprobe -select_streams v:0 -show_streams Videos/007Test.mp4 -v quiet
[STREAM]
index=0
codec_name=h264
codec_long_name=H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10
profile=High
codec_type=video
codec_time_base=1/100
codec_tag_string=avc1
codec_tag=0x31637661
width=1280
height=720
has_b_frames=0
sample_aspect_ratio=1:1
display_aspect_ratio=16:9
pix_fmt=yuv420p
level=40
color_range=tv
color_space=bt709
timecode=N/A
id=N/A
r_frame_rate=50/1
avg_frame_rate=50/1
time_base=1/90000
start_pts=44730
start_time=0.497000
duration_ts=27415800
duration=304.620000
bit_rate=7576497
max_bit_rate=N/A
bits_per_raw_sample=8
nb_frames=15231
nb_read_frames=N/A
nb_read_packets=N/A
DISPOSITION:default=1
DISPOSITION:dub=0
DISPOSITION:original=0
DISPOSITION:comment=0
DISPOSITION:lyrics=0
DISPOSITION:karaoke=0
DISPOSITION:forced=0
DISPOSITION:hearing_impaired=0
DISPOSITION:visual_impaired=0
DISPOSITION:clean_effects=0
DISPOSITION:attached_pic=0
TAG:language=und
TAG:handler_name=VideoHandler
[/STREAM]

add -count_Frames (takes very long!) and you get:
nb_frames=15231
nb_read_frames=15228

#line by line thru pipe: makes progress posible
p = subprocess.Popen(["ls"], stdout=subprocess.PIPE)
while True:
    line = p.stdout.readline()
    if not line:
        break
    print line

'''
