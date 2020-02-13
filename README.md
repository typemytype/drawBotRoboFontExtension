DrawBot RoboFont Extension
==========================

[DrawBot](http://drawbot.com/) inside [RoboFont](http://doc.robofont.com).

The extension has access to all the RoboFont [API](http://doc.robofont.com/api/) and callbacks. So for example `CurrentFont()` and `CurrentGlyph()` are directly accessible in a script!

Additional Callbacks
--------------------

`drawGlyph(aGlyph)` draws a glyph

`bezierPath.addGlyph(aglyph)` adds a glyph to the BezierPath object

Settings
--------

There is one setting: you can tell RoboFont to use DrawBot as the default .py editor.

As Module
---------

The extension installs also `drawBot` as module. This allows to use `import drawBot` and use drawBot in any script.

```python
from drawBot import *
# reset the drawing stack
newDrawing()
# loop over all glyphs
for glyph in CurrentFont():
	# create a new page
	newPage(1000, 1000)
	# draw each glyph on the page
	drawGlyph(glyph)
```
