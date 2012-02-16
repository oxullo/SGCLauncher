#!/usr/bin/env python
# -*- coding: utf-8 -*-

# engine module: generic game engine based on libavg, AVGApp
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
import math
import pickle
import random
import atexit
import libavg
from libavg import avg, Point2D

g_Player = avg.Player.get()
g_Log = avg.Logger.get()


class NotImplementedError(Exception):
    '''Method is not overloaded on child class'''

class EngineError(Exception):
    '''Generic engine error'''


class SoundManager(object):
    objects = {}

    @classmethod
    def init(cls, parent):
        cls.parent = parent

    @classmethod
    def getSample(cls, fileName, loop=False):
        return avg.SoundNode(href=os.path.join('snd', fileName), loop=loop,
                parent=cls.parent)

    @classmethod
    def allocate(cls, fileName, nodes=1):
        if fileName in cls.objects:
            raise RuntimeError('Sound sample %s has been already allocated' % fileName)

        slst = []
        for i in xrange(0, nodes):
            s = SoundManager.getSample(fileName)
            slst.append(s)

        cls.objects[fileName] = slst

    @classmethod
    def play(cls, fileName, randomVolume=False, volume=None):
        if not fileName in cls.objects:
            raise RuntimeError('Sound sample %s hasn\'t been allocated' % fileName)

        mySound = cls.objects[fileName].pop(0)
        mySound.stop()

        if volume is not None:
            maxVol = volume
        else:
            maxVol = 1

        if randomVolume:
            mySound.volume = random.uniform(0.2, maxVol)
        elif volume is not None:
            mySound.volume = volume

        sc = mySound.play()

        cls.objects[fileName].append(mySound)


class PeriodicTimerBase(object):
    def __init__(self):
        self.instances.append(self)

    def kill(self):
        self.instances.remove(self)


class PeriodicTimerSpecs(PeriodicTimerBase):
    instances = []

    def __init__(self, interval, callback):
        self.interval = interval
        self.callback = callback
        self.timerId = None
        super(PeriodicTimerSpecs, self).__init__()

    def start(self):
        assert self.timerId is None
        self.timerId = g_Player.setInterval(self.interval, self.callback)

    def kill(self):
        assert self.timerId is not None
        super(PeriodicTimerSpecs, self).kill()
        self.stop()

    def stop(self):
        assert self.timerId is not None
        g_Player.clearInterval(self.timerId)
        self.timerId = None


class OneShotTimerSpecs(PeriodicTimerBase):
    instances = []

    def __init__(self, delay, callback):
        self.delay = delay
        self.callback = callback
        self.elapsed = False
        self.timerId = g_Player.setTimeout(self.delay, self.__onTimerElapsed)
        super(OneShotTimerSpecs, self).__init__()

    def __onTimerElapsed(self):
        self.elapsed = True
        self.callback()

    def kill(self):
        assert self.timerId is not None
        super(OneShotTimerSpecs, self).kill()
        if not self.elapsed:
            g_Player.clearInterval(self.timerId)


class GameState(avg.DivNode):
    def __init__(self, *args, **kwargs):
        super(GameState, self).__init__(*args, **kwargs)
        self._isFrozen = False
        self._bgTrack = None
        self._maxBgTrackVolume = 1
        self.opacity = 0
        self.sensitive = False

    def init(self, app):
        self.app = app
        self._init()

    def registerBgTrack(self, fileName, maxVolume=1):
        self._bgTrack = SoundManager.getSample(fileName, loop=True)
        self._bgTrack.volume = maxVolume
        self._maxBgTrackVolume = maxVolume

    def registerPeriodicTimer(self, period, callback):
        return PeriodicTimerSpecs(period, callback)

    def registerOneShotTimer(self, delay, callback):
        return OneShotTimerSpecs(delay, callback)

    def update(self, dt):
        self._update(dt)

    def onTouch(self, event):
        if not self._isFrozen:
            self._onTouch(event)

    def onKeyDown(self, event):
        if not self._isFrozen:
            return self._onKeyDown(event)

    def onKeyUp(self, event):
        if not self._isFrozen:
            return self._onKeyUp(event)

    def enter(self):
        self.opacity = 1
        self._enter()
        self.sensitive = True
        if self._bgTrack:
            self._bgTrack.play()
        self._startTimers()

    def leave(self):
        self.sensitive = False
        self._leave()
        self.opacity = 0
        if self._bgTrack:
            self._bgTrack.stop()
        self._stopTimers()

    def _init(self):
        pass

    def _enter(self):
        pass

    def _leave(self):
        pass

    def _pause(self):
        pass

    def _resume(self):
        pass

    def _update(self, dt):
        pass

    def _onTouch(self, event):
        pass

    def _onKeyDown(self, event):
        pass

    def _onKeyUp(self, event):
        pass

    def _startTimers(self):
        for timer in PeriodicTimerSpecs.instances:
            timer.start()

    def _stopTimers(self):
        for ptimer in PeriodicTimerSpecs.instances:
            ptimer.stop()

        for ottimer in OneShotTimerSpecs.instances:
            ottimer.kill()


