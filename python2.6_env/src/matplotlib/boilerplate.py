# Wrap the plot commands defined in axes.  The code generated by this
# file is pasted into pyplot.py.  We did try to do this the smart way,
# with callable functions and new.function, but could never get the
# docstrings right for python2.2.  See
# http://groups.google.com/group/comp.lang.python/browse_frm/thread/dcd63ec13096a0f6/1b14640f3a4ad3dc?#1b14640f3a4ad3dc
# For some later history, see
# http://thread.gmane.org/gmane.comp.python.matplotlib.devel/7068

import inspect
import random
import re
import sys
import types

# import the local copy of matplotlib, not the installed one
#sys.path.insert(0, './lib')
from matplotlib.axes import Axes
from matplotlib.cbook import dedent

_fmtplot = """\
# This function was autogenerated by boilerplate.py.  Do not edit as
# changes will be lost
@autogen_docstring(Axes.%(func)s)
def %(func)s(%(argspec)s):
    %(ax)s = gca()
    # allow callers to override the hold state by passing hold=True|False
    %(washold)s = %(ax)s.ishold()
    %(sethold)s
    if hold is not None:
        %(ax)s.hold(hold)
    try:
        %(ret)s = %(ax)s.%(func)s(%(call)s)
        draw_if_interactive()
    finally:
        %(ax)s.hold(%(washold)s)
    %(mappable)s
    return %(ret)s
"""

_fmtmisc = """\
# This function was autogenerated by boilerplate.py.  Do not edit as
# changes will be lost
@docstring.copy_dedent(Axes.%(func)s)
def %(func)s(%(argspec)s):
    %(ret)s =  gca().%(func)s(%(call)s)
    draw_if_interactive()
    return %(ret)s
"""

# these methods are all simple wrappers of Axes methods by the same
# name.
_plotcommands = (
    'acorr',
    'arrow',
    'axhline',
    'axhspan',
    'axvline',
    'axvspan',
    'bar',
    'barh',
    'broken_barh',
    'boxplot',
    'cohere',
    'clabel',
    'contour',
    'contourf',
    'csd',
    'errorbar',
    'fill',
    'fill_between',
    'fill_betweenx',
    'hexbin',
    'hist',
    'hlines',
    'imshow',
    'loglog',
    'pcolor',
    'pcolormesh',
    'pie',
    'plot',
    'plot_date',
    'psd',
    'quiver',
    'quiverkey',
    'scatter',
    'semilogx',
    'semilogy',
    'specgram',
    #'spy',
    'stem',
    'step',
    'vlines',
    'xcorr',
    'barbs',
    )

_misccommands = (
    'cla',
    'grid',
    'legend',
    'table',
    'text',
    'annotate',
    )

cmappable = {
    'contour' : 'if %(ret)s._A is not None: sci(%(ret)s)',
    'contourf': 'if %(ret)s._A is not None: sci(%(ret)s)',
    'hexbin' :  'sci(%(ret)s)',
    'scatter' : 'sci(%(ret)s)',
    'pcolor'  : 'sci(%(ret)s)',
    'pcolormesh': 'sci(%(ret)s)',
    'imshow'  : 'sci(%(ret)s)',
    #'spy'    :  'sci(%(ret)s)',  ### may return image or Line2D
    'quiver' :  'sci(%(ret)s)',
    'specgram'  : 'sci(%(ret)s[-1])',

}

def format_value(value):
    """
    Format function default values as needed for inspect.formatargspec.
    The interesting part is a hard-coded list of functions used
    as defaults in pyplot methods.
    """
    if isinstance(value, types.FunctionType):
        if value.func_name in ('detrend_none', 'window_hanning'):
            return '=mlab.' + value.func_name
        if value.func_name == 'mean':
            return '=np.' + value.func_name
        raise ValueError, ('default value %s unknown to boilerplate.formatvalue'
                           % value)
    return '='+repr(value)

def remove_final_whitespace(string):
    """
    Return a copy of *string* with final whitespace removed from each line.
    """
    return '\n'.join(x.rstrip() for x in string.split('\n'))

for fmt,cmdlist in (_fmtplot,_plotcommands),(_fmtmisc,_misccommands):
    for func in cmdlist:
        # For some commands, an additional line is needed to set the
        # color map
        if func in cmappable:
            mappable = cmappable[func] % locals()
        else:
            mappable = ''

        # Get argspec of wrapped function
        args, varargs, varkw, defaults = inspect.getargspec(getattr(Axes, func))
        args.pop(0) # remove 'self' argument
        if defaults is None:
            defaults = ()

        # How to call the wrapped function
        call = map(str, args)
        if varargs is not None:
            call.append('*'+varargs)
        if varkw is not None:
            call.append('**'+varkw)
        call = ', '.join(call)

        # Add a hold keyword argument if needed (fmt is _fmtplot) and
        # possible (if *args is used, we can't just add a hold
        # argument in front of it since it would gobble one of the
        # arguments the user means to pass via *args)
        if varargs:
            sethold = "hold = %(varkw)s.pop('hold', None)" % locals()
        elif fmt is _fmtplot:
            args.append('hold')
            defaults = defaults + (None,)
            sethold = ''

        # Now we can build the argspec for defining the wrapper
        argspec = inspect.formatargspec(args, varargs, varkw, defaults,
                                        formatvalue=format_value)
        argspec = argspec[1:-1] # remove parens

        # A gensym-like facility in case some function takes an
        # argument named washold, ax, or ret
        washold,ret,ax = 'washold', 'ret', 'ax'
        bad = set(args) | set((varargs, varkw))
        while washold in bad or ret in bad or ax in bad:
            washold = 'washold' + str(random.randrange(10**12))
            ret = 'ret' + str(random.randrange(10**12))
            ax = 'ax' + str(random.randrange(10**12))

        # Since we can't avoid using some function names,
        # bail out if they are used as argument names
        for reserved in ('gca', 'gci', 'draw_if_interactive'):
            if reserved in bad:
                raise ValueError, \
                    'Axes method %s has kwarg named %s' % (func, reserved)

        print remove_final_whitespace(fmt%locals())

# define the colormap functions
_fmtcmap = """\
# This function was autogenerated by boilerplate.py.  Do not edit as
# changes will be lost
def %(name)s():
    '''
    set the default colormap to %(name)s and apply to current image if any.
    See help(colormaps) for more information
    '''
    rc('image', cmap='%(name)s')
    im = gci()

    if im is not None:
        im.set_cmap(cm.%(name)s)
    draw_if_interactive()

"""

cmaps = (
    'autumn',
    'bone',
    'cool',
    'copper',
    'flag',
    'gray' ,
    'hot',
    'hsv',
    'jet' ,
    'pink',
    'prism',
    'spring',
    'summer',
    'winter',
    'spectral'
)
# add all the colormaps (autumn, hsv, ....)
for name in cmaps:
    print _fmtcmap%locals()
