#!/usr/bin/env python

import time

import zmq

from cnc.cnc import FiveAxisCNC
from zmqobject import ZMQObject
from cnc_cfg import cfgDict

# address = "tcp://127.0.0.1:7200"
address = "ipc:///tmp/cnc"
update_period = 0.1

class ZMQCNC(FiveAxisCNC, ZMQObject):
    def zmq_setup(self, address, context=None):
        if context is None:
            context = zmq.Context()
        ZMQObject.zmq_setup(self, '/'.join((address,'cmd')), context) # setup command socket
        
        # setup position publishers
        self.pos_socket = context.socket(zmq.PUB)
        self.pos_socket.bind('/'.join((address, 'pos')))
        # self.pos_sockets = {}
        # for a in ['x','y','z','b','w']:
        #     self.pos_sockets[a] = context.socket(zmq.PUB)
        #     print '/'.join((address, a))
        #     self.pos_sockets[a].bind('/'.join((address, a)))
        
    def update_positions(self):
        # get current positions from cnc
        pos = self.headAxes.get_position()
        pos.update(self.linearAxes.get_position())
        
        self.pos_socket.send_pyobj(pos)
        
        # # publish new data on zeromq sockets
        # for axis, socket in self.pos_sockets.iteritems():
        #     # print "sending", pos[axis]
        #     r = socket.send(str(pos[axis]))


zmqCnc = ZMQCNC(cfgDict)
zmqCnc.zmq_setup(address)
while True:
    zmqCnc.zmq_update(blocking=False)
    zmqCnc.update_positions()
    time.sleep(update_period)