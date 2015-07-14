#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide.QtGui import *
from PySide.QtCore import *
import sys
import resources_rc #@UnusedImport
import pages

#===============================================================================
# Init
#===============================================================================

app = QApplication (sys.argv)

app.setOrganizationName ('UncleRus')
app.setApplicationName ('MultiOSD configurator')
app.setApplicationVersion ('0.2')


#===============================================================================
# Tools
#===============================================================================

class SquareButton (QToolButton):

    defaultSize = QSize (80, 80)
    defaultIconSize = QSize (48, 48)

    def __init__ (self, text, parent = None):
        super (SquareButton, self).__init__ (parent)
        self.setMinimumSize (self.defaultSize)
        self.setIconSize (self.defaultIconSize)
        self.setCheckable (True)
        self.setChecked (False)
        self.setToolButtonStyle (Qt.ToolButtonTextUnderIcon)
        self.setText (text)

    def setText (self, value):
        super (SquareButton, self).setText (value)
        self.setIcon (QIcon (QPixmap (':/res/icons/%s.png' % value)))


class PageButton (SquareButton):

    def __init__ (self, text, factory, widgetParent, parent = None):
        super (PageButton, self).__init__ (text, parent)
        self.factory = factory
        self.widgetParent = widgetParent
        self.widget = None
        self.setEnabled (False)
        self.toggled.connect (self.onToggled)

    def init (self):
        if self.widget:
            raise RuntimeError ('Widget is already set')
        self.widget = self.factory (self.text (), self.widgetParent)
        self.widgetParent.addWidget (self.widget)
        self.setEnabled (True)
        #self.widget.hide ()

    def clear (self):
        self.widget.deleteLater ()
        self.widget = None
        self.setEnabled (False)

    def onToggled (self, checked):
        #self.widget.setVisible (checked)
        if checked:
            self.widgetParent.setCurrentWidget (self.widget)


#===============================================================================
# Main window
#===============================================================================

class MainWindow (QWidget):

    padding = 16

    def __init__ (self):
        super (MainWindow, self).__init__ ()
        self.board = None
        self.setupUi ()
        #self.refreshUi ()

    def setupUi (self):
        self.setWindowTitle (u'%s v.%s' % (QApplication.applicationName (), QApplication.applicationVersion ()))
        self.lMain = QHBoxLayout (self)

        # buttons panel
        self.pButtons = QFrame (self)
        self.pButtons.setMinimumWidth (SquareButton.defaultSize.width () + self.padding)
        self.pButtons.setMaximumWidth (self.pButtons.minimumWidth ())
        self.pButtons.setFrameStyle (QFrame.StyledPanel | QFrame.Sunken)
        lButtons = QVBoxLayout (self.pButtons)
        self.lMain.addWidget (self.pButtons)

        # content
        self.content = QStackedWidget (self)
        self.content.resize (100, 100)
        self.lMain.addWidget (self.content)

        # port
        lButtons.addWidget (QLabel ('Port:', self.pButtons))
        self.cbPort = QComboBox (self.pButtons)
        self.cbPort.setEditable (True)
        self.cbPort.setEditText ('/dev/ttyUSB0')
        lButtons.addWidget (self.cbPort)

        # Connect/Disconnect button
        self.bConnect = SquareButton ('Connect', self.pButtons)
        lButtons.addWidget (self.bConnect)

        # Firmware button
        self.bFirmware = PageButton ('Firmware', pages.FirmwareWidget, self.content, self.pButtons)
        self.bFirmware.init ()
        lButtons.addWidget (self.bFirmware)

        lButtons.addStretch ()

        # config buttons
        self.bPicture = PageButton ('Picture', pages.ConfigWidget, self.content, self.pButtons)
        lButtons.addWidget (self.bPicture)
        self.bADC = PageButton ('ADC', pages.ConfigWidget, self.content, self.pButtons)
        lButtons.addWidget (self.bADC)
        self.bBattery = PageButton ('Battery', pages.ConfigWidget, self.content, self.pButtons)
        lButtons.addWidget (self.bBattery)
        self.bTelemetry = PageButton ('Telemetry', pages.ConfigWidget, self.content, self.pButtons)
        lButtons.addWidget (self.bTelemetry)
        self.bOSD = PageButton ('OSD', pages.ConfigWidget, self.content, self.pButtons)
        lButtons.addWidget (self.bOSD)
#        self.bScreens = PageButton ('Screens', pages.ConfigWidget, self.content, self.pButtons)
#        lButtons.addWidget (self.bScreens)

        lButtons.addStretch ()

        # Main content area

        # TODO: save & restore window size & pos
        self.resize (1000, 900)


    def refreshUi (self):
        if not self.board:
            self.bPicture.setEnabled (False)
            self.bADC.setEnabled (False)
            self.bBattery.setEnabled (False)
            self.bTelemetry.setEnabled (False)
            self.bOSD.setEnabled (False)
            #self.bScreens.setEnabled (False)
            self.bFirmware.setEnabled (True)
            self.bConnect.setEnabled (True)
            #self.switchTo ()


def main ():
    win = MainWindow ()
    win.show ()

    sys.exit (app.exec_ ())

if __name__ == '__main__':
    main ()
