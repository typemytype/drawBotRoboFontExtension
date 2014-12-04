import sys
import os

from fontTools.pens.cocoaPen import CocoaPen

from drawBot.drawBotDrawingTools import _drawBotDrawingTool
from drawBot.context.baseContext import BezierPath

from mojo.events import addObserver
from mojo.extensions import getExtensionDefault

from drawBotController import DrawBotController

sys.path.append(os.path.dirname(__file__))

def drawGlyph(glyph):
    if hasattr(glyph, "getRepresentation"):
        path = glyph.getRepresentation("defconAppKit.NSBezierPath")
    else:
        pen = CocoaPen(glyph.getParent())
        glyph.draw(pen)
        path = pen.path
    _drawBotDrawingTool.drawPath(path)

_drawBotDrawingTool.drawGlyph = drawGlyph

class RFBezierPath(BezierPath):

    def addGlyph(self, glyph):
        if hasattr(glyph, "getRepresentation"):
            path = glyph.getRepresentation("defconAppKit.NSBezierPath")
        else:
            pen = CocoaPen(glyph.getParent())
            glyph.draw(pen)
            path = pen.path
        self.getNSBezierPath().appendBezierPath_(path)

_drawBotDrawingTool._bezierPathClass = RFBezierPath

# reload the module to make them everwhere available
import drawBot
reload(drawBot)

class OpenFilesInDrawBotController(object):

    def __init__(self):
        addObserver(self, "openFile", "applicationOpenFile")

    def openFile(self, notification):
        if getExtensionDefault("com.drawBot.openPyFileDirectly", False):
            fileHandler = notification["fileHandler"]
            path = notification["path"]
            DrawBotController().open(path)
            fileHandler["opened"] = True

OpenFilesInDrawBotController()
