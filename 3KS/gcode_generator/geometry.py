#!/usr/bin/env python

import sys
import numpy
import itertools

def normalize(aVector):
    oNorm = aVector * numpy.sign(aVector[0])
    oNorm = oNorm / numpy.linalg.norm(oNorm)
    return oNorm

def isParallel(aLine1, aLine2):
    fEpsilon = 1e-5
    aVector1 = normalize(numpy.array([aLine1.a1, aLine1.a2]))
    aVector2 = normalize(numpy.array([aLine2.a1, aLine2.a2]))
    return True if (numpy.dot(aVector1, aVector2) > (1.0-fEpsilon)) else False

def isIter(o):
    return (type(o) is tuple) or (type(o) is numpy.ndarray)

class Line:
    def __init__(self, *nargs):
        if len(nargs) == 2 and isIter(nargs[0]) and isIter(nargs[1]):
            self.oPoint1, self.oPoint2 = nargs
            tDirection                 = tuple(map(lambda a,b: b-a, self.oPoint1, self.oPoint2))
            tNorm                      = (-tDirection[1], tDirection[0])
            nOffset                    = -(tuple(itertools.accumulate(map(lambda a,b: a*b, tNorm, self.oPoint1)))[-1])
            self.a1, self.a2           = tNorm
            self.a0                    = nOffset
        else:
            raise ValueError("Two points must be given to construct line.")

    def intersect(self, oSecondLine):
        oMat = numpy.array([[self.a1, self.a2], [oSecondLine.a1, oSecondLine.a2]])
        oVec = -numpy.array([self.a0,oSecondLine.a0])
        return numpy.linalg.solve(oMat, oVec)
    
    def shift(self, d):
        """Shifts the line by d units. The sign determines the sign of the x shift."""
        oNorm = normalize(numpy.array([self.a1, self.a2]))

        oNewPoint1 = self.oPoint1+d*oNorm
        oNewPoint2 = self.oPoint2+d*oNorm

        return Line(oNewPoint1, oNewPoint2)
    
    def __repr__(self):
        return "{:5.2f}x + {:5.2f}y + {:5.2f} = 0".format(self.a1, self.a2, self.a0)

def shiftCurve(ltiCurveUM, iDistanceUM):
    toLines = tuple( Line(*x).shift(iDistanceUM) for x in zip(ltiCurveUM,ltiCurveUM[1:]) )
    ltoCurvePoints = [ oLine[0].intersect(oLine[1]) for oLine in zip(toLines,toLines[1:]) if not isParallel(oLine[0], oLine[1]) ]
    aFirstPoint = ltiCurveUM[0] + iDistanceUM*normalize(numpy.array([toLines[0].a1, toLines[0].a2]))
    aLastPoint  = ltiCurveUM[-1] + iDistanceUM*normalize(numpy.array([toLines[-1].a1, toLines[-1].a2]))

    ltoCurvePoints.insert(0, aFirstPoint)
    ltoCurvePoints.append(aLastPoint)

    return ltoCurvePoints

if __name__ == "__main__":
    tt  = ( (1,2), (1,1), (0,0) )
    oLine1 = Line( (0,0), (1,1) )
    oLine2 = oLine1.shift(1)
