#!/usr/bin/env python


def open(cfg, section):
    ctype = cfg.get(section, 'type')
    if ctype == 'dc1394':
        pass
    else:
        raise ValueError("Unknown camera type: %s" % ctype)
