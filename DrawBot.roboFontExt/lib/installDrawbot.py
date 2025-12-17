import sys
import os

from fontTools.pens.cocoaPen import CocoaPen

from drawBot.drawBotDrawingTools import _drawBotDrawingTool
from drawBot.context.baseContext import BezierPath
from drawBot.context import subscribeContext

from settings import DrawBotSettingsController

from mojo.events import addObserver
from mojo.extensions import getExtensionDefault, ExtensionBundle
from mojo.tools import CallbackWrapper

from drawBotController import DrawBotController
import glyphContext

import AppKit
from fontTools.ufoLib.glifLib import readGlyphFromString
from merz.tools.drawingTools import NSImageDrawingTools
import math
from vanilla.vanillaList import VanillaMenuBuilder


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
        self._callbacks = []
        self.addToMenu()

    def addToMenu(self):
        menubar = AppKit.NSApp().mainMenu()

        menuItem = menubar.itemWithTitle_("DrawBot")
        if menuItem: menubar.removeItem_(menuItem)

        item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("DrawBot", "", "")
        item.setImage_(self.menuBarIcon)

        menu = AppKit.NSMenu.alloc().initWithTitle_("DrawBot")

        # build this one separately so we can override the bindings
        buildDrawBotItem = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("DrawBot", "action:", "D")
        target = CallbackWrapper(self.openDrawBotCallback)
        self._callbacks.append(target) # we need to keep a live reference to the callback
        buildDrawBotItem.setTarget_(target)
        buildDrawBotItem.setKeyEquivalentModifierMask_(AppKit.NSShiftKeyMask | AppKit.NSCommandKeyMask);

        menuItems = [
            buildDrawBotItem,
            dict(title="Settings", callback=self.drawBotSettingsCallback),
            "----",
            dict(title="Help", callback=self.drawBotHelpCallback),
        ]

        VanillaMenuBuilder(self, menuItems, menu)
        item.setSubmenu_(menu)
        menubar.insertItem_atIndex_(item, menubar.numberOfItems() - 1)


    def drawBotSettingsCallback(self, sender):
        DrawBotSettingsController()

    def openDrawBotCallback(self, sender):
        DrawBotController().open()

    def drawBotHelpCallback(self, sender):
        ExtensionBundle("DrawBot").openHelp()

    def openFile(self, notification):
        fileHandler = notification["fileHandler"]
        path = notification["path"]
        _, ext = os.path.splitext(path)
        if ext.lower() == ".py":
            with open(path, "r", encoding="utf8") as file:
                header = file.readline().strip('\n')
                # dont be strict about case or whitespace
                if header.lower().replace(" ", "") == "#drawbot" or getExtensionDefault("com.drawBot.openPyFileDirectly", False):
                    if not fileHandler.get("opened", False): # check if the file is already opened !
                        DrawBotController().open(path)
                        fileHandler["opened"] = True


    @property
    def menuBarIcon(self):
        iconGlifString = b"""<?xml version='1.0' encoding='UTF-8'?>
        <glyph name="a" format="2">
          <advance width="796"/>
          <outline>
            <contour>
              <point x="30" y="709" type="line"/>
              <point x="137" y="725"/>
              <point x="232" y="733"/>
              <point x="314" y="733" type="curve" smooth="yes"/>
              <point x="633" y="733"/>
              <point x="766" y="612"/>
              <point x="766" y="374" type="curve" smooth="yes"/>
              <point x="766" y="134"/>
              <point x="632" y="12"/>
              <point x="313" y="12" type="curve" smooth="yes"/>
              <point x="231" y="12"/>
              <point x="137" y="20"/>
              <point x="30" y="36" type="curve"/>
            </contour>
            <contour>
              <point x="307" y="479" type="curve"/>
              <point x="307" y="266" type="line"/>
              <point x="321" y="265"/>
              <point x="333" y="265"/>
              <point x="345" y="265" type="curve" smooth="yes"/>
              <point x="446" y="265"/>
              <point x="492" y="299"/>
              <point x="492" y="374" type="curve" smooth="yes"/>
              <point x="492" y="446"/>
              <point x="449" y="481"/>
              <point x="353" y="481" type="curve" smooth="yes"/>
              <point x="339" y="481"/>
              <point x="324" y="481"/>
            </contour>
          </outline>
        </glyph>
        """

        iconGlyph = RGlyph()
        readGlyphFromString(iconGlifString, glyphObject=iconGlyph, pointPen=iconGlyph.getPointPen())
        bot = NSImageDrawingTools((iconGlyph.width*1.2, iconGlyph.bounds[3]), scale=.02)

        bot.fill(1,1,1,.2)
        bezPen = bot.BezierPath()
        iconGlyph.draw(bezPen)
        bot.drawPath(bezPen)

        bot.fill(0,0,0,1)
        pencil = [(545,315),(575,185),(710,220),(875,535),(710,630)]
        bot.polygon(*pencil, close=True)

        image = bot.getImage()
        image.setTemplate_(True)

        return image

if __name__ == "__main__":
    OpenFilesInDrawBotController()
