import CoreText
import AppKit
import os
import re

from drawBot.context.baseContext import BaseContext, GraphicsState, BezierPath

from fontTools.misc.transform import Transform

from mojo.roboFont import RGlyph, CurrentFont, CurrentGlyph


layerNameRE = re.compile('\((.*?)\)')


class GlyphDrawBotError(Exception):

    pass


class GlyphBezierPath(BezierPath):

    def oval(self, x, y, w, h):
        # make the oval with points at the extremes
        # the NSBezierPath oval has no extreme points
        c = 0.60
        hx = w * c * .5
        hy = h * c * .5
        self.moveTo((x+w*.5, y))
        self.curveTo((x+w*.5 + hx, y), (x+w, y+h*.5 - hy), (x+w, y+h*.5))
        self.curveTo((x+w, y+h*.5 + hy), (x+w*.5 + hx, y+h), (x+w*.5, y+h))
        self.curveTo((x+w*.5 - hx, y+h), (x, y+h*.5 + hy), (x, y+h*.5))
        self.curveTo((x, y+h*.5 - hy), (x+w*.5 - hx, y), (x+w*.5, y))
        self.closePath()


class GlyphGraphicsState(GraphicsState):

    def __init__(self):
        super(GlyphGraphicsState, self).__init__()
        # keep a custom transform matrix
        self.transformMatrix = Transform(1, 0, 0, 1, 0, 0)

    def copy(self):
        new = super(GlyphGraphicsState, self).copy()
        new.transformMatrix = Transform(*self.transformMatrix[:])
        return new


class GlyphContext(BaseContext):

    fileExtensions = ["glyph"]

    _graphicsStateClass = GlyphGraphicsState
    _bezierPathClass = GlyphBezierPath

    def __init__(self):
        super(GlyphContext, self).__init__()
        self._glyphs = []
        self._pen = None
        self._layerCount = 0

    def _newPage(self, width, height):
        self._glyphs.append(RGlyph())
        self._pen = self._glyphs[-1].getPen()
        self.reset()

    def _save(self):
        pass

    def _restore(self):
        pass

    def _blendMode(self, operation):
        pass

    def _drawPath(self):
        path = self._state.path
        for contour in path.contours:
            point = contour[0][0]
            point = self._state.transformMatrix.transformPoint(point)
            self._pen.moveTo(point)
            for points in contour[1:]:
                if len(points) == 1:
                    func = self._pen.lineTo
                else:
                    func = self._pen.curveTo
                points = self._state.transformMatrix.transformPoints(points)
                func(*points)
            if contour.open:
                self._pen.endPath()
            else:
                self._pen.closePath()

    def _clipPath(self):
        pass

    def _transform(self, transform):
        self._state.transformMatrix = self._state.transformMatrix.transform(transform)

    def _textBox(self, txt, (x, y, w, h), align):
        attrString = self.attributedString(txt, align=align)
        if self._state.text.hyphenation:
            attrString = self.hyphenateAttributedString(attrString, w)
        txt = attrString.string()

        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        path = CoreText.CGPathCreateMutable()
        CoreText.CGPathAddRect(path, None, CoreText.CGRectMake(x, y, w, h))
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)

        ctLines = CoreText.CTFrameGetLines(box)
        origins = CoreText.CTFrameGetLineOrigins(box, (0, len(ctLines)), None)

        path = self._bezierPathClass()

        for i, (originX, originY) in enumerate(origins):
            ctLine = ctLines[i]
            ctRuns = CoreText.CTLineGetGlyphRuns(ctLine)
            for ctRun in ctRuns:
                attributes = CoreText.CTRunGetAttributes(ctRun)
                font = attributes.get(AppKit.NSFontAttributeName)
                fontName = font.fontName()
                fontSize = font.pointSize()

                r = CoreText.CTRunGetStringRange(ctRun)
                runTxt = txt.substringWithRange_((r.location, r.length))

                while runTxt and runTxt[-1] == " ":
                    runTxt = runTxt[:-1]
                runTxt = runTxt.replace("\n", "")
                runTxt = runTxt.encode("utf-8")

                runPos = CoreText.CTRunGetPositions(ctRun, (0, 1), None)
                runX = runY = 0
                if runPos:
                    runX = runPos[0].x
                    runY = runPos[0].y

                offset = originX + runX + x, originY + runY + y

                path.text(runTxt, font=fontName, fontSize=fontSize, offset=offset)

        self.drawPath(path)

    def _image(self, path, (x, y), alpha):
        image = self._glyphs[-1].addImage(path, (x, y))
        image.brightness = alpha
        image.transformation = self._state.transformMatrix

    def _frameDuration(self, seconds):
        pass

    def _reset(self):
        pass

    def _saveImage(self, path, multipage):
        # extract glyph name and layername for the path
        # full syntax: 'a(background).glyph'
        # draw in glyph with name 'a' in the 'background' layer
        glyphName, ext = os.path.splitext(os.path.basename(path))
        # extract the layername
        layerName = layerNameRE.findall(glyphName)
        # replace the layername by nothing
        glyphName = layerNameRE.sub("", glyphName)
        # layer name found
        if layerName:
            layerName = layerName[0]
        else:
            layerName = None
        # if there is an extension --> there is a glyph name
        # get the glyph from the CurrentFont
        # otherwise draw in the CurrentGlyph
        if ext:
            font = CurrentFont()
            if glyphName not in font:
                dest = font.newGlyph(glyphName)
                if dest is None:
                    raise GlyphDrawBotError("No font available to draw in")
                dest.width = 500
            else:
                dest = font[glyphName]
        else:
            dest = CurrentGlyph()
        # can not found a proper glyph to draw in
        if dest is None:
            raise GlyphDrawBotError("No glyph available to draw in")

        multiplePages = len(self._glyphs) > 1

        for count, glyph in enumerate(self._glyphs):
            if layerName:
                if multiplePages:
                    n = "%s_%s" % (layerName, count + 1)
                else:
                    n = layerName
                destLayer = dest.getLayer(n)
            else:
                destLayer = dest
                layerName = "drawBot"
            destLayer.appendGlyph(glyph)

            if glyph.image:
                image = glyph.image
                destImage = destLayer.addImage(image.path)
                destImage.transformation = image.transformation

    def _printImage(self, pdf=None):
        pass
