#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide.QtGui import *
from PySide.QtCore import *
import sys
import gettext
import os.path as osp

import resources_rc #@UnusedImport

#===============================================================================
# Init
#===============================================================================

app = QApplication (sys.argv)

app.setOrganizationName ('UncleRus')
app.setApplicationName ('MultiOSD configurator')
app.setApplicationVersion ('0.2')

gettext.install ('MultiConf', osp.join (app.applicationDirPath (), 'locales'), unicode = True)


#===============================================================================
# local imports
#===============================================================================
from settings import settings
from storage import storage
import utils
import ui
import firmware
import config
import multiosd
#import screens


#===============================================================================
# Connect window
#===============================================================================

class ConnectWindow (QDialog):

    def __init__ (self, osd, parent):
        super (ConnectWindow, self).__init__ (parent, Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowMinMaxButtonsHint | Qt.Window)

        self.osd = osd

        self.osd.connectionChanged.connect (self.refresh)
        self.osd.timeoutOccured.connect (self.onTimeout)
        self.osd.errorOccured.connect (self.close)

        self.setupUi ()
        offs = parent.size () / 2 - self.size () / 2
        self.move (parent.pos ().x () + offs.width (), parent.pos ().y () + offs.height ())

    def setupUi (self):
        self.setWindowTitle (_('MinimOSD connection'))
        l = QVBoxLayout (self)
        self.lMessage = QLabel (self)
        self.lMessage.setStyleSheet ('font-size: 12pt; padding-top: 16px; padding-bottom: 16px;')
        l.addWidget (self.lMessage)
        l.addStretch ()
        bl = QHBoxLayout ()
        bl.addStretch ()
        self.bAgain = QPushButton (_('Try again'), self)
        self.bAgain.clicked.connect (self.tryAgain)
        self.bCancel = QPushButton (_('Cancel'), self)
        self.bCancel.clicked.connect (self.close)
        bl.addWidget (self.bAgain)
        bl.addWidget (self.bCancel)
        l.addLayout (bl)
        self.resize (300, 100)

        self.setWindowModality (Qt.ApplicationModal)

    def refresh (self, state):
        self.connected = state
        if state is None:
            self.bAgain.setEnabled (False)
            self.bCancel.setEnabled (False)
            self.lMessage.setText (_('Connect MinimOSD and press reset...'))
            return
        if state:
            self.close ()
        else:
            self.onTimeout ()

    def updateState (self, state):
        self.lMessage.setText (state)

    def onTimeout (self):
        self.bAgain.setEnabled (True)
        self.bCancel.setEnabled (True)

    def tryAgain (self):
        self.refresh (None)
        self.osd.connectBoard ()

    def run (self):
        self.show ()
        self.tryAgain ()


#===============================================================================
# Main window
#===============================================================================

