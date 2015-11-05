import sys
import os

from fontTools.pens.cocoaPen import CocoaPen

from drawBot.drawBotDrawingTools import _drawBotDrawingTool
from drawBot.context.baseContext import BezierPath
from drawBot.context import subscribeContext


from mojo.events import addObserver
from mojo.extensions import getExtensionDefault

from drawBotController import DrawBotController
import glyphContext

# add drawBot to the sys path
sys.path.append(os.path.dirname(__file__))


# add a drawGlyph callback
def drawGlyph(glyph):
    if hasattr(glyph, "getRepresentation"):
        path = glyph.getRepresentation("defconAppKit.NSBezierPath")
    else:
        pen = CocoaPen(glyph.getParent())
        glyph.draw(pen)
        path = pen.path
    _drawBotDrawingTool.drawPath(path)

_drawBotDrawingTool.drawGlyph = drawGlyph


# add a addGlyph callback in a bezierPath
class RFBezierPath(glyphContext.GlyphBezierPath):

    def addGlyph(self, glyph):
        if hasattr(glyph, "getRepresentation"):
            path = glyph.getRepresentation("defconAppKit.NSBezierPath")
        else:
            pen = CocoaPen(glyph.getParent())
            glyph.draw(pen)
            path = pen.path
        self.getNSBezierPath().appendBezierPath_(path)

_drawBotDrawingTool._bezierPathClass = RFBezierPath


# add a glyphContext
subscribeContext(glyphContext.GlyphContext)


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
            _, ext = os.path.splitext(path)
            if ext.lower() == ".py":
                DrawBotController().open(path)
                fileHandler["opened"] = True

OpenFilesInDrawBotController()
