import sys
import traceback

from AppKit import *


class StdOutput(object):

    def __init__(self, output, isError=False):
        self.data = output
        self.isError = isError

    def write(self, data):
        self.data.append((data, self.isError))

    def flush(self):
        pass

    def close(self):
        pass


def CallbackRunner(callback, stdout=None, stderr=None, args=[], kwargs={}, fallbackResult=None):
    result = fallbackResult
    saveStdout = sys.stdout
    saveStderr = sys.stderr
    if stdout:
        sys.stdout = stdout
    if stderr:
        sys.stderr = stderr
    try:
        result = callback(*args, **kwargs)
    except:
        etype, value, tb = sys.exc_info()
        if tb.tb_next is not None:
            tb = tb.tb_next
        traceback.print_exception(etype, value, tb)
        etype = value = tb = None
    finally:
        sys.stdout = saveStdout
        sys.stderr = saveStderr

    return result


def createSavePDFImage():
    im = NSImage.imageNamed_("toolbarScriptNew")
    pdfText = NSString.stringWithString_("PDF")

    shadow = NSShadow.alloc().init()
    shadow.setShadowOffset_((0, -1))
    shadow.setShadowColor_(NSColor.whiteColor())
    shadow.setShadowBlurRadius_(1)

    attributes = {
        NSFontAttributeName: NSFont.boldSystemFontOfSize_(7),
        NSForegroundColorAttributeName: NSColor.darkGrayColor(),
        NSShadowAttributeName: shadow
    }

    pdfSaveImage = NSImage.alloc().initWithSize_(im.size())

    pdfSaveImage.lockFocus()
    im.drawAtPoint_fromRect_operation_fraction_((0, 0), NSZeroRect, NSCompositeSourceOver, 1)
    pdfText.drawAtPoint_withAttributes_((10, 10), attributes)
    pdfSaveImage.unlockFocus()

    return pdfSaveImage
