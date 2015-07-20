#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide.QtGui import *
from PySide.QtCore import *
import sys
import resources_rc #@UnusedImport


#===============================================================================
# Init
#===============================================================================

app = QApplication (sys.argv)

app.setOrganizationName ('UncleRus')
app.setApplicationName ('MultiOSD configurator')
app.setApplicationVersion ('0.2')


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

    padding = 22

    def __init__ (self):
        super (MainWindow, self).__init__ ()
        self.board = qboard.QBoard (self)
        self.board.stateChanged.connect (self.updateState)
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
        self.pButtons.setAutoFillBackground (True)
        self.pButtons.setBackgroundRole (QPalette.Mid)
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

        self.lConnected = ui.FramedLabel (self.tr ('Disconnected'), parent = cont)
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

        # config buttons
        self.bPicture = ui.PageButton ('Picture', self.tr ('Picture'), config.ConfigWidget, self.content, self.pButtons)
        lButtons.addWidget (self.bPicture)
        self.bADC = ui.PageButton ('ADC', self.tr ('ADC'), config.ConfigWidget, self.content, self.pButtons)
        lButtons.addWidget (self.bADC)
        self.bBattery = ui.PageButton ('Battery', self.tr ('Battery'), config.ConfigWidget, self.content, self.pButtons)
        lButtons.addWidget (self.bBattery)
        self.bTelemetry = ui.PageButton ('Telemetry', self.tr ('Telemetry'), config.ConfigWidget, self.content, self.pButtons)
        lButtons.addWidget (self.bTelemetry)
        self.bOSD = ui.PageButton ('OSD', self.tr ('OSD'), config.ConfigWidget, self.content, self.pButtons)
        lButtons.addWidget (self.bOSD)
        self.bScreens = ui.PageButton ('Screens', self.tr ('Screens'), lambda *args: None, self.content, self.pButtons)
        lButtons.addWidget (self.bScreens)
        lButtons.addStretch ()

        self.configButtons = (self.bPicture, self.bADC, self.bBattery, self.bTelemetry, self.bOSD, self.bScreens)

        # Firmware button
        self.bFirmware = ui.PageButton ('Firmware', self.tr ('Firmware'), firmware.FirmwareWidget, self.content, self.pButtons)
        self.bFirmware.init ()
        lButtons.addWidget (self.bFirmware)

        # Connect/Disconnect button
        self.bConnect = ui.SquareButton ('Connect', self.tr ('Connect'), self.pButtons)
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
        lPort.addWidget (QLabel (self.tr ('Port:'), self.pButtons))
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

        self.bFirmware.setChecked (True)

    def updateState (self, state):
        self.lStatus.setText (state)
        QApplication.processEvents ()

    def updateConnectionState (self, state):
        self.lConnected.setText (self.tr ('Connected') if state else self.tr ('Disconnected'))
        self.bFirmware.setEnabled (not state)
        if state:
            self.bConnect.setText (self.tr ('Disconnect'))
            self.bConnect.setName ('Disconnect')
        else:
            self.bConnect.setText (self.tr ('Connect'))
            self.bConnect.setName ('Connect')

        self.board.map = hw.OptionsMap (storage.getMap (self.board.version))
        self.board.map.load (self.board.eeprom)

        for btn in self.configButtons:
            if state:
                btn.init ()
            btn.setEnabled (state)

        QApplication.processEvents ()

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
        QMessageBox.critical (self, self.tr ('Error'), error)


def main ():
    win = MainWindow ()
    win.show ()

    sys.exit (app.exec_ ())

if __name__ == '__main__':
    main ()
