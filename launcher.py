#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# STATTMEDIA GAME CONTEST games launcher
# Copyright (c) 2010-2011 OXullo Intersecans <x@brainrapers.org>. All rights reserved.
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

import os
import subprocess
import threading
import time
import logging
import serial

import ConfigParser

import ctypes
import win32api
import win32con
import win32gui
import win32process

import libavg
from libavg import avg
libavg.player = avg.Player.get()

TH32CS_SNAPPROCESS = 0x00000002
class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_ulong),
        ("cntUsage", ctypes.c_ulong),
        ("th32ProcessID", ctypes.c_ulong),
        ("th32DefaultHeapID", ctypes.c_ulong),
        ("th32ModuleID", ctypes.c_ulong),
        ("cntThreads", ctypes.c_ulong),
        ("th32ParentProcessID", ctypes.c_ulong),
        ("pcPriClassBase", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("szExeFile", ctypes.c_char * 260)]


class Game(object):
    def __init__(self, name, path, exe):
        self.name = name
        self.path = path
        self.exe = exe

class GameLauncher(threading.Thread):
    STATE_INITIALIZING = 'STATE_INITIALIZING'
    STATE_RUNNING = 'STATE_RUNNING'
    STATE_TERMINATED = 'STATE_TERMINATED'
    STATE_ERROR = 'STATE_ERROR'

    def __init__(self, game, *args, **kwargs):
        super(GameLauncher, self).__init__(*args, **kwargs)
        self.game = game
        self.env = None
        self.popen = None
        self.state = self.STATE_INITIALIZING

        if not os.path.isdir(self.game['path']):
            raise RuntimeError('Unexistent path %s (game: %s)' % (
                    self.game['path'], self.game))
        elif not os.path.isfile(os.path.join(self.game['path'], self.game['exe'])):
            raise RuntimeError('Exe %s not found (game: %s)' % (
                    os.path.join(self.game['path'], self.game['exe']), self.game))

    def run(self):
        try:
            self.popen = subprocess.Popen(
                    os.path.join(self.game['path'], self.game['exe']),
                    bufsize= -1,
                    cwd=self.game['path'],
                    shell=False,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    env=self.env,
                    close_fds=False)
        except Exception, e:
            self.state = self.STATE_ERROR
            logging.error('Cannot start game %s: %s' % (self.game['shortname'], e))
            return

        self.popen.stdin.close()
        self.popen.stdout.close()
        self.state = self.STATE_RUNNING

        while self.popen.poll() is None:
            try:
                ln = self.popen.stderr.readline().strip()
            except Exception, e:
                logging.info('Game launcher %s ended' % self.game['shortname'])
                break
            else:
                if ln:
                    print 'STDERR:', ln

        self.state = self.STATE_TERMINATED

    def terminate(self):
        handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, self.popen.pid)
        win32api.TerminateProcess(handle, 0)
        win32api.CloseHandle(handle)


class U0Interface(object):
    def __init__(self, port, cbStateChanged):
        self.__serialObj = serial.Serial(port, timeout=0)
        self.__oldStates = [False] * 5
        self.__cbStateChanged = cbStateChanged

        libavg.player.setOnFrameHandler(self.__poll)

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
                self.__notify(mask)

    def __notify(self, mask):
        states = []

        for i in xrange(6):
            if mask & (1 << i):
                thisState = True
            else:
                thisState = False

            states.append(thisState)

        self.__onStatesUpdate(states)

    def __onStatesUpdate(self, states):
        changed = [s1 != s2 for s1, s2 in zip(states, self.__oldStates)]

        for i in xrange(5):
            if changed[i]:
                self.__cbStateChanged(i, states[i])

        self.__oldStates = states


class U0KeyTranslator(object):
    def stateToKey(self, index, state):
        vkey = 0x31 + index
        scan = ctypes.windll.user32.MapVirtualKeyA(vkey + index, 0)

        eventf = 0 if state else 2

        ctypes.windll.user32.keybd_event(vkey, scan, eventf, 0)

        logging.debug('Sent key 0x%x, eventf=%d' % (vkey, eventf))


class MyConfigParser(ConfigParser.ConfigParser):
    def getDefaulted(self, section, option, default):
        if self.has_option(section, option):
            return self.get(section, option)
        else:
            return default


