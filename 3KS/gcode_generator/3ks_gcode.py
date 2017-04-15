#!/usr/bin/env python3

m_iCodeDistanceUM   = 500
m_iCurveThicknessUM = 1200
m_iPinDistanceUM    = 3500
m_iPinLengthY       = 1000
m_iCodesDouble      = 7
m_iCodesSingle      = 9
m_iPositions        = 6
m_iCurveOffsetY_UM  = 35000
m_iSafetyZDistanceUM= 5000
m_iMillDiameterUM   = 1000
m_iEntryWidthX_UM   = 2750
m_iEntryWidthY_UM   = 3500
m_iTopExtraY_UM     = 1000
import sys
import argparse
from itertools import repeat
from geometry import shiftCurve

def getYValues(iYOffset=m_iCurveOffsetY_UM, iPinDistanceUM=m_iPinDistanceUM, iPoints=m_iPositions):
    li = list()
    iLocalOffset = -int(m_iPinLengthY/2)
    iYOffset += iLocalOffset
    iYOffset -= m_iTopExtraY_UM
    liRange = [ x for item in range(iPoints) for x in repeat(item, 2) ]
    for i in liRange:
        li.append(-i*iPinDistanceUM - iLocalOffset + iYOffset)
        iLocalOffset *= -1
    li[0]  += m_iTopExtraY_UM
    li[0]  -= m_iMillDiameterUM/2
    li[-1] -= m_iMillDiameterUM/2
    return li

def codeToDistance(liCode, iMax, iUM=m_iCodeDistanceUM):
    """Converts Evva3KS locking code into list of x values centered to the middle of the curve axis."""
    liCode = list(liCode)
    iMiddle = int((iMax+1)/2)
    liCode.append(iMiddle)
    return [ (i-iMiddle)*iUM for i in liCode ]

def millOffset(ltCoords, iMillRadiusUM, iCurveThicknessUM=m_iCurveThicknessUM):
    """Shifts the x values such that a curve of thickness iCurveThicknessUM is milled."""

def createDoubleCurveEntry(ltiCurveUM, iEntryFactor):
    """
    Creates the "entry" of the double courve.
    iEntryFactor must be -1 for the left curve and +1 for the right curve.
    """
    tLast = ltiCurveUM.pop()
    ltiCurveUM.append((iEntryFactor*m_iEntryWidthX_UM, tLast[1]-m_iEntryWidthY_UM))

def millCurve(ltiCurveUM, liDepthsUM, oGcode):
    """Mills a curve, including going to the start point."""
    oGcode.goto(None, None, m_iSafetyZDistanceUM)
    for iDepthUM in liDepthsUM:
      oGcode.goto(*ltiCurveUM[0])
      oGcode.millPath([(None, None, iDepthUM)])
      oGcode.millPath(ltiCurveUM[1:])
    oGcode.goto(None, None, m_iSafetyZDistanceUM)

class GCode:
    def __init__(self, fOut):
        self.fOut = fOut

    def coord(self,sG,iX_UM=None,iY_UM=None,iZ_UM=None):
        sOut = str()
        if iX_UM != None:
            sOut += " X{:.2f}".format(iX_UM/1000.0)
        if iY_UM != None:
            sOut += " Y{:.2f}".format(iY_UM/1000.0)
        if iZ_UM != None:
            sOut += " Z{:.2f}".format(iZ_UM/1000.0)
        if len(sOut) > 0:
            self.fOut.write("{:s}{:s}\n".format(sG,sOut))
        else:
            raise ValueError("At least one of X, Y, Z must be given")

    def goto(self,*ti):
        self.coord("G00", *ti)


    def millPath(self, ltiCoordsUM):
        """Creates G-Code from a list of point tuples."""
        for t in ltiCoordsUM:
            self.coord("G01", *t)
    def end(self):
        self.fOut.write("M5\n")
        self.fOut.write("M30\n")

def shiftX(ltCoords, iShiftOffset):
    """Shits x,y tuples on the x coordinate by iShiftOffset."""
    return [ (t[0]+iShiftOffset, t[1]) for t in ltCoords ]

def fullWidthCurve(ltiCoordsUM, iCurveThicknessUM=m_iCurveThicknessUM, iMillDiameterUM=m_iMillDiameterUM):
    ttiLineSegmentsUM = tuple( x for x in zip(ltiCoordsUM, ltiCoordsUM[1:]) )
    ltiCurveLeftUM  = shiftCurve(ltiCoordsUM, (-iCurveThicknessUM+iMillDiameterUM)/2)
    ltiCurveRightUM = shiftCurve(ltiCoordsUM, (+iCurveThicknessUM-iMillDiameterUM)/2)

    return ltiCurveLeftUM + ltiCurveRightUM[::-1] + [ltiCurveLeftUM[0]]

def codeToCurve(iCode, iMaxCode):
    liCode = list()
    while iCode > 0:
        liCode.append(iCode%10)
        iCode = int(iCode/10)
    liXValuesUM = [ x for item in codeToDistance(liCode, iMaxCode) for x in repeat(item, 2) ]
    liYValuesUM = getYValues(iPoints=len(liXValuesUM))
    ltiCoordsUM = list(zip(liXValuesUM, liYValuesUM))
    return ltiCoordsUM

def getCode(sType, lsAllCodes):
    for s in lsAllCodes:
        if s.startswith(sType):
            return int(s[len(sType):][::-1])

def main():
    oParser = argparse.ArgumentParser(description="Generates G-Code for EVVA 3KS curves")
    oParser.add_argument("code", help="key code", nargs='+')
    oParser.add_argument("outfile", help="output file", type=argparse.FileType("w"))
    oArgs = oParser.parse_args()

    iDoubleCurve = getCode("d", oArgs.code)
    iSingleCurve = getCode("s", oArgs.code)
    if iDoubleCurve is None:
        sys.stderr.write("No double curve given\n")
        sys.exit(1)
    if iSingleCurve is None:
        sys.stderr.write("No single curve given\n")
        sys.exit(1)

    print("Generating G-Code for key code: d{:s} s{:s}".format(str(iDoubleCurve)[::-1], str(iSingleCurve)[::-1]))
    ltiDoubleCoordsUM = codeToCurve(iDoubleCurve, m_iCodesDouble)
    ltiDoubleCurveLeft  = list(ltiDoubleCoordsUM)
    createDoubleCurveEntry(ltiDoubleCurveLeft, -1)
    ltiDoubleCurveLeft = fullWidthCurve(ltiDoubleCurveLeft)
    ltiDoubleCurveLeft = shiftX(ltiDoubleCurveLeft, -1250)

    ltiSingleCoordsUM = codeToCurve(iSingleCurve, m_iCodesSingle)
    ltiSingleCurve  = list(ltiSingleCoordsUM)
    ltiSingleCurve = fullWidthCurve(ltiSingleCurve)

    ltiDoubleCurveRight = list(ltiDoubleCoordsUM)
    createDoubleCurveEntry(ltiDoubleCurveRight, 1)
    ltiDoubleCurveRight = fullWidthCurve(ltiDoubleCurveRight)
    ltiDoubleCurveRight = shiftX(ltiDoubleCurveRight, 1250)

    oG = GCode(oArgs.outfile)
    millCurve(shiftX(ltiDoubleCurveLeft, 12750), [1800, 1600], oG)
    millCurve(shiftX(ltiSingleCurve, 12750), [1800, 1600, 1400, 1200, 1100], oG)
    millCurve(shiftX(ltiDoubleCurveRight, 12750), [1800, 1600], oG)

    oG.end()
if __name__ == "__main__":
    main()
