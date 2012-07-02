#!/usr/bin/env python

import logging

import zmq


def process_error(code, cmd, args, kwargs):
    if code == -1:
        raise AttributeError("[%i]\t%s does not exist: %s, %s" % \
                (code, cmd, str(args), str(kwargs)))
    elif code == -2:
        raise Exception("[%i]\tUnknown error: %s, %s, %s" % \
                (code, cmd, str(args), str(kwargs)))
    elif code == -10:
        raise Exception("[%i]\tUnknown exception: %s, %s, %s" % \
                (code, cmd, str(args), str(kwargs)))
    else:
        raise Exception("[%i]\tUnknown code: %s, %s, %s" % \
                (code, cmd, str(args), str(kwargs)))


class ZMQClient:
    def __init__(self, address, context=None):
        if context is None:
            context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(address)

    def call(self, cmd, *args, **kwargs):
        self.socket.send_pyobj([cmd, args, kwargs])
        result = self.socket.recv_pyobj()
        if result[0] != 0:
            process_error(result[0], cmd, args, kwargs)
        return result[1]


def get_func(obj, cmd):
    """
    Recursing function for parsing a command involving a '.' operator.
    Example:
        obj = self
        cmd = foo.bar
            will get the sub-object foo from self and then recurse with...
        obj = self.foo
        cmd = bar
            will return the bar function from object self.foo
    """
    if '.' in cmd:
        return get_func(getattr(obj, cmd.split('.')[0]), cmd.partition('.')[2])
    else:
        return getattr(obj, cmd)


class ZMQObject:
    def zmq_setup(self, address, context=None):
        """
        Creates a zmq.REP socket (zmq_socket) that manages this object
        Client sockets should be of type zmq.REQ
        """
        if context is None:
            context = zmq.Context()

        self.zmq_socket = context.socket(zmq.REP)
        self.zmq_socket.bind(address)

    def zmq_update(self, blocking=True):
        """
        Receive a command from a client in the form of:
            ("command", *args, **kwargs)
        execute the command and return the results in the form:
            [errcode, *results]
        error codes:
            0   : a-ok
            -1  : command does not exist (AttributeError)
            -2  : unkown error
            -10 : unknown exception (Exception)
        """
        logging.debug("Receiving...")
        if blocking:
            flags = 0
        else:
            flags = zmq.NOBLOCK
        try:
            cmd, args, kwargs = self.zmq_socket.recv_pyobj(flags)
        except zmq.ZMQError as e:
            if blocking:
                raise e
            else:
                logging.debug("Nonblocking receive returned nothing")
                return
        logging.debug("Command: %s" % cmd)
        logging.debug("Args: %s" % str(args))
        logging.debug("Kwarg: %s" % str(kwargs))
        result = None
        err = -2
        try:
            result = get_func(self, cmd)(*args, **kwargs)
            err = 0
        except AttributeError as e:
            logging.warning("AttributeError: %s" % e)
            err = -1
        except Exception as e:
            logging.warning("Exception: %s" % e)
            logging.warning("\t%s" % cmd)
            logging.warning("\t%s" % str(args))
            logging.warning("\t%s" % str(kwargs))
            err = -10

        logging.debug("Result(%i): %s" % (err, str(result)))
        self.zmq_socket.send_pyobj((err, result))

if __name__ == '__main__':
    import time
    address = "tcp://127.0.0.1:7200"
    logging.basicConfig(level=logging.DEBUG)

    class Sub:
        def foo(self):
            return "sub foo"

    class Foo(ZMQObject):
        def __init__(self):
            self.sub = Sub()

        def foo(self):
            return "foo"

        def bar(self, *args):
            print "bar called with", args
            return args

        def baz(self, *args, **kwargs):
            print "baz called with", args
            return args[0]

    f = Foo()
    f.zmq_setup(address)
    print "Creating..."

    print "Looping..."
    while True:
        f.zmq_update(False)
        time.sleep(0.1)

