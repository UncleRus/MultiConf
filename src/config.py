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

    stateChanged = Signal ()

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
            ctrl.stateChanged.connect (self.onChanged)
            self.controls.append (ctrl)
            self.lContent.addRow (ctrl.label, ctrl.input)

    def onChanged (self):
        self.stateChanged.emit ()
