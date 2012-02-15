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
import logging
import config


class GamesRegistry(object):
    GAMES_SUBDIR = 'games'

    def __init__(self, gamesConfig='games.ini'):
        cfg = config.MyConfigParser()
        cfg.read(gamesConfig)

        basePath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                self.GAMES_SUBDIR)

        self.__games = []
        for section in cfg.sections():
            if cfg.getboolean(section, 'active'):
                game = dict()

                game['handle'] = section
                game['path'] = os.path.join(basePath, cfg.get(section, 'path'))
                game['exe'] = cfg.get(section, 'exe')
                game['name'] = cfg.getDefaulted(section, 'name', None)
                game['author'] = cfg.getDefaulted(section, 'author', None)
                game['description'] = cfg.getDefaulted(section, 'description', None)
                game['players'] = cfg.getDefaulted(section, 'players', None)
                game['keysdelay'] = cfg.getDefaulted(section, 'keysdelay', None)

                if game['keysdelay'] is not None:
                    game['keysdelay'] = int(game['keysdelay'])

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

    def getCurrentGame(self):
        return self.__games[self.__gamePtr]


games = GamesRegistry()

