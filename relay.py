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
import socket
import time
import errno

import libavg

u0 = None

class U0RelayBase(object):
    def __init__(self):
        self._oldStates = [False] * 5
        self._callbacks = []
        self._isRelayActive = False
        self._readBuffer = ''

        libavg.player.setOnFrameHandler(self._poll)

    def registerStateChangeCallback(self, callback):
        self._callbacks.append(callback)

    def forceStatesUpdate(self):
        return self._notifyStates(self._oldStates, [True] * 5, False)

    def setRelayActive(self, active):
        self._isRelayActive = active

    def _processBuffer(self):
        try:
            mask = int(self._readBuffer)
            self._readBuffer = ''
            logging.debug('mask: %s' % mask)
        except ValueError:
            logging.warning('Garbage received from serial'
                    ': %s' % str(list(self._readBuffer)))
            self._readBuffer = ''
        else:
            self._processMask(mask)

    def _processMask(self, mask):
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

        self._processStates(states)

    def _processStates(self, states):
        '''
        Prepare a notification for the changed states only
        '''
        changed = [s1 != s2 for s1, s2 in zip(states, self._oldStates)]

        self._notifyStates(states, changed, self._isRelayActive)
        self._oldStates = states

    def _notifyStates(self, states, which, inject):
        for i in xrange(5):
            if which[i]:
                for callback in self._callbacks:
                    callback(i, states[i])

                if inject:
                    self._injectKey(i, states[i])

    def _injectKey(self, index, state):
        vkey = 0x31 + index
        scan = ctypes.windll.user32.MapVirtualKeyA(vkey + index, 0)

        eventf = 0 if state else 2

        ctypes.windll.user32.keybd_event(vkey, scan, eventf, 0)

        logging.debug('Sent key 0x%x, eventf=%d' % (vkey, eventf))


class U0RelaySerial(U0RelayBase):
    def __init__(self, port):
        super(U0RelaySerial, self).__init__()
        self.__serialObj = serial.Serial(port, timeout=0)

    def _poll(self):
        while True:
            ch = self.__serialObj.read()

            if not ch:
                return
            elif ch == '\n':
                self._processBuffer()
            elif ch != '\r':
                self._readBuffer += ch


class U0RelayTCP(U0RelayBase):
    U0NET_PORT = 10000
    RECONNECT_DELAY = 5

    STATE_CONNECTING = 'STATE_CONNECTING'
    STATE_CONNECTED = 'STATE_CONNECTED'

    def __init__(self, host):
        super(U0RelayTCP, self).__init__()
        self.__host = host
        self.__state = self.STATE_CONNECTING
        self.__nextConnectionAttempt = 0
        self.__checkConnectionState()

    def _poll(self):
        self.__checkConnectionState()

        if self.__state == self.STATE_CONNECTED:
            try:
                ch = self.__socket.recv(1)
            except socket.error, e:
                if e.errno != errno.EWOULDBLOCK:
                    print e
                    self.__socket.close()
                    self.__state = self.STATE_CONNECTING

                return

            if ch == '\n':
                self._processBuffer()
            elif ch != '\r':
                self._readBuffer += ch

    def __connect(self):
        try:
            self.__socket = socket.create_connection((self.__host, self.U0NET_PORT), 0.5)
        except Exception, e:
            logging.error('U0RelayTCP: cannot connect (%s)' % str(e))
            self.__nextConnectionAttempt = time.time() + self.RECONNECT_DELAY
        else:
            logging.info('U0RelayTCP connected to %s' % self.__host)
            self.__state = self.STATE_CONNECTED
            self.__socket.setblocking(0)

    def __checkConnectionState(self):
        if (self.__state == self.STATE_CONNECTING and
                time.time() >= self.__nextConnectionAttempt):
            self.__connect()


def initSerial(port):
    global u0

    u0 = U0RelaySerial(port)

def initNet(host):
    global u0

    u0 = U0RelayTCP(host)
