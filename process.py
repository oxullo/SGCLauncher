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

import os
import subprocess
import threading
import logging

import ctypes
import win32api
import win32con
import win32gui
import win32process

LIBAVG_WINDOW_HANDLE = None


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


class Process(threading.Thread):
    STATE_INITIALIZING = 'STATE_INITIALIZING'
    STATE_RUNNING = 'STATE_RUNNING'
    STATE_TERMINATED = 'STATE_TERMINATED'
    STATE_CANTSTART = 'STATE_CANTSTART'
    STATE_BADEXIT = 'STATE_BADEXIT'

    def __init__(self, game, *args, **kwargs):
        super(Process, self).__init__(*args, **kwargs)
        self.game = game
        self.env = None
        self.__popen = None
        self.state = self.STATE_INITIALIZING

        if not os.path.isdir(self.game['path']):
            raise RuntimeError('Unexistent path %s (game: %s)' % (
                    self.game['path'], self.game))
        elif not os.path.isfile(os.path.join(self.game['path'], self.game['exe'])):
            raise RuntimeError('Exe %s not found (game: %s)' % (
                    os.path.join(self.game['path'], self.game['exe']), self.game))

    def run(self):
        try:
            self.__popen = subprocess.Popen(
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
            self.state = self.STATE_CANTSTART
            logging.error('Cannot start game %s: %s' % (self.game['shortname'], e))
            return

        self.__popen.stdin.close()
        self.__popen.stdout.close()
        self.state = self.STATE_RUNNING

        while self.__popen.poll() is None:
            try:
                ln = self.__popen.stderr.readline().strip()
            except Exception, e:
                logging.info('Game launcher %s ended' % self.game['shortname'])
                break
            else:
                if ln:
                    print 'STDERR:', ln

        if self.__popen.returncode == 0:
            self.state = self.STATE_TERMINATED
        else:
            self.state = self.STATE_BADEXIT

    def terminate(self):
        handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, self.__popen.pid)
        win32api.TerminateProcess(handle, 0)
        win32api.CloseHandle(handle)

    def hasFocus(self):
        if self.state != self.STATE_RUNNING:
            return False
        else:
            fgHwnd = win32gui.GetForegroundWindow()
            thrid, pid = win32process.GetWindowThreadProcessId(fgHwnd)
            return pid == self.__popen.pid

def getWindowsList():
    winlist = []
    def enum_callback(hwnd, ignore):
        winlist.append((hwnd, win32gui.GetWindowText(hwnd)))

    win32gui.EnumWindows(enum_callback, None)

    return winlist

def init():
    global LIBAVG_WINDOW_HANDLE

    winlist = getWindowsList()
    windows = [hwnd for hwnd, title in winlist if 'avg' in title.lower()]
    # just grab the first window that matches
    LIBAVG_WINDOW_HANDLE = windows[0]

def hideLauncherWindow():
    global LIBAVG_WINDOW_HANDLE
    assert LIBAVG_WINDOW_HANDLE is not None
    win32gui.ShowWindow(LIBAVG_WINDOW_HANDLE, win32con.SW_FORCEMINIMIZE)

def restoreLauncherWindow():
    global LIBAVG_WINDOW_HANDLE
    assert LIBAVG_WINDOW_HANDLE is not None
    win32gui.ShowWindow(LIBAVG_WINDOW_HANDLE, win32con.SW_MAXIMIZE)

def moveMouseOut():
    win32api.SetCursorPos((5000, 5000))
