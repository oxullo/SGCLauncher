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

import libavg
from libavg import avg

import engine
import helpers
import registry

class InfoState(engine.FadeGameState):
    def _init(self):
        helpers.BlueText(text='NOW PLAYING',
                fontsize=78,
                pos=(600, 207),
                parent=self)

        helpers.BlueText(text='AUTHOR/S',
                fontsize=60,
                pos=(710, 434),
                parent=self)

        helpers.BlueText(text='PLAYERS',
                fontsize=60,
                pos=(1498, 434),
                parent=self)

        helpers.BlueText(text='DESCRIPTION',
                fontsize=60,
                pos=(710, 674),
                parent=self)

        self.__name = helpers.YellowText(
                fontsize=107,
                pos=(600, 273),
                parent=self)

        self.__author = helpers.YellowText(
                fontsize=60,
                pos=(710, 500),
                size=(736, 186),
                parent=self)

        self.__description = helpers.YellowText(
                fontsize=48,
                pos=(710, 747),
                size=(1160, 306),
                parent=self)

        self.__players = helpers.YellowText(
                fontsize=108,
                pos=(1498, 487),
                parent=self)

    def _preTransIn(self):
        self.setupGameInfo(registry.games.getCurrentGame())

    def _onKeyDown(self, event):
        if event.keystring == 'n':
            self.setupGameInfo(registry.games.getNextGame())
        elif event.keystring == 'p':
            self.setupGameInfo(registry.games.getPrevGame())
        elif event.keystring == 'v':
            self.onGameExited()

    def setupGameInfo(self, game):
        self.__name.text = game['name'].upper()
        self.__author.text = game['author'].upper()
        self.__description.text = game['description'].upper()
        self.__players.text = game['players'].upper()

    def onGameExited(self):
        self.app.changeState('Vote')


class VoteState(engine.FadeGameState):
    VOTE_TIME = 5
    HURRYUP_AFTER = 3
    VOTE_TEXTS = ['LIKED IT? STEP ON A PAD!', 'NOT SO MANY FANS',
            'NO MORE FANS?', 'BLABLA',
            'FROB FRAB', 'OUTSTANDING!']

    def _init(self):
        self.__divRealtimeVote = avg.DivNode(parent=self)
        self.__divFinalVote = avg.DivNode(parent=self)

        self.__hurryup = helpers.HurryupIcon(pos=(1645, 591),
                parent=self.__divRealtimeVote)

        helpers.BlueText(text='NOW VOTING',
                fontsize=78,
                pos=(600, 207),
                parent=self)

        helpers.YellowText(text='VOTES',
                fontsize=120,
                pos=(878, 546),
                parent=self.__divFinalVote)

        helpers.BlueText(text='CLOSING VOTE IN',
                fontsize=77,
                pos=(1285, 461),
                parent=self.__divRealtimeVote)

        self.__name = helpers.YellowText(
                fontsize=107,
                pos=(600, 273),
                parent=self)

        self.__vote = helpers.YellowText(
                fontsize=253,
                pos=(717, 434),
                parent=self.__divFinalVote)

        self.__voteText = helpers.YellowText(
                fontsize=57,
                pos=(733, 685),
                parent=self.__divFinalVote)

        self.__voteTime = helpers.YellowText(
                fontsize=144,
                pos=(1564, 539),
                alignment='center',
                parent=self.__divRealtimeVote)

        self.__pacs = []
        for i in xrange(5):
            avg.ImageNode(href='u0pad.png', pos=(687 + 230 * i, 834),
                    parent=self)
            self.__pacs.append(avg.ImageNode(
                    href='pac.png',
                    pos=(717 + 230 * i, 833),
                    opacity=0,
                    parent=self))

        self.__tmrClock = None
        self.__timeLeft = None
        self.__voteArbitrator = helpers.VoteArbitrator(self.__onVoteChanged)

    def setupGameInfo(self, game):
        self.__name.text = game['name'].upper()

    def _onKeyDown(self, event):
        if event.keystring == 'n':
            self.app.changeState('Info')
        elif event.keycode in range(49, 54):
            self.__voteArbitrator.setVote(event.keystring)

    def _onKeyUp(self, event):
        if event.keycode in range(49, 54):
            self.__voteArbitrator.unsetVote(event.keystring)

    def _preTransIn(self):
        self.setupGameInfo(registry.games.getCurrentGame())
        self.__tmrClock = libavg.player.setInterval(1000, self.__tick)
        self.__voteArbitrator.reset()
        self.__divFinalVote.x = 0
        self.__voteText.opacity = 1
        self.__divRealtimeVote.opacity = 1
        self.__timeLeft = self.VOTE_TIME
        self.__syncTimeLeft()

    def _preTransOut(self):
        registry.games.getNextGame()
        self.__resetTimer()

    def __tick(self):
        self.__timeLeft -= 1

        self.__syncTimeLeft()

        if self.__timeLeft == 0:
            self.__onTimerElapsed()
            self.__resetTimer()

    def __syncTimeLeft(self):
        self.__voteTime.text = '%ds' % self.__timeLeft
        if self.__timeLeft > self.HURRYUP_AFTER:
            self.__hurryup.deactivate()
        else:
            self.__hurryup.activate()

    def __onVoteChanged(self, vote, mask):
        for index, state in enumerate(mask):
            self.__pacs[index].opacity = 1 if state else 0

        self.__vote.text = str(vote)
        self.__voteText.text = self.VOTE_TEXTS[vote]

    def __onTimerElapsed(self):
        avg.fadeOut(self.__divRealtimeVote, 300)
        self.__voteArbitrator.freeze()
        avg.EaseInOutAnim(self.__divFinalVote, 'x', 400, 0, 300, 200, 300).start()
        self.__voteText.opacity = 0

    def __resetTimer(self):
        if self.__tmrClock is not None:
            libavg.player.clearInterval(self.__tmrClock)
            self.__tmrClock = None
