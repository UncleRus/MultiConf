# -*- coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *
import os.path as osp
import controls
from utils import Setting


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


class ConfigWidget (Scrollable):

    _factories = {
        'bool': controls.BoolControl,
        'float': controls.FloatControl,
        'enum': controls.EnumControl,
        'uint8': controls.IntControl,
        'uint16': controls.IntControl,
        'str': controls.StrControl
    }

    changed = Signal ()

    def __init__ (self, name, parent):
        super (ConfigWidget, self).__init__ (parent)
        self.name = name
        self.controls = []
        self.lContent = QFormLayout (self.content)

        _map = self.parent ().board.map
        for optname in _map.struct ['map'][self.name]:
            opt = _map.map [optname]
            if not opt.section.enabled (self.parent ().board.modules):
                continue
            ctrl = self._factories [opt.type] (opt, self.content)
            ctrl.load ()
            ctrl.changed.connect (self.onChanged)
            self.controls.append (ctrl)
            self.lContent.addRow (ctrl.label, ctrl.input)

    def onChanged (self):
        self.changed.emit ()


class FirmwareWidget (Scrollable):

    startUpload = Signal ([str])

    dataPath = Setting ('dataPath', osp.join (QDesktopServices.storageLocation (QDesktopServices.DataLocation), QCoreApplication.applicationName ()))
    productName = Setting ('productName', 'MultiOSD')
    updateURL = Setting ('updateUrl', 'http://github/UncleRus-bla-bla')

    def __init__ (self, name, parent = None):
        super (FirmwareWidget, self).__init__ (parent)
        self.maps = {}
        self.builds = []
        print self.dataPath

    def setupUi (self):
        super (FirmwareWidget, self).setupUi ()
        self.lContent = QVBoxLayout (self.content)

        l = QHBoxLayout ()
        l.addWidget (QLabel ('Latest firmware version:', self.content))
        self.lblVersion = QLabel (self.content)
        l.addWidget (self.lblVersion)
        l.addStretch ()
        self.lContent.addLayout (l)

        self.gbBuilds = QGroupBox ('Firmware build', self.content)
        self.lBuilds = QVBoxLayout (self.gbBuilds)
        self.lContent.addWidget (self.gbBuilds)

        l = QHBoxLayout ()
        self.bUpload = QPushButton ('Upload firmware', self.content)
        self.bUpload.setEnabled (False)
        self.bUpload.clicked.connect (self.onUpload)
        l.addWidget (self.bUpload)
        l.addStretch ()
        self.lContent.addLayout (l)

        self.lContent.addStretch ()

    def refresh (self, map):
        self.clear ()
        product = map.struct ['product']
        self.productName = product ['name']
        self.productVersion = product ['version']
        self.lblVersion.setText ('<b>%s</b>' % product ['version'])
        for build in product ['builds']:
            b = QRadioButton (' + '.join (build), self.gbBuilds)
            self.lBuilds.addWidget (b)
            self.builds.append ((b, build))
            b.clicked.connect (self.onBuildSelected)

    def clear (self):
        del self.builds [:]
        self.productName = None
        QWidget ().setLayout (self.lBuilds)
        self.lBuilds = QFormLayout (self.gbBuilds)

    def onBuildSelected (self):
        self.bUpload.setEnabled (True)

    def onUpload (self):
        for btn, build in self.builds:
            if btn.isChecked ():
                self.startUpload.emit ('%s/%s_%s.hex' % (self.productVersion, self.productName, '_'.join ((b.lower () for b in build))))
                return


