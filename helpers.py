#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# STATTMEDIA GAME CONTEST games launcher
# Copyright (c) 2011-2012 OXullo Intersecans <x@brainrapers.org>. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification, are
# permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this list of
#    conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice, this list
#    of conditions and the following disclaimer in the documentation and/or other
#    materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY OXullo Intersecans ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL OXullo Intersecans OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
# The views and conclusions contained in the software and documentation are those of the
# authors and should not be interpreted as representing official policies, either 
# expressed or implied, of OXullo Intersecans.

import logging

import libavg
from libavg import avg


class SGCText(avg.WordsNode):
    def __init__(self, **kwargs):
        kwargs['font'] = 'Geogrotesque'
        kwargs['variant'] = 'Medium'
        super(SGCText, self).__init__(**kwargs)


class BlueText(SGCText):
    def __init__(self, **kwargs):
        kwargs['color'] = '48a5ae'
        super(BlueText, self).__init__(**kwargs)


class YellowText(SGCText):
    def __init__(self, **kwargs):
        kwargs['color'] = 'f0e345'
        super(YellowText, self).__init__(**kwargs)


class HurryupIcon(avg.ImageNode):
    STATE_ACTIVE = 'STATE_ACTIVE'
    STATE_INACTIVE = 'STATE_INACTIVE'
    def __init__(self, **kwargs):
        kwargs['href'] = 'hurryup.png'
        super(HurryupIcon, self).__init__(**kwargs)
        self.__state = self.STATE_INACTIVE
        self.opacity = 0
        self.__tmrAnim = None

    def activate(self):
        if self.__state == self.STATE_INACTIVE:
            self.opacity = 1
            self.__state = self.STATE_ACTIVE
            self.__tmrAnim = libavg.player.setInterval(200, self.__animate)

    def deactivate(self):
        if self.__state == self.STATE_ACTIVE:
            self.opacity = 0
            self.__state = self.STATE_INACTIVE
            libavg.player.clearInterval(self.__tmrAnim)
            self.__tmrAnim = None

    def __animate(self):
        if self.opacity == 1:
            self.opacity = 0
        else:
            self.opacity = 1


class VoteArbitrator(object):
    STATE_VOTE_OPEN = 'STATE_VOTE_OPEN'
    STATE_VOTE_CLOSED = 'STATE_VOTE_CLOSED'

    def __init__(self, voteChangedCb):
        self.__voteChangedCb = voteChangedCb
        self.reset()

    def reset(self):
        self.__state = self.STATE_VOTE_OPEN
        self.__currentVote = 0
        self.__mask = [False] * 5
        self.__updateVote()

    def setVote(self, pad):
        if self.__state != self.STATE_VOTE_OPEN:
            return

        try:
            padIndex = int(pad) - 1
        except ValueError:
            logging.error('Error while attempting to convert pad %s to index' % pad)
        else:
            self.__mask[padIndex] = True
            self.__updateVote()

    def unsetVote(self, pad):
        if self.__state != self.STATE_VOTE_OPEN:
            return

        try:
            padIndex = int(pad) - 1
        except ValueError:
            logging.error('Error while attempting to convert pad %s to index' % pad)
        else:
            self.__mask[padIndex] = False
            self.__updateVote()

    def freeze(self):
        print 'Final vote:', self.__currentVote
        self.__state = self.STATE_VOTE_CLOSED

    def __updateVote(self):
        self.__currentVote = 0
        for state in self.__mask:
            if state:
                self.__currentVote += 1

        self.__voteChangedCb(self.__currentVote, self.__mask)


class VoteTimer(avg.DivNode):
    VOTE_TIME = 5
    HURRYUP_AFTER = 3

    def __init__(self, timerElapsedCb, **kwargs):
        super(VoteTimer, self).__init__(**kwargs)

        self.__timerElapsedCb = timerElapsedCb

        self.__hurryup = HurryupIcon(pos=(360, 130), parent=self)

        BlueText(text='CLOSING VOTE IN',
                fontsize=77,
                pos=(0, 0),
                parent=self)

        self.__voteTime = YellowText(
                fontsize=144,
                pos=(300, 78),
                alignment='center',
                parent=self)

        self.__tmrClock = None
        self.__timeLeft = None

    def start(self):
        self.opacity = 1
        self.__timeLeft = self.VOTE_TIME
        self.__tmrClock = libavg.player.setInterval(1000, self.__tick)
        self.__syncTimeLeft()

    def reset(self):
        self.__killTimer()

    def __tick(self):
        self.__timeLeft -= 1

        self.__syncTimeLeft()

        if self.__timeLeft == 0:
            self.__onTimerElapsed()
            self.__killTimer()

    def __syncTimeLeft(self):
        self.__voteTime.text = '%ds' % self.__timeLeft
        if self.__timeLeft > self.HURRYUP_AFTER:
            self.__hurryup.deactivate()
        else:
            self.__hurryup.activate()

    def __onTimerElapsed(self):
        avg.fadeOut(self, 300)
        self.__killTimer()
        self.__timerElapsedCb()

    def __killTimer(self):
        if self.__tmrClock is not None:
            libavg.player.clearInterval(self.__tmrClock)
            self.__tmrClock = None
