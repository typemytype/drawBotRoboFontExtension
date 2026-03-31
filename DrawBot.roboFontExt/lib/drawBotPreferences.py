import vanilla

from mojo.extensions import getExtensionDefault, setExtensionDefault


class DrawBotPreferencesController(object):

    def __init__(self):
        self.w = vanilla.Window((250, 45), "DrawBot Settings")

        self.w.openPythonFilesInDrawBot = vanilla.CheckBox(
            (10, 10, -10, 22),
            "Open .py files directly in DrawBot.",
            value=getExtensionDefault("com.drawBot.openPyFileDirectly", False),
            callback=self.openPythonFilesInDrawBotCallback
        )

        self.w.open()

    def openPythonFilesInDrawBotCallback(self, sender):
        setExtensionDefault("com.drawBot.openPyFileDirectly", sender.get())


DrawBotPreferencesController()
