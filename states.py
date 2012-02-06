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

class IntroState(engine.FadeGameState):
    def _init(self):
        helpers.BlueText(text='NOW PLAYING',
                fontsize=78,
                pos=(710, 207),
                parent=self)

        helpers.YellowText(text='THE NAME OF THE GAME',
                fontsize=107,
                pos=(710, 273),
                parent=self)

        helpers.BlueText(text='AUTHOR',
                fontsize=60,
                pos=(710, 434),
                parent=self)

        helpers.BlueText(text='PLAYERS',
                fontsize=60,
                pos=(1298, 434),
                parent=self)

        helpers.BlueText(text='DESCRIPTION',
                fontsize=60,
                pos=(710, 674),
                parent=self)

        helpers.YellowText(text='THE NAME OF THE AUTHOR/S',
                fontsize=60,
                pos=(710, 500),
                size=(536, 186),
                parent=self)

        helpers.YellowText(text='Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent adipiscing sem sed turpis gravida id rutrum mi ullamcorper. Nulla ac rhoncus nisi. In et ligula non mi interdum pharetra.'.upper(),
                fontsize=48,
                pos=(710, 747),
                size=(1160, 306),
                parent=self)

        helpers.YellowText(text='2 TO 5',
                fontsize=108,
                pos=(1298, 487),
                parent=self)

    def _onKeyDown(self, event):
        if event.keystring == 'n':
            self.app.changeState('Vote')

class VoteState(engine.FadeGameState):
    def _init(self):
        pass

    def _onKeyDown(self, event):
        if event.keystring == 'n':
            self.app.changeState('Intro')