class MainWindow (QWidget):

    configPages = ('Telemetry', 'Picture', 'ADC', 'Battery', 'OSD')

    padding = 22

    def __init__ (self, application):
        super (MainWindow, self).__init__ ()

        application.aboutToQuit.connect (self.shutdown)

        self.ports = None
        self.firmwarePage = None

        self.osd = multiosd.OSDProcess (self)
        self.osd.connectionChanged.connect (self.updateConnectionState)
        self.osd.errorOccured.connect (self.showError)
        self.osd.stateChanged.connect (self.updateState)
        self.osd.progressUpdated.connect (lambda x: self.pbProgress.setValue (x))
        self.osd.start ()

        self.setupActions ()

        self.setupUi ()
        storage.updated.connect (self.updateConnectButton)
        self.updateConnectButton ()

    def setupActions (self):
        self.aWriteEeprom = QAction (QIcon (QPixmap (':/res/icons/save.png')), _('Write EEPROM'), self)
        self.aWriteEeprom.activated.connect (self.writeEeprom)
        self.aWriteEeprom.setEnabled (False)
        self.aReadEeprom = QAction (QIcon (QPixmap (':/res/icons/refresh.png')), _('Read EEPROM'), self)
        self.aReadEeprom.activated.connect (self.readEeprom)
        self.aReadEeprom.setEnabled (False)

    def shutdown (self):
        self.osd.quit ()
        self.osd.wait ()
        self.osd.deleteLater ()

    def setupUi (self):
        self.setWindowTitle (u'%s v.%s' % (QApplication.applicationName (), QApplication.applicationVersion ()))
        self.lMain = QVBoxLayout (self)
        self.lMain.setContentsMargins (2, 2, 2, 2)

        # buttons panel
        self.pButtons = QFrame (self)
        self.pButtons.setMinimumHeight (ui.SquareButton.defaultSize.height () + self.padding)
        self.pButtons.setMaximumHeight (self.pButtons.minimumHeight ())
        self.pButtons.setFrameStyle (QFrame.StyledPanel | QFrame.Sunken)
        lButtons = QHBoxLayout (self.pButtons)
        self.lMain.addWidget (self.pButtons)

        # content
        self.content = QStackedWidget (self)
        self.content.currentChanged.connect (self.onPageChanged)
        self.content.board = self.osd
        self.lMain.addWidget (self.content)

        # tools
        self.pTools = QFrame (self)
        self.pTools.setFrameStyle (QFrame.StyledPanel)
        lTools = QHBoxLayout (self.pTools)
        self.lBoardInfo = QLabel (self.pTools)
        self.lBoardInfo.setStyleSheet ('color: %s' % self.lBoardInfo.palette ().color (QPalette.Mid).name ())
        lTools.addWidget (self.lBoardInfo)
        lTools.addStretch ()
        self.lMain.addWidget (self.pTools)
        self.pTools.hide ()

        # eeprom buttons
        lTools.addStretch ()
        self.bEepromWrite = QToolButton (self.pTools)
        self.bEepromWrite.setDefaultAction (self.aWriteEeprom)
        self.bEepromWrite.setToolButtonStyle (Qt.ToolButtonTextBesideIcon)
        #self.bEepromWrite.setSizePolicy (QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        lTools.addWidget (self.bEepromWrite)
        self.bEepromRead = QToolButton (self.pTools)
        self.bEepromRead.setDefaultAction (self.aReadEeprom)
        self.bEepromRead.setToolButtonStyle (Qt.ToolButtonTextBesideIcon)
        #self.bEepromRead.setSizePolicy (QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        lTools.addWidget (self.bEepromRead)

        # stausbar
        lStatus = QHBoxLayout ()
        cont = QWidget (self)
        cont.setMaximumWidth (210)
        lCont = QHBoxLayout (cont)
        lCont.setContentsMargins (0, 0, 0, 0)
        lStatus.addWidget (cont)
        self.lMain.addLayout (lStatus)
        self.lConnected = ui.FramedLabel (_('Disconnected'), parent = cont)
        lCont.addWidget (self.lConnected)
        self.pbProgress = QProgressBar (cont)
        self.pbProgress.setMinimumWidth (100)
        self.pbProgress.setMaximumWidth (150)
        self.pbProgress.setMaximumHeight (self.lConnected.height () - 8)
        lCont.addWidget (self.pbProgress)
        self.lStatus = QLabel (self)
        self.lStatus.setAlignment (Qt.AlignLeft | Qt.AlignVCenter)
        lStatus.addWidget (self.lStatus)
        lStatus.addStretch ()

        # config pages
        self.pages = []
        for name in self.configPages:
            page = config.ConfigWidget (name, self.osd, self.content)
            self.content.addWidget (page)
            lButtons.addWidget (page.button)
            self.pages.append (page)
        #lButtons.addWidget (self.bScreens)
        lButtons.addStretch ()

        self.firmwarePage = firmware.FirmwareWidget (self.osd, self.content)
        self.firmwarePage.button.setParent (self.pButtons)
        lButtons.addWidget (self.firmwarePage.button)
        self.content.addWidget (self.firmwarePage)

        # Connect/Disconnect button
        self.bConnect = ui.SquareButton ('Connect', _('Connect'), self.pButtons)
        self.bConnect.setCheckable (False)
        self.bConnect.clicked.connect (self.boardConnect)
        lButtons.addWidget (self.bConnect)

        # port
        lPort = QVBoxLayout ()
        lPort.addStretch ()

        lPort.addWidget (QLabel (_('Port:'), self.pButtons))
        self.cbPort = QComboBox (self)
        self.cbPort.currentIndexChanged.connect (self.changePort)
        self.refreshPorts ()
        lPort.addWidget (self.cbPort)
        lPort.addStretch ()
        lButtons.addLayout (lPort)

        # TODO: save & restore window size & pos
        self.resize (900, 600)

        self.firmwarePage.button.click ()

    def changePort (self):
        try:
            settings.port = self.ports [self.cbPort.currentIndex ()]
        except IndexError:
            pass

    def refreshPorts (self):
        ports = utils.serialPorts ()
        if ports == self.ports:
            return
        self.ports = ports

        self.cbPort.currentIndexChanged.disconnect (self.changePort)
        self.cbPort.clear ()
        self.cbPort.addItems (self.ports)
        self.cbPort.currentIndexChanged.connect (self.changePort)
        try:
            index = self.ports.index (settings.port)
        except ValueError:
            index = 0
        self.cbPort.setCurrentIndex (index)
        self.changePort ()

    def onPageChanged (self, *args):
        self.pTools.setVisible (self.content.currentWidget () != self.firmwarePage)

    def updateState (self, state):
        self.lStatus.setText (state)

    def updateConnectionState (self, state):
        self.lConnected.setText (_('Connected') if state else _('Disconnected'))
        self.cbPort.setEnabled (not state)

        if state:
            self.bConnect.setText (_('Disconnect'))
            self.bConnect.setName ('Disconnect')
            self.pages [0].button.toggle ()
            self.lBoardInfo.setText (_(u'v.%s, modules: %s') % (self.osd.osd.version, ', '.join (self.osd.osd.modules)))
        else:
            self.firmwarePage.button.toggle ()
            self.bConnect.setText (_('Connect'))
            self.bConnect.setName ('Connect')
            self.lBoardInfo.setText ()
        self.firmwarePage.button.setEnabled (not state)

        self.aWriteEeprom.setEnabled (state)
        self.aReadEeprom.setEnabled (state)

    def updateProgress (self, percentage):
        self.pbProgress.setValue (percentage)

    def updateConnectButton (self):
        self.bConnect.setEnabled (not storage.isEmpty ())

    def boardConnect (self):
        if self.osd.isConnected ():
            self.osd.disconnectBoard ()
        else:
            win = ConnectWindow (self.osd, self)
            win.run ()

    def showError (self, error):
        QMessageBox.critical (self, _('Error'), error)

    def writeEeprom (self):
        pass

    def readEeprom (self):
        pass


def main ():
    win = MainWindow (app)
    win.show ()

    sys.exit (app.exec_ ())

if __name__ == '__main__':
    main ()
