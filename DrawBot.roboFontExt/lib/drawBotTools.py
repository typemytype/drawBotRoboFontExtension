import sys
import traceback

import AppKit


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
    im = AppKit.NSImage.imageNamed_("toolbarScriptNew")
    pdfText = AppKit.NSString.stringWithString_("PDF")

    shadow = AppKit.NSShadow.alloc().init()
    shadow.setShadowOffset_((0, -1))
    shadow.setShadowColor_(AppKit.NSColor.whiteColor())
    shadow.setShadowBlurRadius_(1)

    attributes = {
        AppKit.NSFontAttributeName: AppKit.NSFont.boldSystemFontOfSize_(7),
        AppKit.NSForegroundColorAttributeName: AppKit.NSColor.darkGrayColor(),
        AppKit.NSShadowAttributeName: shadow
    }

    pdfSaveImage = AppKit.NSImage.alloc().initWithSize_(im.size())

    pdfSaveImage.lockFocus()
    im.drawAtPoint_fromRect_operation_fraction_((0, 0), AppKit.NSZeroRect, AppKit.NSCompositeSourceOver, 1)
    pdfText.drawAtPoint_withAttributes_((10, 10), attributes)
    pdfSaveImage.unlockFocus()

    return pdfSaveImage
