#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *


import hw
from settings import settings
from storage import storage


def command (func):
    def wrapper (*args, **kwargs):
        self = args [0]
        try:
            if not self.isConnected ():
                raise IOError (_('Board is not connected'))
            return func (*args, **kwargs)
        except Exception as e:
            self.setError (e)
    return wrapper


class MultiOSD (QObject):

    timeoutOccured = Signal ()
    connectionChanged = Signal (bool)
    errorOccured = Signal (str)
    stateChanged = Signal (str)
    progressUpdated = Signal (int)

    def __init__ (self, parent = None):
        super (MultiOSD, self).__init__ (parent)
        self.board = hw.Board (settings.port, settings.baudrate)
        self.version = None
        self.modules = None
        self.panels = None
        self.eeprom = None
        self.options = hw.OptionsMap ()

    def setError (self, e):
        self.stateChanged.emit (_('Error'))
        self.errorOccured.emit (str (e).decode ('utf-8'))

    def updateProgress (self, maxValue):
        def wrapped (value):
            self.progressUpdated.emit (int (100.0 * value / maxValue))
        return wrapped

    def isConnected (self):
        return self.board.connected

    def connectBoard (self):
        if self.isConnected ():
            self.disconnectBoard ()
        try:
            self.stateChanged.emit (_('Connecting...'))
            self.board.port = settings.port
            self.board.connect (timeout = settings.connectionTimeout)
            self.version, self.modules, self.panels = self.board.info ()
            self.eeprom = self.board.eeprom_read (self.updateProgress (self.board.EEPROM_SIZE))
            self.options.parse (storage.getMap (self.version))
            self.options.load (self.eeprom)
            self.stateChanged.emit (_('Connected.'))
            self.connectionChanged.emit (True)
        except hw.TimeoutError:
            self.stateChanged.emit (_('Timeout.'))
            self.timeoutOccured.emit ()
        except Exception as e:
            self.disconnectBoard ()
            self.setError (e)

    @command
    def disconnectBoard (self):
        if not self.isConnected ():
            return
        self.board.disconnect ()
        self.connectionChanged.emit (False)
        self.stateChanged.emit (_('Disconnected.'))

    @command
    def saveOptions (self):
        self.stateChanged.emit (_('Writing EEPROM...'))
        self.options.save (self.eeprom)
        self.board.eeprom_write (self.eeprom, self.updateProgress (self.board.EEPROM_SIZE))

        self.stateChanged.emit (_('Reading EEPROM...'))
        eeprom = self.board.eeprom_read (self.updateProgress (self.board.EEPROM_SIZE))
        if self.eeprom != eeprom:
            raise IOError (_('EEPROM verification failed'))

        self.stateChanged.emit (_('Done.'))

    @command
    def uploadFont (self, filename = None):
        self.stateChanged.emit (_('Writing font...'))
        if not filename:
            filename = storage.getFont (self.version)
        if not filename:
            raise RuntimeError (_('Cannot find font'))
        self.board.font_upload (open (filename, 'rb'), self.updateProgress (0x4000))
        self.stateChanged.emit (_('Done.'))

    @command
    def downloadFont (self, filename):
        self.stateChanged.emit (_('Reading font...'))
        self.board.font_download (open (filename, 'wb'), self.updateProgress (0x4000))
        self.stateChanged.emit (_('Done.'))

    def port (self):
        return self.board.port

    def setPort (self, value):
        if self.board.port == value:
            return
        if self.isConnected ():
            self.disconnectBoard ()
        self.board.port = value

    def baudrate (self):
        return self.board.baudrate

    def setBaudrate (self, value):
        if self.board.baudrate == value:
            return
        if self.isConnected ():
            self.disconnectBoard ()
        self.board.baudrate = value


class OSDProcess (QThread):

    timeoutOccured = Signal ()
    connectionChanged = Signal (bool)
    errorOccured = Signal (str)
    stateChanged = Signal (str)
    progressUpdated = Signal (int)

    doConnectBoard = Signal ()
    doDisconnectBoard = Signal ()
    doSaveOptions = Signal ()
    doUploadFont = Signal (str)
    doDownloadFont = Signal (str)
    doSetPort = Signal (str)
    doSetBaudrate = Signal (int)

    def __init__ (self, parent = None):
        super (OSDProcess, self).__init__ (parent)
        self.finished.connect (self.deleteLater)
        self.ready = False

    def run (self):
        self.osd = MultiOSD ()

        self.osd.timeoutOccured.connect (lambda: self.timeoutOccured.emit (), Qt.QueuedConnection)
        self.osd.connectionChanged.connect (lambda x: self.connectionChanged.emit (x), Qt.QueuedConnection)
        self.osd.errorOccured.connect (lambda x: self.errorOccured.emit (x), Qt.QueuedConnection)
        self.osd.stateChanged.connect (lambda x: self.stateChanged.emit (x), Qt.QueuedConnection)
        self.osd.progressUpdated.connect (lambda x: self.progressUpdated.emit (x), Qt.QueuedConnection)

        self.doConnectBoard.connect (self.osd.connectBoard, Qt.QueuedConnection)
        self.doDisconnectBoard.connect (self.osd.disconnectBoard, Qt.QueuedConnection)
        self.doSaveOptions.connect (self.osd.saveOptions, Qt.QueuedConnection)
        self.doUploadFont.connect (self.osd.uploadFont, Qt.QueuedConnection)
        self.doDownloadFont.connect (self.osd.downloadFont, Qt.QueuedConnection)
        self.doSetPort.connect (self.osd.setPort, Qt.QueuedConnection)
        self.doSetBaudrate.connect (self.osd.setBaudrate, Qt.QueuedConnection)

        self.ready = True
        self.exec_ ()

        self.osd.disconnectBoard ()
        self.osd.deleteLater ()

    def connectBoard (self):
        self.doConnectBoard.emit ()

    def disconnectBoard (self):
        self.doDisconnectBoard.emit ()

    def isConnected (self):
        return self.osd.isConnected ()

    def saveOptions (self):
        self.doSaveOptions.emit ()

    def uploadFont (self, *args, **kwargs):
        self.doUploadFont.emit (*args, **kwargs)

    def downloadFont (self, *args, **kwargs):
        self.doDownloadFont.emit (*args, **kwargs)

    def setPort (self, *args, **kwargs):
        self.doSetPort.emit (*args, **kwargs)

    def setBaudrate (self, *args, **kwargs):
        self.doSetBaudrate.emit (*args, **kwargs)
