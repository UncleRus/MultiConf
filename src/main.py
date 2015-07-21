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
import qboard
import hw
#import screens


#===============================================================================
# Main window
#===============================================================================

class MainWindow (QWidget):

    configPages = ('Telemetry', 'Picture', 'ADC', 'Battery', 'OSD')

    padding = 22

    def __init__ (self):
        super (MainWindow, self).__init__ ()
        self.board = qboard.QBoard (self)
        self.board.changed.connect (self.updateState)
        self.board.connectionChanged.connect (self.updateConnectionState)
        self.board.errorOccured.connect (self.showError)
        self.setupUi ()
        storage.updated.connect (self.updateConnectButton)
        self.updateConnectButton ()
        #self.refreshUi ()

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
        self.content.board = self.board
        self.lMain.addWidget (self.content)

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
            page = config.ConfigWidget (name, self.board, self.content)
            self.content.addWidget (page)
            lButtons.addWidget (page.button)
            self.pages.append (page)
        #lButtons.addWidget (self.bScreens)
        lButtons.addStretch ()

        self.firmwarePage = firmware.FirmwareWidget (self.board, self.content)
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
        def changePort ():
            try:
                settings.port = utils.ports [self.cbPort.currentIndex ()]
                print settings.port
            except IndexError:
                pass
        lPort.addWidget (QLabel (_('Port:'), self.pButtons))
        self.cbPort = QComboBox (self)
        self.cbPort.addItems (utils.ports)
        self.cbPort.currentIndexChanged.connect (changePort)
        try:
            index = utils.ports.index (settings.port)
        except ValueError:
            index = 0
        self.cbPort.setCurrentIndex (index)
        lPort.addWidget (self.cbPort)
        lPort.addStretch ()
        lButtons.addLayout (lPort)

        # TODO: save & restore window size & pos
        self.resize (900, 600)

        self.firmwarePage.button.click ()

    def updateState (self, state):
        self.lStatus.setText (state)
        QApplication.processEvents ()

    def updateConnectionState (self, state):
        self.lConnected.setText (_('Connected') if state else _('Disconnected'))
        self.cbPort.setEnabled (not state)
        self.bFirmware.setEnabled (not state)

        if state:
            self.bConnect.setText (_('Disconnect'))
            self.bConnect.setName ('Disconnect')
            self.configPages [0].button.click ()
        else:
            self.bFirmware.toggle ()
            self.bConnect.setText (_('Connect'))
            self.bConnect.setName ('Connect')

    def updateProgress (self, percentage):
        self.pbProgress.setValue (percentage)
        QApplication.processEvents ()

    def updateConnectButton (self):
        self.bConnect.setEnabled (not storage.isEmpty ())

    def boardConnect (self):
        if self.board.isConnected ():
            return self.boardDisconnect ()
        self.board.connectBoard ()

    def boardDisconnect (self):
        self.board.disconnectBoard ()

    def showError (self, error):
        QMessageBox.critical (self, _('Error'), error)


def main ():
    win = MainWindow ()
    win.show ()

    sys.exit (app.exec_ ())

if __name__ == '__main__':
    main ()
