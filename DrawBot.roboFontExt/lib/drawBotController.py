# -*- coding: utf-8 -*-
import AppKit

from vanilla import *
from defconAppKit.windows.baseWindow import BaseWindowController

from lib.scripting.codeEditor import OutPutEditor
from lib.scripting.scriptTools import ScriptRunner
from lib.tools.defaults import getDefault, setDefault

from drawBot.ui.drawView import DrawView, ThumbnailView

from drawBot.drawBotDrawingTools import _drawBotDrawingTool
from drawBot.context.drawBotContext import DrawBotContext

from drawBot.misc import warnings
from drawBot.ui.splitView import SplitView

from drawBotViews import CodeEditor
from drawBotTools import StdOutput, CallbackRunner, createSavePDFImage


class DrawBotController(BaseWindowController):

    """
    The controller for a DrawBot window.
    """

    windowAutoSaveName = "DrawBotController"

    def __init__(self):
        # make a window
        self.w = Window((400, 400), "DrawBot", minSize=(200, 200), textured=False)
        # setting previously stored frames, if any
        self.w.getNSWindow().setFrameUsingName_(self.windowAutoSaveName)
        try:
            # on 10.7+ full screen support
            self.w.getNSWindow().setCollectionBehavior_(128) #NSWindowCollectionBehaviorFullScreenPrimary
        except:
            pass

        toolbarItems = [
            dict(itemIdentifier="run",
                label="Run",
                imageNamed="toolbarRun",
                callback=self.toolbarRun,
                imageTemplate=True,
                ),
            dict(itemIdentifier="comment",
                label="Comment",
                imageNamed="toolbarComment",
                callback=self.toolbarComment,
                imageTemplate=True,
                ),
            dict(itemIdentifier="uncomment",
                label="Uncomment",
                imageNamed="toolbarUncomment",
                callback=self.toolbarUncomment,
                imageTemplate=True,
                ),
            dict(itemIdentifier="indent",
                label="Indent",
                imageNamed="toolbarIndent",
                callback=self.toolbarIndent,
                imageTemplate=True,
                ),
            dict(itemIdentifier="dedent",
                label="Dedent",
                imageNamed="toolbarDedent",
                callback=self.toolbarDedent,
                imageTemplate=True,
                ),
            dict(itemIdentifier=AppKit.NSToolbarFlexibleSpaceItemIdentifier),

            dict(itemIdentifier="save",
                label="Save",
                imageNamed="toolbarScriptSave",
                callback=self.toolbarSave,
                imageTemplate=True,
                ),
            dict(itemIdentifier="savePDF",
                label=u"Save PDF…",
                imageObject=createSavePDFImage(),
                callback=self.toolbarSavePDF,
                imageTemplate=True,
                ),

            dict(itemIdentifier=AppKit.NSToolbarSpaceItemIdentifier),

            dict(itemIdentifier="reload",
                label="Reload",
                imageNamed="toolbarScriptReload",
                callback=self.toolbarReload,
                imageTemplate=True,
                ),
            dict(itemIdentifier="new",
                label="New",
                imageNamed="toolbarScriptNew",
                callback=self.toolbarNewScript,
                imageTemplate=True,
                ),
            dict(itemIdentifier="open",
                label=u"Open…",
                imageNamed="toolbarScriptOpen",
                callback=self.toolbarOpen,
                imageTemplate=True,
                ),
            dict(itemIdentifier=AppKit.NSToolbarFlexibleSpaceItemIdentifier),
            ]
        self.w.addToolbar(toolbarIdentifier="DrawBotRoboFontExtensionToolbar", toolbarItems=toolbarItems, addStandardItems=False)

        # the code editor
        self.codeView = CodeEditor((0, 0, -0, -0))
        self.codeView.setCallback(self.runCode)
        # the output view (will catch all stdout and stderr)
        self.outPutView = OutPutEditor((0, 0, -0, -0), readOnly=True)
        # the view to draw in
        self.drawView = DrawView((0, 0, -0, -0))
        # the view with all thumbnails
        self.thumbnails = ThumbnailView((0, 0, -0, -0))
        # connect the thumbnail view with the draw view
        self.thumbnails.setDrawView(self.drawView)

        # collect all code text view in a splitview
        paneDescriptors = [
            dict(view=self.codeView, identifier="codeView", minSize=50, canCollapse=False),
            dict(view=self.outPutView, identifier="outPutView", size=100, minSize=50, canCollapse=False),
        ]
        self.codeSplit = SplitView((0, 0, -0, -0), paneDescriptors, isVertical=False)

        # collect the draw scroll view and the code split view in a splitview
        paneDescriptors = [
            dict(view=self.thumbnails, identifier="thumbnails", minSize=100, size=100, maxSize=100),
            dict(view=self.drawView, identifier="drawView", minSize=50),
            dict(view=self.codeSplit, identifier="codeSplit", minSize=50, canCollapse=False),
        ]
        self.w.split = SplitView((0, 0, -0, -0), paneDescriptors)

        # setup BaseWindowController base behavoir
        self.setUpBaseWindowBehavior()

        # get the real size of the window
        windowX, windowY, windowWidth, windowHeight = self.w.getPosSize()
        # set the split view dividers at a specific position based on the window size
        self.w.split.setDividerPosition(0, 0)
        self.w.split.setDividerPosition(1, windowWidth * .6)
        self.codeSplit.setDividerPosition(0, windowHeight * .7)

    def runCode(self, liveCoding=False):
        # get the code
        code = self.code()
        # save the code in the defaults, if something goes wrong
        setDefault("pythonCodeBackup", code)
        # get te path of the document (will be None for an untitled document)
        path = self.path()
        # reset the internal warning system
        warnings.resetWarnings()
        # reset the drawing tool
        _drawBotDrawingTool.newDrawing()
        # create a namespace
        namespace = {}
        # add the tool callbacks in the name space
        _drawBotDrawingTool._addToNamespace(namespace)
        # when enabled clear the output text view
        if getDefault("PyDEClearOutput", True):
            self.outPutView.clear()
        # create a new std output, catching all print statements and tracebacks
        self.output = []
        self.stdout = StdOutput(self.output)
        self.stderr = StdOutput(self.output, True)
        # warnings should show the warnings
        warnings.shouldShowWarnings = True
        # run the code
        ScriptRunner(code, path, namespace=namespace, stdout=self.stdout, stderr=self.stderr)
        # warnings should stop posting them
        warnings.shouldShowWarnings = False
        # set context, only when the panes are visible
        if self.w.split.isPaneVisible("drawView") or self.w.split.isPaneVisible("thumbnails"):
            def createContext(context):
                # draw the tool in to the context
                _drawBotDrawingTool._drawInContext(context)
            # create a context to draw in
            context = DrawBotContext()
            # savely run the callback and track all traceback back the the output
            CallbackRunner(createContext, stdout=self.stdout, stderr=self.stderr, args=[context])
            # get the pdf document and set in the draw view
            pdfDocument = context.getNSPDFDocument()
            if not liveCoding or (pdfDocument and pdfDocument.pageCount()):
                self.drawView.setPDFDocument(pdfDocument)
            # scroll down
            self.drawView.scrollDown()
        else:
            # if the panes are not visible, clear the draw view
            self.drawView.setPDFDocument(None)
        # drawing is done
        _drawBotDrawingTool.endDrawing()
        # set the catched print statements and tracebacks in the the output text view
        for text, isError in self.output:
            if liveCoding and isError:
                continue
            self.outPutView.append(text, isError)

        # reset the code backup if the script runs with any crashes
        setDefault("pythonCodeBackup", None)
        # clean up

        self.output = None
        self.stdout = None
        self.stderr = None

    def checkSyntax(self, sender=None):
        # get the code
        code = self.code()
        # get te path of the document (will be None for an untitled document)
        path = self.path()
        # when enabled clear the output text view
        if getDefault("PyDEClearOutput", True):
            self.outPutView.set("")
        # create a new std output, catching all print statements and tracebacks
        self.output = []
        self.stdout = StdOutput(self.output)
        self.stderr = StdOutput(self.output, True)
        # run the code, but with the optional flag checkSyntaxOnly so it will just compile the code
        ScriptRunner(code, path, stdout=self.stdout, stderr=self.stderr, checkSyntaxOnly=True)
        # set the catched print statements and tracebacks in the the output text view
        for text, isError in self.output:
            self.outPutView.append(text, isError)
        # clean up
        self.output = None
        self.stdout = None
        self.stderr = None

    def _savePDF(self, path):
        # get the pdf date from the draw view
        data = self.drawView.get()
        if data:
            # if there is date save it
            data.writeToFile_atomically_(path , False)

    def savePDF(self, sender=None):
        """
        Save the content as a pdf.
        """
        # pop up a show put file sheet
        self.showPutFile(["pdf"], callback=self._savePDF)

    def setPath(self, path):
        """
        Sets the content of a file into the code view.
        """
        # open a file
        f = open(path)
        # read the content
        code = f.read()
        # close the file
        f.close()
        # set the content into the code view
        self.codeView.set(code)

    def path(self):
        """
        Returns the path of the document,
        return None if the document is never saved before.
        """
        # get the docuemnt
        document = self.document()
        # check if it is not None
        if document is None:
            return None
        # get the url of the document
        url = document.fileURL()
        if url is None:
            return None
        # return the path as a string
        return url.path()

    def code(self):
        """
        Returns the content of the code view as a string.
        """
        return self.codeView.get()

    getText = code

    def setCode(self, code):
        """
        Sets code in to the code view.
        """
        self.codeView.set(code)

    def pdfData(self):
        """
        Returns the pdf data from the draw view
        """
        return self.drawView.get()

    def set(self, path, force=False):
        self.setPath(path)

    # UI

    def open(self, path=None):
        documentController = AppKit.NSDocumentController.sharedDocumentController()
        documentClass = documentController.documentClassForType_("Python Source File")
        document = documentClass.alloc().init()
        document.vanillaWindowController = self
        documentController.addDocument_(document)
        document.addWindowController_(self.w.getNSWindowController())
        if path:
            self.codeView.openFile(path)
        # open the window
        self.w.open()
        # set the code view as first responder
        self.w.getNSWindow().makeFirstResponder_(self.codeView.getNSTextView())

    def assignToDocument(self, nsDocument):
        # assing the window to the document
        self.w.assignToDocument(nsDocument)

    def document(self):
        """
        Returns the document.
        """
        return self.w.getNSWindow().document()

    def setUpBaseWindowBehavior(self):
        # bind whenever a user moves or resizes a window
        self.w.bind("move", self.windowMoveCallback)
        self.w.bind("resize", self.windowResizeCallback)
        super(DrawBotController, self).setUpBaseWindowBehavior()

    def windowMoveCallback(self, sender):
        # save the frame in the defaults
        self.w.getNSWindow().saveFrameUsingName_(self.windowAutoSaveName)

    def windowResizeCallback(self, sender):
        # save the frame in the defaults
        self.w.getNSWindow().saveFrameUsingName_(self.windowAutoSaveName)

    def windowCloseCallback(self, sender):
        # unbind on window close
        self.w.unbind("move", self.windowMoveCallback)
        self.w.unbind("resize", self.windowResizeCallback)
        super(DrawBotController, self).windowCloseCallback(sender)

    # toolbar

    def toolbarRun(self, sender):
        self.runCode()

    def toolbarComment(self, sender):
        self.codeView.comment()

    def toolbarUncomment(self, sender):
        self.codeView.uncomment()

    def toolbarIndent(self, sender):
        self.codeView.indent()

    def toolbarDedent(self, sender):
        self.codeView.dedent()

    def toolbarReload(self, sender):
        self.codeView.reload()

    def toolbarOpen(self, sender):
        self.codeView.open()
        self.document().windowController = self

    def toolbarNewScript(self, sender):
        self.codeView.newScript()
        self.document().windowController = self

    def toolbarSavePDF(self, sender):
        self.savePDF()

    def toolbarSave(self, sender):
        if AppKit.NSEvent.modifierFlags() & AppKit.NSAlternateKeyMask:
            self.document().saveDocumentAs_(self)
        else:
            self.document().saveDocument_(self)
