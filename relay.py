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

import serial
import ctypes
import logging

import libavg

u0 = None

class U0Relay(object):
    def __init__(self, port):
        self.__serialObj = serial.Serial(port, timeout=0)
        self.__oldStates = [False] * 5
        self.__callbacks = []
        self.__isRelayActive = False

        libavg.player.setOnFrameHandler(self.__poll)

    def registerStateChangeCallback(self, callback):
        self.__callbacks.append(callback)

    def forceStatesUpdate(self):
        return self.__notifyStates(self.__oldStates, [True] * 5, False)

    def setRelayActive(self, active):
        self.__isRelayActive = active

    def __poll(self):
        line = self.__serialObj.readline()
        if line:
            line = line.strip()
            try:
                mask = int(line)
                logging.debug('mask: %s' % mask)
            except ValueError:
                logging.debug('Garbage received from serial: %s' % str(list(line)))
            else:
                self.__processMask(mask)

    def __processMask(self, mask):
        '''
        Bitmask integer to a list of states (13 -> [True, True, False, False, True]
        '''
        states = []

        for i in xrange(6):
            if mask & (1 << i):
                thisState = True
            else:
                thisState = False

            states.append(thisState)

        self.__processStates(states)

    def __processStates(self, states):
        '''
        Prepare a notification for the changed states only
        '''
        changed = [s1 != s2 for s1, s2 in zip(states, self.__oldStates)]

        self.__notifyStates(states, changed, self.__isRelayActive)
        self.__oldStates = states

    def __notifyStates(self, states, which, inject):
        for i in xrange(5):
            if which[i]:
                for callback in self.__callbacks:
                    callback(i, states[i])

                    if inject:
                        self.__injectKey(i, states[i])

    def __injectKey(self, index, state):
        vkey = 0x31 + index
        scan = ctypes.windll.user32.MapVirtualKeyA(vkey + index, 0)

        eventf = 0 if state else 2

        ctypes.windll.user32.keybd_event(vkey, scan, eventf, 0)

        logging.debug('Sent key 0x%x, eventf=%d' % (vkey, eventf))


def init(port):
    global u0

    u0 = U0Relay(port)
