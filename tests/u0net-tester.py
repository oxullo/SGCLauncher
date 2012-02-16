#!/usr/bin/python
# -*- coding: utf-8 -*-


import re
import sys
import random
from twisted.internet import protocol, reactor
from twisted.protocols import basic
from twisted.python import log


class U0NetProto(basic.LineReceiver):
    delimiter='\r\n'

    def connectionMade(self):
        log.msg('Connection made')
        self.factory.protos.append(self)

    def clientConnectionLost(self, connector, reason):
        self.factory.protos.remove(self)
    

class U0Net(protocol.ServerFactory):
    protocol = U0NetProto
    protos = []

    def __init__(self):
        self.__cascade()
        
    def sendShit(self):
        if self.protos:
            mask = random.randrange(0, 32)
            lmask = []
            for i in xrange(5):
                lmask.append('I' if mask & 1 << i else 'X')
            
            log.msg('Sending %s (%d)' % (str(lmask), mask))
            for proto in self.protos:
                proto.sendLine('%d' % mask)
            
        self.__cascade()
    
    def __cascade(self):
        reactor.callLater(random.uniform(0.01, 1.5), self.sendShit)


if __name__=='__main__':
    log.startLogging(sys.stdout)
    reactor.listenTCP(10000, U0Net())
    
    reactor.run()