# Abstract
class TransitionGameState(GameState):
    TRANS_DURATION = 300
    def enter(self):
        self._isFrozen = True
        self._preTransIn()
        self._doTransIn(self.__postTransIn)
        if self._bgTrack:
            self._doBgTrackTransIn()
        self._startTimers()

    def leave(self):
        self.sensitive = False
        self._isFrozen = True
        self._preTransOut()
        self._doTransOut(self.__postTransOut)
        if self._bgTrack:
            self._doBgTrackTransOut()
        self._stopTimers()

    def _doTransIn(self, postCb):
        raise NotImplementedError()

    def _doTransOut(self, postCb):
        raise NotImplementedError()

    def _doBgTrackTransIn(self):
        self._bgTrack.play()

    def _doBgTrackTransOut(self):
        self._bgTrack.stop()

    def _preTransIn(self):
        pass

    def _postTransIn(self):
        pass

    def _preTransOut(self):
        pass

    def _postTransOut(self):
        pass

    def __postTransIn(self):
        self._isFrozen = False
        self._postTransIn()
        self.sensitive = True

    def __postTransOut(self):
        self._isFrozen = False
        self._postTransOut()


class FadeGameState(TransitionGameState):
    def _doTransIn(self, postCb):
        avg.fadeIn(self, self.TRANS_DURATION, 1, postCb)

    def _doTransOut(self, postCb):
        avg.fadeOut(self, self.TRANS_DURATION, postCb)

    def _doBgTrackTransIn(self):
        self._bgTrack.volume = 0
        self._bgTrack.play()
        avg.LinearAnim(self._bgTrack, 'volume', self.TRANS_DURATION, 0,
                self._maxBgTrackVolume).start()

    def _doBgTrackTransOut(self):
        avg.LinearAnim(self._bgTrack, 'volume', self.TRANS_DURATION,
                self._maxBgTrackVolume, 0, False, None,
                self._bgTrack.stop).start()


class ApplicationStarter(libavg.AVGAppStarter):
    def __init__(self, appClass, resolution, fullscreen=True):
        self._AppClass = appClass
        resolution = Point2D(resolution)

        width = int(resolution.x)
        height = int(resolution.y)

        # dynamic avg creation in order to set resolution
        libavg.player.loadString("""
<?xml version="1.0"?>
<!DOCTYPE avg SYSTEM "../../libavg/doc/avg.dtd">
<avg width="%(width)u" height="%(height)u">
</avg>""" % {
            'width': width,
            'height': height,
            })
        rootNode = libavg.player.getRootNode()

        self._appNode = libavg.player.createNode('div', {
            'opacity': 0,
            'sensitive': False})
        # the app should know the size of its "root" node:
        self._appNode.size = rootNode.size
        rootNode.appendChild(self._appNode)

        libavg.player.showCursor(False)

        screenResolution = libavg.player.getScreenResolution()

        libavg.player.setResolution(
                fullscreen,
                int(screenResolution.x), int(screenResolution.y),
                0 # color depth
                )

        rootNode.setEventHandler(avg.KEYDOWN, avg.NONE, self.__onKeyDown)
        rootNode.setEventHandler(avg.KEYUP, avg.NONE, self.__onKeyUp)

        self._onBeforePlay()
        libavg.player.setTimeout(0, self._onStart)
        self._appInstance = self._AppClass(self._appNode)
        self._appInstance.setStarter(self)
        libavg.player.play()
        self._appInstance.exit()

    def __onKeyDown(self, event):
        return self._activeApp.onKeyDown(event)

    def __onKeyUp(self, event):
        return self._activeApp.onKeyUp(event)


