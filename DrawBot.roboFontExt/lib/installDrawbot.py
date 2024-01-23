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

root = os.path.dirname(__file__)
# add drawBot to the sys path
sys.path.append(root)

# set the gifsicle tool as executable
gifsiclePath = os.path.join(root, "drawBot", "context", "tools", "gifsicle")
potrace = os.path.join(root, "drawBot", "context", "tools", "potrace")
mkbitmap = os.path.join(root, "drawBot", "context", "tools", "mkbitmap")
ffmpeg = os.path.join(root, "drawBot", "context", "tools", "ffmpeg")
os.chmod(gifsiclePath, 0o0755)
os.chmod(potrace, 0o0755)
os.chmod(mkbitmap, 0o0755)
os.chmod(ffmpeg, 0o0755)


# add a drawGlyph callback
def drawGlyph(glyph):
    if hasattr(glyph, "getRepresentation"):
        path = glyph.getRepresentation("defconAppKit.NSBezierPath")
    else:
        font = None
        if hasattr(glyph, "font"):
            font = glyph.font
        elif hasattr(glyph, "getParent"):
            font = glyph.getParent()
        pen = CocoaPen(font)
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
            font = None
            if hasattr(glyph, "font"):
                font = glyph.font
            elif hasattr(glyph, "getParent"):
                font = glyph.getParent()
            pen = CocoaPen(font)
            glyph.draw(pen)
            path = pen.path
        self.getNSBezierPath().appendBezierPath_(path)

_drawBotDrawingTool._bezierPathClass = RFBezierPath


# add a glyphContext
subscribeContext(glyphContext.GlyphContext)


# reload the module to make them everwhere available
import drawBot
try:
    # in py2
    reload
except NameError:
    # in py3
    from importlib import reload

reload(drawBot)

class OpenFilesInDrawBotController(object):

    def __init__(self):
        addObserver(self, "openFile", "applicationOpenFile")

    def openFile(self, notification):
        fileHandler = notification["fileHandler"]
        path = notification["path"]
        _, ext = os.path.splitext(path)
        if ext.lower() == ".py":
            with open(path, "r", encoding="utf8") as file:
                header = file.readline().strip('\n')
                # dont be strict about case or whitespace
                if header.lower().replace(" ", "") == "#drawbot" or getExtensionDefault("com.drawBot.openPyFileDirectly", False):
                    DrawBotController().open(path)
                    fileHandler["opened"] = True

OpenFilesInDrawBotController()
