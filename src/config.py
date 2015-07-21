# -*- coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *
import controls
import ui


class ConfigWidget (ui.Scrollable):

    _factories = {
        'bool': controls.BoolControl,
        'float': controls.FloatControl,
        'enum': controls.EnumControl,
        'uint8': controls.IntControl,
        'uint16': controls.IntControl,
        'str': controls.StrControl
    }

    changed = Signal ()

    def __init__ (self, name, board, parent):
        super (ConfigWidget, self).__init__ (parent)
        self.name = name
        self.lContent = None
        self.board = board
        self.board.connectionChanged.connect (self.refresh)
        self.controls = []
        self.button = ui.SquareButton (name, _(name))
        self.button.toggled.connect (lambda state: self.parent ().setCurrentWidget (self))
        self.refresh (False)

    def refresh (self, state):
        if not state:
            self.clear ()
        else:
            self.load ()
        self.button.setEnabled (not self.isEmpty ())

    def clear (self):
        for ctrl in self.controls:
            ctrl.deleteLater ()
        del self.controls [:]
        if self.lContent:
            QWidget ().setLayout (self.lContent)
        self.lContent = QFormLayout (self.content)

    def load (self):
        _map = self.board.map
        for optname in _map.struct ['map'][self.name]:
            opt = _map.map [optname]
            if not opt.section.enabled (self.board.modules):
                continue
            ctrl = self._factories [opt.type] (opt, self.content)
            ctrl.load ()
            ctrl.changed.connect (self.onChanged)
            self.controls.append (ctrl)
            self.lContent.addRow (ctrl.label, ctrl.input)

    def onChanged (self):
        self.changed.emit ()

    def isEmpty (self):
        return not bool (self.controls)
