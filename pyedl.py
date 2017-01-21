#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Originally written by https://github.com/sbidoul/edledit
# Additional changes by https://github.com/KnisterPeter/edl-editor
#

import re
from datetime import timedelta

ACTION_NONE = None
ACTION_SKIP = 0
ACTION_MUTE = 1

_ = lambda s: s

block_re = re.compile(r"(\d+(?:\.?\d+)?)\s(\d+(?:\.?\d+)?)\s([01])")


def _td2str(td):
    if td is None or td == timedelta.max:
        return ""
    else:
        return "%f" % (td.days * 86400 + td.seconds + td.microseconds / 1000000.)


class EDLBlock(object):
    def __init__(self, startTime, stopTime, action=ACTION_SKIP):
        # pre-initialize so the validation during intialization will work
        self.__startTime = timedelta.min
        self.__stopTime = timedelta.max
        self.__action = ACTION_NONE
        # set properties (validates)
        self.startTime = startTime
        self.stopTime = stopTime
        self.action = action

    @property
    def action(self):
        return self.__action

    @action.setter
    def action(self, value):
        self.__action = value

    @property
    def startTime(self):
        return self.__startTime

    @startTime.setter
    def startTime(self, value):
        if value > self.__stopTime:
            raise RuntimeError(_("start time must be before stop time"))
        self.__startTime = value

    @property
    def stopTime(self):
        if self.__stopTime == timedelta.max:
            return None
        else:
            return self.__stopTime

    @stopTime.setter
    def stopTime(self, value):
        if value is None:
            value = timedelta.max
        if value < self.__startTime:
            raise RuntimeError(_("end time must be after start timer"))
        self.__stopTime = value

    def __str__(self):
        return "%s\t%s\t%d" % (_td2str(self.startTime), _td2str(self.stopTime),
                               self.action)

    def overlaps(self, block):
        # not optimal but easy to understand
        return self.containsTime(block.__startTime) or \
               self.containsTime(block.__stopTime) or \
               block.containsTime(self.__startTime) or \
               block.containsTime(self.__stopTime)

    def containsTime(self, aTime):
        if aTime is None:
            aTime = timedelta.max
        return self.__startTime <= aTime < self.__stopTime

    def containsEndTime(self, aTime):
        if aTime is None:
            aTime = timedelta.max
        return self.__startTime < aTime <= self.__stopTime


class EDL(list):
    def findBlock(self, aTime):
        for block in self:
            if block.containsTime(aTime):
                return block
        return None

    def normalize(self, totalTime=None):
        # TODO remove zero-length blocks
        # self.sort(key=lambda block: block.startTime)
        for block in self:
            if totalTime:
                if block.stopTime is None or block.stopTime > totalTime:
                    block.stopTime = totalTime
        i = 0
        while i < len(self):
            if i > 0:
                prev = self[i - 1]
                curr = self[i]
                if prev.overlaps(curr):
                    if prev.startTime > curr.startTime:
                        prev.startTime = curr.startTime
                    if prev.stopTime < curr.stopTime:
                        prev.stopTime = curr.stopTime
                    del self[i:i + 1]
                    i -= 1
            i += 1
        self.validate()

    def newBlock(self, start, end):
        self.append(EDLBlock(start, end))

    def deleteBlock(self, aTime):
        """ Delete the block overlapping aTime """
        for i, block in enumerate(self):
            if block.containsTime(aTime):
                del self[i:i + 1]
                return
        raise RuntimeError(_("No block found containing time %s") % aTime)

    def getNextBoundary(self, aTime):
        for block in self:
            if block.startTime > aTime:
                return block.startTime
            if block.stopTime is None or block.stopTime > aTime:
                return block.stopTime
        return None

    def getPrevBoundary(self, aTime):
        for block in reversed(self):
            if block.stopTime is not None and block.stopTime < aTime:
                return block.stopTime
            if block.startTime < aTime:
                return block.startTime
        return timedelta(0)

    def validate(self):
        prevBlock = None
        for block in self:
            if not isinstance(block, EDLBlock):
                raise RuntimeError(_("Element %s not an EDLBlock") % (block,))
            if prevBlock is not None:
                if prevBlock.startTime >= block.startTime:
                    raise RuntimeError(_("block '%s' and '%s' not in order") % (prevBlock, block))
                if prevBlock.overlaps(block):
                    raise RuntimeError(_("block '%s' overlaps block '%s'") % (prevBlock, block))
            prevBlock = block


def load(fp):
    edl = EDL()
    for line in fp.readlines():
        line = line.strip()
        if not line:
            pass
        mo = block_re.match(line)
        if not mo:
            raise RuntimeError(_("Invalid EDL line: '%s'") % (line,))
        start, stop, action = mo.groups()
        edl.append(EDLBlock(
            timedelta(seconds=float(start)),
            timedelta(seconds=float(stop)),
            int(action)))
    return edl


def dump(edl, f):
    for block in edl:
        f.write(str(block))
        f.write("\n")
