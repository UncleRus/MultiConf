# -*- coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *
import ui
import stk500
import qboard
from settings import settings
from storage import storage
from hw.options import OptionsMap
import traceback


class FirmwareUpload (ui.AsyncProcess):

    def __init__ (self, hexFilename, fontFilename, parent):
        super (FirmwareUpload, self).__init__ (self.upload, parent, True)

        self.fontFilename = fontFilename
        self.hexFilename = hexFilename

        self.board = stk500.Arduino (self)
        self.board.errorOccured.connect (self.onErrorOccured)
        self.board.changed.connect (self.onStateChanged)
        self.board.progressUpdated.connect (self.onProgressUpdated)

        self.osd = qboard.QBoard (self)
        self.osd.changed.connect (self.onStateChanged)
        self.osd.progressUpdated.connect (self.onProgressUpdated)
        self.osd.timeoutOccured.connect (lambda: self.onErrorOccured (_('Timeout')))
        self.osd.errorOccured.connect (self.onErrorOccured)

    def onStateChanged (self, state):
        print 'State changed!', state
        self.changed.emit (state)

    def onProgressUpdated (self, percentage):
        self.progressUpdated.emit (percentage)

    def onErrorOccured (self, error):
        traceback.print_exc ()
        self.error = True
        self.errorOccured.emit (error)

    def upload (self):
        self.bannerUpdated.emit (_('Press reset button on MinimOSD'))
        if not self.board.open (settings.port, settings.stkBaudrate):
            return
        self.bannerUpdated.emit (_('Please wait'))
        signature = self.board.readSignature ()
        if signature != settings.chipSignature:
            raise RuntimeError (_('Invalid chip signature'))
        self.board.uploadHex (open (self.hexFilename, 'rb'))
        self.board.close ()

        self.bannerUpdated.emit (_('Firmware was uploaded successfully'))

        if self.fontFilename:
            self.bannerUpdated.emit (_('Connecting to MultiOSD...'))
            self.osd.connectBoard ()
            self.bannerUpdated.emit (_('Please wait'))
            self.osd.uploadFont (self.fontFilename)
            self.osd.disconnectBoard ()
            self.bannerUpdated.emit (_('Font was uploaded successfully'))

    def cancel (self):
        self.board.cancel ()
        self.errorOccured.emit (_('Cancelled'))


class FirmwareDialog (ui.ProcessDialog):

    def __init__ (self, hexFilename, fontFilename, parent = None):
        super (FirmwareDialog, self).__init__ (parent)
        self.hexFilename = hexFilename
        self.fontFilename = fontFilename
        self.setWindowTitle (_('Firmware upload'))

    def reset (self):
        super (FirmwareDialog, self).reset ()
        self.lBanner.setText (_('Connect MinimOSD and press "Continue"'))

    def start (self):
        self.process = FirmwareUpload (self.hexFilename, self.fontFilename, self)
        self.setupProcess ()
        self.process.start ()


class FirmwareWidget (ui.Scrollable):

    def __init__ (self, board, parent = None):
        super (FirmwareWidget, self).__init__ (parent)
        storage.updated.connect (self.showUpdates)
        self.maps = {}
        self.builds = []
        self.refresh ()
        self.button = ui.SquareButton ('Firmware', _('Firmware'), self)
        self.button.toggled.connect (lambda state: self.parent ().setCurrentWidget (self))
        self.board = board
        self.board.connectionChanged.connect (self.refreshButton)

    def setupUi (self):
        super (FirmwareWidget, self).setupUi ()
        self.lContent = QVBoxLayout (self.content)

        l = QHBoxLayout ()
        l.addWidget (QLabel (_('Latest firmware version:'), self.content))
        self.cbVersion = QComboBox (self)
        self.cbVersion.currentIndexChanged.connect (self.refreshSelected)
        self.cbVersion.setMinimumWidth (220)
        l.addWidget (self.cbVersion)
        self.bUpdate = QPushButton (_('Check for updates'), self.content)
        self.bUpdate.setIcon (QIcon (QPixmap (':res/icons/update.png')))
        self.bUpdate.clicked.connect (self.checkForUpdates)
        l.addWidget (self.bUpdate)
        l.addStretch ()
        self.lContent.addLayout (l)

        self.gbBuilds = QGroupBox (_('Firmware build'), self.content)
        self.lBuilds = QVBoxLayout (self.gbBuilds)
        self.lContent.addWidget (self.gbBuilds)

        l = QHBoxLayout ()
        self.bUpload = QPushButton (_('Upload firmware'), self.content)
        self.bUpload.setIcon (QIcon (QPixmap (':res/icons/upload.png')))
        self.bUpload.setEnabled (False)
        self.bUpload.clicked.connect (self.onUpload)
        l.addWidget (self.bUpload)
        l.addStretch ()
        self.lContent.addLayout (l)

        self.lContent.addStretch ()

    def refreshButton (self, state):
        self.button.setEnabled (not state)

    def refresh (self):
        self.cbVersion.clear ()
        self.cbVersion.addItems (['%s / %s' % (rel ["name"], rel ["published_at"]) for rel in storage.releases])
        self.cbVersion.setCurrentIndex (-1 if storage.isEmpty () else 0)

    def showUpdates (self, updated):
        if updated:
            self.refresh ()
        QMessageBox.information (self, _('Result'), _('Updates are found') if updated else _('No updates were found.'))

    def refreshSelected (self):
        del self.builds [:]
        self.productName = None
        QWidget ().setLayout (self.lBuilds)
        self.lBuilds = QFormLayout (self.gbBuilds)

        if storage.isEmpty () or self.cbVersion.currentIndex () < 0:
            return

        map = OptionsMap (storage.releases [self.cbVersion.currentIndex ()]['struct'])

        product = map.struct ['product']
        self.productName = product ['name']
        self.productVersion = product ['version']
        for build in product ['builds']:
            b = QRadioButton (' + '.join (build), self.gbBuilds)
            self.lBuilds.addWidget (b)
            self.builds.append (b)
            b.clicked.connect (self.onBuildSelected)

    def onBuildSelected (self):
        self.bUpload.setEnabled (True)

    def checkForUpdates (self):
        storage.update ()

    def onUpload (self):
        for i, btn in enumerate (self.builds):
            if btn.isChecked ():
                hex = storage.getHex (self.cbVersion.currentIndex (), i)
                mcm = storage.getFont (self.cbVersion.currentIndex ())
                if hex and mcm:
                    FirmwareDialog (hex, mcm, self).exec_ ()
                return

