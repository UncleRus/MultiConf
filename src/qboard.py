#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide.QtCore import *
import hw
from settings import settings
from storage import storage
import traceback
from PySide.QtGui import QApplication


class QBoard (QObject):

    timeoutOccured = Signal ()
    connectionChanged = Signal (bool)
    errorOccured = Signal (str)
    changed = Signal (str)
    progressUpdated = Signal (int)

    def __init__ (self, parent = None):
        super (QBoard, self).__init__ (parent)
        self.eeprom = None
        self.board = hw.Board (settings.port, settings.baudrate)
        self.version = None
        self.modules = None
        self.panels = None
        self.options = hw.OptionsMap ()

    def updateProgress (self, maxValue):
        def wrapped (value):
            self.progressUpdated.emit (int (100.0 * value / maxValue))
        return wrapped

    def isConnected (self):
        return self.board.connected

    def onError (self, e):
        traceback.print_exc ()
        msg = str (e).decode ('utf-8')
        self.errorOccured.emit (msg)
        self.changed.emit (_('Error: %s') % msg)

    def connectBoard (self):
        if self.isConnected ():
            self.disconnectBoard ()
        try:
            QApplication.setOverrideCursor (Qt.WaitCursor)
            self.changed.emit (_('Connecting...'))
            QApplication.processEvents ()
            self.board.connect (timeout = settings.connectionTimeout)
            self.version, self.modules, self.panels = self.board.info ()
            self.eeprom = self.board.eeprom_read (self.updateProgress (self.board.EEPROM_SIZE))
            self.options.parse (storage.getMap (self.version))
            self.options.load (self.eeprom)
            self.changed.emit (_('Connected.'))
            self.connectionChanged.emit (True)
        except hw.TimeoutError:
            self.changed.emit (_('Timeout.'))
            self.timeoutOccured.emit ()
        except Exception as e:
            traceback.print_exc ()
            self.disconnectBoard ()
            self.onError (e)
        QApplication.restoreOverrideCursor ()
        QApplication.processEvents ()

    def disconnectBoard (self):
        if self.isConnected ():
            try:
                self.board.disconnect ()
                self.connectionChanged.emit (False)
                self.changed.emit (_('Disconnected.'))
            except Exception as e:
                self.onError (e)

    def saveOptions (self):
        if not self.isConnected ():
            return

        try:
            self.changed.emit (_('Writing EEPROM...'))
            self.options.save (self.eeprom)
            self.board.eeprom_write (self.eeprom, self.updateProgress (self.board.EEPROM_SIZE))

            self.changed.emit (_('Reading EEPROM...'))
            eeprom = self.board.eeprom_read (self.updateProgress (self.board.EEPROM_SIZE))
            if self.eeprom != eeprom:
                raise IOError (_('EEPROM verification failed'))

            self.changed.emit (_('Done.'))
        except Exception as e:
            self.onError (e)

    def uploadFont (self, filename = None):
        try:
            self.changed.emit (_('Writing font...'))
            if not filename:
                filename = storage.getFont (self.version)
            if not filename:
                raise RuntimeError (_('Cannot find font'))
            self.board.font_upload (open (filename, 'rb'), self.updateProgress (0x4000))
            self.changed.emit (_('Done.'))
        except Exception as e:
            self.onError (e)

    def downloadFont (self, filename):
        try:
            self.changed.emit (_('Reading font...'))
            self.board.font_download (open (filename, 'wb'), self.updateProgress (0x4000))
            self.changed.emit (_('Done.'))
        except Exception as e:
            self.onError (e)

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
