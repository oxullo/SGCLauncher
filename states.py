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

class IntroState(engine.FadeGameState):
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

    def _onKeyDown(self, event):
        if event.keystring == 'n':
            self.setupGameInfo(registry.games.getNextGame())
        elif event.keystring == 'p':
            self.setupGameInfo(registry.games.getPrevGame())

    def setupGameInfo(self, game):
        self.__name.text = game['name'].upper()
        self.__author.text = game['author'].upper()
        self.__description.text = game['description'].upper()
        self.__players.text = game['players'].upper()


class VoteState(engine.FadeGameState):
    def _init(self):
        pass

    def _onKeyDown(self, event):
        if event.keystring == 'n':
            self.app.changeState('Intro')