class Application(libavg.AVGApp):
    def __init__(self, *args, **kwargs):
        self.__registeredStates = {}
        self.__currentState = None
        self.__tickTimer = None
        self.__entryHandle = None
        self.__elapsedTime = 0
        self.__pointer = None
        super(Application, self).__init__(*args, **kwargs)

        pkgpath = self._getPackagePath()
        if pkgpath is not None:
            avg.WordsNode.addFontDir(libavg.AVGAppUtil.getMediaDir(pkgpath, 'fonts'))
            self._parentNode.mediadir = libavg.AVGAppUtil.getMediaDir(pkgpath)


    def setupPointer(self, instance):
        self._parentNode.appendChild(instance)
        instance.sensitive = False
        self.__pointer = instance
        g_Player.showCursor(False)

    @property
    def size(self):
        return g_Player.getRootNode().size

    def registerState(self, handle, state):
        g_Log.trace(g_Log.APP, 'Registering state %s: %s' % (handle, state))
        self._parentNode.appendChild(state)
        state.init(self)
        self.__registeredStates[handle] = state

    def bootstrap(self, handle):
        if self.__currentState:
            raise EngineError('The game has been already bootstrapped')

        self.__entryHandle = handle

    def changeState(self, handle):
        if self.__entryHandle is None:
            raise EngineError('Game must be bootstrapped before changing its state')

        newState = self.__getState(handle)

        if self.__currentState:
            self.__currentState.leave()

        newState.enter()
        g_Log.trace(g_Log.APP, 'Changing state %s -> %s' % (self.__currentState,
                newState))

        self.__currentState = newState

    def getState(self, handle):
        return self.__getState(handle)

    def onKeyDown(self, event):
        if self.__currentState:
            return self.__currentState.onKeyDown(event)

    def onKeyUp(self, event):
        if self.__currentState:
            return self.__currentState.onKeyUp(event)

    def onTouch(self, event):
        if self.__currentState:
            self.__currentState.onTouch(event)

        if event.source == avg.TOUCH and self.__pointer:
            self.__pointer.opacity = 0

    def onMouseMotion(self, event):
        if self.__pointer:
            self.__pointer.opacity = 1
            self.__pointer.pos = event.pos - self.__pointer.size / 2
            self.__pointer.refresh()

    def _enter(self):
        self._parentNode.setEventHandler(avg.CURSORDOWN, avg.MOUSE | avg.TOUCH,
                self.onTouch)
        self._parentNode.setEventHandler(avg.CURSORMOTION, avg.MOUSE,
                self.onMouseMotion)

        self.__tickTimer = g_Player.setOnFrameHandler(self.__onFrame)

        if self.__currentState:
            self.__currentState._resume()
        else:
            self.changeState(self.__entryHandle)

    def _leave(self):
        self._parentNode.setEventHandler(avg.CURSORDOWN,
                avg.MOUSE | avg.TOUCH, None)
        self._parentNode.setEventHandler(avg.CURSORMOTION,
                avg.MOUSE, None)
        g_Player.clearInterval(self.__tickTimer)
        self.__tickTimer = None

        if self.__currentState:
            self.__currentState.leave()
            self.__currentState = None

    def _getPackagePath(self):
        return __file__

    def __getState(self, handle):
        if handle in self.__registeredStates:
            return self.__registeredStates[handle]
        else:
             raise EngineError('No state with handle %s' % handle)

    def __onFrame(self):
        if self.__currentState:
            dt = g_Player.getFrameTime() - self.__elapsedTime
            self.__currentState.update(dt)

        self.__elapsedTime = g_Player.getFrameTime()
