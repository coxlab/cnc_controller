#!/usr/bin/env python

import logging

import zmq

from zmqobject import ZMQClient

# ===============================

# address = "tcp://127.0.0.1:7200"
address = "ipc:///tmp/cnc"
commands = [[ 'linearAxes.get_position', ['y'],{} ],
            [ 'linearAxes.move_relative', [-19.0,'y'], {} ],
            [ 'linearAxes.get_position', ['y'],{} ]]

axes = ['x','y','z','w','b']
context = zmq.Context()

# ===============================

cncClient = ZMQClient('/'.join((address, 'cmd')), context)

pos_socket = context.socket(zmq.SUB)
pos_socket.connect('/'.join((address, 'pos')))
pos_socket.setsockopt(zmq.SUBSCRIBE,"")

# pos_sockets = {}
# for a in axes:
#     pos_sockets[a] = context.socket(zmq.SUB)
#     addr = '/'.join((address, a))
#     print "Making subscriber for:", addr
#     pos_sockets[a].connect(addr)
#     pos_sockets[a].setsockopt(zmq.SUBSCRIBE,"") # neede for subscribe

for cmd, args, kwargs in commands:
    print "Calling: %s, %s, %s" % (cmd, args, kwargs)
    print cncClient.call(cmd, *args, **kwargs)
    
    pos = pos_socket.recv_pyobj()
    print pos
    
    # # update position sockets
    # for a, p in pos_sockets.iteritems():
    #     try:
    #         r = p.recv(zmq.NOBLOCK)
    #         print a, r
    #     except zmq.ZMQError as e:
    #         print "nothing recieved", e