class GamesRegistry(object):
    GAMES_SUBDIR = 'games'
    DEFAULT_KEYSDELAY = 5

    def __init__(self, gamesConfig='games.ini'):
        config = MyConfigParser()
        config.read(gamesConfig)

        basePath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                self.GAMES_SUBDIR)

        self.__games = []
        for section in config.sections():
            if config.getboolean(section, 'active'):
                game = dict()

                game['shortname'] = section
                game['path'] = os.path.join(basePath, config.get(section, 'path'))
                game['exe'] = config.get(section, 'exe')
                game['name'] = config.getDefaulted(section, 'name', None)
                game['author'] = config.getDefaulted(section, 'author', None)
                game['description'] = config.getDefaulted(section, 'description', None)
                game['keysdelay'] = config.getDefaulted(section, 'keysdelay',
                        self.DEFAULT_KEYSDELAY)

                logging.debug('Configuring game %s' % section)
                self.__games.append(game)

        self.__gamePtr = 0

    def getNextGame(self):
        self.__gamePtr += 1

        if self.__gamePtr == len(self.__games):
            self.__gamePtr = 0

        return self.__games[self.__gamePtr]

    def getPrevGame(self):
        self.__gamePtr -= 1

        if self.__gamePtr == -1:
            self.__gamePtr = len(self.__games) - 1

        return self.__games[self.__gamePtr]

class SGCText(libavg.avg.WordsNode):
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


class LauncherApp(libavg.AVGApp):
    def init(self):
        libavg.avg.ImageNode(href='media/background.png', parent=self._parentNode)

        BlueText(text='NOW PLAYING',
                fontsize=78,
                pos=(710, 207),
                parent=self._parentNode)

        YellowText(text='THE NAME OF THE GAME',
                fontsize=107,
                pos=(710, 273),
                parent=self._parentNode)

        BlueText(text='AUTHOR',
                fontsize=60,
                pos=(710, 434),
                parent=self._parentNode)

        BlueText(text='PLAYERS',
                fontsize=60,
                pos=(1298, 434),
                parent=self._parentNode)

        BlueText(text='DESCRIPTION',
                fontsize=60,
                pos=(710, 674),
                parent=self._parentNode)

        YellowText(text='THE NAME OF THE AUTHOR/S',
                fontsize=60,
                pos=(710, 500),
                size=(536, 186),
                parent=self._parentNode)

        YellowText(text='Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent adipiscing sem sed turpis gravida id rutrum mi ullamcorper. Nulla ac rhoncus nisi. In et ligula non mi interdum pharetra.'.upper(),
                fontsize=48,
                pos=(710, 747),
                size=(1160, 306),
                parent=self._parentNode)

        YellowText(text='2 TO 5',
                fontsize=108,
                pos=(1298, 487),
                parent=self._parentNode)

        self.logLines = []
        self.log = libavg.avg.WordsNode(pos=(100, 100), parent=self._parentNode)
        self.addLogLine('Idling')
        self.propagateKeys = False

        self.gamesRegistry = GamesRegistry()

        self.proc = None

        self.propagateKeys = False
        self.u0Interface = U0Interface('COM3', self.__onU0StateChanged)
        self.u0KeyTranslator = U0KeyTranslator()

        self.__saveAvgWindowHandle()

        libavg.player.setOnFrameHandler(self.__poll)

    def onKeyDown(self, event):
        if event.keystring == 'b':
            # This is kinda relevant. Some games won't start if another
            # fullscreen app is stealing the context
            win32gui.ShowWindow(self.avgWindowHandle, win32con.SW_FORCEMINIMIZE)

            game = self.gamesRegistry.getNextGame()
            self.addLogLine('Starting %s' % game['name'])
            self.proc = GameLauncher(game)

            self.proc.start()
            libavg.player.setTimeout(game['keysdelay'] * 1000,
                    self.startKeyFlow)

    def addLogLine(self, line):
        self.logLines.append(line)
        if len(self.logLines) > 30:
            self.logLines = self.logLines[1:]

        self.log.text = '<br/>'.join(self.logLines)
        logging.info(line)

    def startKeyFlow(self):
        self.propagateKeys = True

    def terminateApp(self):
        self.__setFocusBack()

        if self.proc is not None:
            self.addLogLine('Terminating %s' % self.proc.game['name'])
            self.proc.terminate()
            self.proc = None

    def __poll(self):
        if self.proc and self.proc.state in (self.proc.STATE_TERMINATED, self.proc.STATE_ERROR):
            self.__setFocusBack()
            self.addLogLine('%s crashed or exited' % self.proc.game['name'])
            self.proc = None

    def __setFocusBack(self):
        self.propagateKeys = False

#        win32gui.SetForegroundWindow(avgwin[0])
        win32gui.ShowWindow(self.avgWindowHandle, win32con.SW_MAXIMIZE)

    def __saveAvgWindowHandle(self):
        toplist = []
        winlist = []
        def enum_callback(hwnd, results):
            winlist.append((hwnd, win32gui.GetWindowText(hwnd)))

        win32gui.EnumWindows(enum_callback, toplist)
        windows = [(hwnd, title) for hwnd, title in winlist if 'avg' in title.lower()]
        # just grab the first window that matches
        self.avgWindowHandle = windows[0][0]

    def __onU0StateChanged(self, index, state):
        if self.propagateKeys:
            self.u0KeyTranslator.stateToKey(index, state)


if __name__ == '__main__':
    import os

    os.environ['AVG_DEPLOY'] = '1'
    LauncherApp.start(resolution=(1920, 1080))
