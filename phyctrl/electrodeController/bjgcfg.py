#!/usr/bin/env python

import sys, os

CfgModule = __name__

def assign_cfg_module(moduleName):
    global CfgModule
    CfgModule = moduleName

def load_external_cfg(cfgFile):
    """Load an external configuration file into this module
    The values found in the external module will overwrite any
    values defined here. New variables will be created when 
    needed.
    
    Example:
    
    test.py:
      import cfg.py
      <<point 1>>
      cfg.load_external_cfg('customCfg.py')
      <<point 2>>
    
    cfg.py:
      foo = '1'
    
    customCfg.py:
      foo = '2'
      bar = 'hi'
    
    will result in:
      cfg.foo <<at point 1>> = '1'
      cfg.bar <<at point 1>> does not exist
      cfg.foo <<at point 2>> = '2'
      cfg.bar <<at point 2>> = 'hi'
    """
    mod = sys.modules[CfgModule]
    
    # change to that directory so that 
    newDir = os.path.dirname(cfgFile)
    #print 'newDirectory:', newDir
    if newDir != '':
        oldDir = os.path.abspath(os.curdir)
        os.chdir(newDir)
    else:
        oldDir = '.'
    #oldDir = os.path.abspath(os.curdir)
    #print 'oldDirectory:', oldDir
    #print 'currentDirectory:', os.path.abspath(os.curdir)
    
    sys.path.append(os.path.dirname(cfgFile))
    
    moduleName = os.path.splitext(os.path.basename(cfgFile))[0]
    
    # if there is already a module that shares this name, remove it
    if sys.modules.has_key(moduleName):
        sys.modules.pop(moduleName)
    
    cfg = __import__(moduleName)
    for i in dir(cfg):
        if i[0] == '_':
            continue
        if type(i) == type(sys):
            continue
        mod.__setattr__(i,cfg.__getattribute__(i))
    
    # remove appended path
    sys.path.pop()
    
    # return to old directory
    os.chdir(oldDir)
    #print 'leaving, in directory:', os.path.abspath(os.curdir)

def print_cfg():
    mod = sys.modules[CfgModule]
    print dir(mod)

def process_options(options=sys.argv):
    """Parse a list of options (default=sys.argv) of the form:
    --variable=value
    assigning the new values to the variables within this module,
    creating variables where needed. Do NOT use spaces in the value
    
    Example:
     python test.py --foo='a' --bar=1 --junk='[1,2,3]'
    
    where test.py:
      import cfg.py
      cfg.process_options()
    
    will result in:
      cfg.foo = 'a' (type string)
      cfg.bar = 1 (type int)
      cfg.junk = [1,2,3] (type list)
    """
    #print options
    mod = sys.modules[CfgModule]
    for o in options[1:]:
        if o[:2] != '--':
            #print "option:%s invalid, no preceeding --" % o
            continue
        items = o.split('=')
        if len(items) != 2:
            #print "option:%s invalid, len=%i" % (o, len(items))
            continue
        arg = items[0][2:]
        val = items[1]
        #print "found arg:%s and val:%s" % (arg, val)
        #exec('%s = %s' % (arg, val), globals(), locals())
        exec('mod.%s = %s' % (arg, val))
