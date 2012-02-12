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
libavg.player = avg.Player.get()

import engine
import states
import registry
import process


class LauncherApp(engine.Application):
    def init(self):
        logging.getLogger().setLevel(logging.DEBUG)
        process.init()

        avg.ImageNode(href='background.png', parent=self._parentNode)

#        self.propagateKeys = False
#        self.u0Interface = U0Interface('COM3', self.__onU0StateChanged)
#        self.u0KeyTranslator = U0KeyTranslator()

        self.registerState('Info', states.InfoState())
        self.registerState('Vote', states.VoteState())

        self.bootstrap('Info')

    def startKeyFlow(self):
        self.propagateKeys = True

    def terminateApp(self):
        self.__setFocusBack()

        if self.proc is not None:
            self.addLogLine('Terminating %s' % self.proc.game['name'])
            self.proc.terminate()
            self.proc = None
    def __onU0StateChanged(self, index, state):
        if self.propagateKeys:
            self.u0KeyTranslator.stateToKey(index, state)

if __name__ == '__main__':
    import os

    os.environ['AVG_DEPLOY'] = '1'
    LauncherApp.start(resolution=(1920, 1080))
