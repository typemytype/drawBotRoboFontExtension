from vanilla import *

from mojo.extensions import getExtensionDefault, setExtensionDefault


class DrawBotSettingsController(object):

    def __init__(self):
        self.w = Window((250, 45), "DrawBot Settings")

        self.w.openPythonFilesInDrawBot = CheckBox((10, 10, -10, 22),
            "Open .py files directly in DrawBot.",
            value=getExtensionDefault("com.drawBot.openPyFileDirectly", False),
            callback=self.openPythonFilesInDrawBotCallback)

        self.w.open()

    def openPythonFilesInDrawBotCallback(self, sender):
        setExtensionDefault("com.drawBot.openPyFileDirectly", sender.get())


DrawBotSettingsController()
