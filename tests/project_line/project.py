#!/usr/bin/env python

from pylab import *

def project_point_onto_line(p, o, m):
    """
    Project a point onto a line defined by:
    <xy...> = o + t * m
    
    Returns: (pp, t)
        pp = the resulting projected point located on the line
        t = the location of the projected point on the line (relative to the origin)
    """
    t = dot(m, p - o) / dot(m,m)
    pp = o + t*m
    return pp, t

def reassign_origin(o, m, p, t):
    """
    Reassign the origin of a line defined by:
    <xy...> = o + t * m
    by providing:
        -a point (p, that will be projected onto the line)
        -the desired t (location on the line of the projected point)
    
    Returns: (newO, m)
        newO = new origin
        m = slope (unchanged)
    """
    pp, ppt = project_point_onto_line(p, o, m)
    dt = ppt - t
    newO = o + dt * m
    return newO, m

def test_2d():
    # =============== 2d ==============
    
    # line = o + tm
    m = array([2,1]); m = m / norm(m)
    o = array([1,1])
    p = array([1.5, 3.2])
    
    # draw line
    p0 = o + -5 * m
    p1 = o +  5 * m
    plot([p0[0],p1[0]], [p0[1],p1[1]], c='b')
    
    # draw point to project
    scatter(*p, c='b')
    
    # draw projected point
    pp, t = project_point_onto_line(p, o, m)
    # t = dot(m, p - o) / dot(m,m)
    # pp = o + t*m
    scatter(*pp, c='r')
    
    # check that p-p' and m are perpendicular
    print dot(p-pp, m) < 0e-16
    
    gca().set_aspect(1.)
    xlim([0,4])
    ylim([0,4])

def test_3d():
    # ================ 3d ==============
    
    from mpl_toolkits.mplot3d import Axes3D
    ax = Axes3D(gcf())
    
    m = array([4,2,1]); m = m / norm(m)
    o = array([1,1,1])
    p = array([1.5, 3.2, 4.5])
    
    # draw line
    p0 = o + -10 * m
    p1 = o +  10 * m
    ax.plot([p0[0],p1[0]],[p0[1],p1[1]],[p0[2],p1[2]], c='b')
    
    # draw point to project
    ax.scatter([p[0]],[p[1]],[p[2]], c='b')
    
    # draw projected point
    pp, t = project_point_onto_line(p, o, m)
    # t = dot(m, p - o) / dot(m,m)
    # pp = o + t*m
    ax.scatter([pp[0]],[pp[1]],[pp[2]], c='r')
    
    # check that p-p' and m are perpendicular
    print dot(p-pp, m) < 0e-16
    
    ax.set_aspect(1.)
    ax.set_xlim3d([0,4])
    ax.set_ylim3d([0,4])
    ax.set_zlim3d([0,4])

def test_reassign_origin():
    m = array([2,1]); m = m / norm(m)
    o = array([1,1])
    t = 2.0
    p = o + t * m
    newT = 1.0
    
    # draw line
    p0 = o + -5 * m
    p1 = o +  5 * m
    plot([p0[0],p1[0]], [p0[1],p1[1]], c='b')
    
    # draw point
    scatter(*p, c='b', s=50)
    
    newO, m = reassign_origin(o, m , p, newT)
    print o
    print newO
    o = newO
    
    # draw line
    p0 = o + -5 * m
    p1 = o +  5 * m
    plot([p0[0],p1[0]], [p0[1],p1[1]], c='g')
    
    # draw point
    newP = o + newT * m
    scatter(*newP, c='g', s=50)
    
    gca().set_aspect(1.)
    xlim([0,4])
    ylim([0,4])

if __name__ == '__main__':
    # figure()
    # test_2d()
    
    figure()
    test_reassign_origin()
    
    # figure()
    # test_3d()
    show()