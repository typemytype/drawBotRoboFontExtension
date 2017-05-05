from lib.scripting.scriptingWindow import PyTextEditor
from lib.scripting.PyDETextView import PyDETextView


class DrawBotPyDETextView(PyDETextView):

    def runPython_(self, sender):
        self._runCodeCallback()


class CodeEditor(PyTextEditor):

    nsTextViewClass = DrawBotPyDETextView

    def setCallback(self, callback):
        self.getNSTextView()._runCodeCallback = callback
