# -*- coding: utf-8 -*-

from PySide.QtGui import *
from PySide.QtCore import *


class FramedLabel (QFrame):

    def __init__ (self, text = None, style = QFrame.StyledPanel | QFrame.Sunken, parent = None):
        super (FramedLabel, self).__init__ (parent)
        self.setFrameStyle (style)
        l = QVBoxLayout (self)
        l.setContentsMargins (2, 2, 2, 2)
        self.lText = QLabel (self)
        l.addWidget (self.lText)
        if text:
            self.setText (text)

    def text (self):
        return self.lText.text ()

    def setText (self, value):
        self.lText.setText (value)


class SquareButton (QToolButton):

    defaultSize = QSize (80, 80)
    defaultIconSize = QSize (48, 48)

    def __init__ (self, name, text, parent = None):
        super (SquareButton, self).__init__ (parent)
        self.setMinimumSize (self.defaultSize)
        self.setIconSize (self.defaultIconSize)
        self.setCheckable (True)
        self.setChecked (False)
        self.setAutoExclusive (True)
        self.setToolButtonStyle (Qt.ToolButtonTextUnderIcon)
        self.setText (text)
        self.setName (name)

    def name (self):
        return self._name

    def setName (self, value):
        self._name = value
        self.setIcon (QIcon (QPixmap (':/res/icons/%s.png' % self.name ())))


class Scrollable (QWidget):

    def __init__ (self, parent = None):
        super (Scrollable, self).__init__ (parent)
        self.setupUi ()

    def setupUi (self):
        layout = QVBoxLayout (self)
        self.scrollArea = QScrollArea (self)
        self.scrollArea.setWidgetResizable (True)
        self.scrollArea.setFrameShape (QFrame.NoFrame)
        layout.addWidget (self.scrollArea)

        self.content = QWidget (self)
        self.content.setSizePolicy (QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.scrollArea.setWidget (self.content)

        self.setSizePolicy (QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

