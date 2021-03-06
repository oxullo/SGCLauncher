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

import engine
import helpers
import registry
import process
import relay
import config


class InfoState(engine.FadeGameState):
    def _init(self):
        helpers.BlueText(text='ABOUT TO PLAY',
                fontsize=78,
                pos=(580, 207),
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
                pos=(580, 273),
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

        self.__currentProcess = None
        self.__autostartTimer = None
        self.registerPeriodicTimer(100, self.__pollStatus)
        self.registerBgTrack('01.mp3', 0.3)

    def _preTransIn(self):
        self.setupGameInfo(registry.games.getCurrentGame())
        if config.data.autoskip:
            self.__autostartTimer = self.registerOneShotTimer(
                    config.data.infostateduration * 1000,
                    self.__runGame)

    def _onKeyDown(self, event):
        if event.keystring == 'n':
            self.__loadNextGame()
        elif event.keystring == 'p':
            self.setupGameInfo(registry.games.getPrevGame())
        elif event.keystring == 'v':
            self.__onGameExited()
        elif event.keystring == 'x' and self.__currentProcess is None:
            self.__runGame()

    def setupGameInfo(self, game):
        self.__name.text = game['name'].upper()
        self.__author.text = game['author'].upper()
        self.__description.text = game['description'].upper()
        self.__players.text = game['players'].upper()

    def __pollStatus(self):
        if self.__currentProcess:
            if self.__currentProcess.state == process.Process.STATE_RUNNING:
                if registry.games.getCurrentGame()['keysdelay'] is None:
                    relay.u0.setRelayActive(self.__currentProcess.hasFocus())
                return
            elif self.__currentProcess.state == process.Process.STATE_BADEXIT:
                logging.error('%s crashed' % self.__currentProcess.game['handle'])
            elif self.__currentProcess.state == process.Process.STATE_CANTSTART:
                logging.error('%s couldn\'t be '
                        'started' % self.__currentProcess.game['handle'])
            elif self.__currentProcess.state == process.Process.STATE_TERMINATED:
                logging.info('%s exited' % self.__currentProcess.game['handle'])
            elif self.__currentProcess.state == process.Process.STATE_INITIALIZING:
                logging.debug('%s slow to start, '
                        'waiting' % self.__currentProcess.game['handle'])
                return

            process.restoreLauncherWindow()
            self.__currentProcess = None
            self.__onGameExited()

    def __runGame(self):
        self._doBgTrackTransOut()

        if config.data.autoskip and not self.__autostartTimer.elapsed:
            self.__autostartTimer.kill()

        game = registry.games.getCurrentGame()
        process.hideLauncherWindow()
        self.__currentProcess = process.Process(game)
        self.__currentProcess.start()

        if game['keysdelay'] is not None:
            logging.info('Preparing manual injection mode for game %s '
                    '(delay=%d)' % (game['handle'], game['keysdelay']))
            self.registerOneShotTimer(game['keysdelay'],
                    lambda: relay.u0.setRelayActive(True))

        self.registerOneShotTimer(5000, lambda: process.moveMouseOut())
        if config.data.autoskip:
            self.registerOneShotTimer(config.data.defaultgameduration * 1000,
                    self.__terminateGame)

    def __terminateGame(self):
        if self.__currentProcess is not None:
            self.__currentProcess.terminate()

    def __loadNextGame(self):
        self.setupGameInfo(registry.games.getNextGame())

    def __onGameExited(self):
        relay.u0.setRelayActive(False)
        self.__currentProcess = None

        if config.data.voting:
            self.app.changeState('Vote')
        else:
            self.__loadNextGame()


class VoteState(engine.FadeGameState):
    def _init(self):
        self.__voteTimer = helpers.VoteTimer(self.__onTimerElapsed,
                pos=(1285, 431), parent=self)
        self.__divFinalVote = avg.DivNode(parent=self)

        self.__nowVoting = helpers.BlueText(text='NOW VOTING',
                fontsize=122,
                pos=(442, 225),
                parent=self)

        self.__name = helpers.YellowText(
                fontsize=60,
                pos=(1146, 250),
                parent=self)

        self.__vote = helpers.YellowText(
                fontsize=253,
                pos=(717, 434),
                parent=self.__divFinalVote)

        self.__voteText = helpers.YellowText(text='LIKED IT? STAND STILL ON A PAD!',
                fontsize=57,
                pos=(733, 685),
                parent=self.__divFinalVote)

        self.__voteLabel = helpers.YellowText(text='VOTES',
                fontsize=120,
                pos=(878, 546),
                parent=self.__divFinalVote)

        self.__pacs = []
        for i in xrange(5):
            avg.ImageNode(href='u0pad.png', pos=(687 + 230 * i, 834),
                    parent=self)
            self.__pacs.append(avg.ImageNode(
                    href='pac.png',
                    pos=(717 + 230 * i, 833),
                    opacity=0,
                    parent=self))

        engine.SoundManager.allocate('bleep.mp3')
        self.__u0FeedActive = False

        self.__voteArbitrator = helpers.VoteArbitrator(self.__onVoteChanged)
        relay.u0.registerStateChangeCallback(self.__onU0StateChanged)
        self.registerPeriodicTimer(200, self.__blinkNowVoting)
        self.__shouldBlink = True
        self.registerBgTrack('02.mp3', 0.3)

    def setupGameInfo(self, game):
        self.__name.text = game['name'].upper()

    def _onKeyDown(self, event):
        if event.keystring == 'n':
            self.app.changeState('Info')
        elif event.keycode in range(49, 54):
            self.__voteArbitrator.setVoteByKey(event.keystring)

    def _onKeyUp(self, event):
        if event.keycode in range(49, 54):
            self.__voteArbitrator.unsetVoteByKey(event.keystring)

    def _preTransIn(self):
        self.setupGameInfo(registry.games.getCurrentGame())
        self.__voteArbitrator.reset()
        self.__divFinalVote.x = 0
        self.__voteText.opacity = 1
        self.__voteTimer.start()
        self.__shouldBlink = True

    def _postTransIn(self):
        self.__u0FeedActive = True
        relay.u0.forceStatesUpdate()

    def _preTransOut(self):
        self.__u0FeedActive = False
        registry.games.getNextGame()
        self.__voteTimer.reset()

    def __blinkNowVoting(self):
        if not self.__shouldBlink or self.__nowVoting.opacity == 0:
            self.__nowVoting.opacity = 1
        else:
            self.__nowVoting.opacity = 0

    def __onVoteChanged(self, votes, mask):
        for index, state in enumerate(mask):
            self.__pacs[index].opacity = 1 if state else 0

        if votes == 1:
            self.__voteLabel.text = 'VOTE'
        else:
            self.__voteLabel.text = 'VOTES'

        self.__vote.text = str(votes)

    def __onTimerElapsed(self):
        self.__u0FeedActive = False
        self.__voteArbitrator.freeze()
        avg.EaseInOutAnim(self.__divFinalVote, 'x', 400, 0, 300, 200, 300).start()
        self.__voteText.opacity = 0
        if config.data.autoskip:
            self.registerOneShotTimer(config.data.votestateduration * 1000,
                    lambda: self.app.changeState('Info'))
        self.__shouldBlink = False

    def __onU0StateChanged(self, index, state):
        if self.__u0FeedActive:
            if state:
                engine.SoundManager.play('bleep.mp3')
                self.__voteArbitrator.setVoteByIndex(index)
            else:
                self.__voteArbitrator.unsetVoteByIndex(index)
