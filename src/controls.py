# -*- coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *


__all__ = ['Control', 'BoolControl', 'FloatControl', 'EnumControl', 'IntControl', 'StrControl']


class Control (QObject):

    changed = Signal ()

    def __init__ (self, option, parent):
        super (Control, self).__init__ (parent)
        self.option = option
        self.field = QVBoxLayout ()
        self.setupUi ()

    def setupUi (self):
        self.input.setDisabled (self.option.readonly)
        l = QHBoxLayout ()
        l.addWidget (self.input)
        l.addStretch ()
        self.field.addLayout (l)
        if self.option.description and self.option.description != self.option.name:
            self.hint = QLabel (_(self.option.description))
            self.hint.setStyleSheet ('padding-bottom: 8px; color: %s' % self.hint.palette ().color (QPalette.Shadow).name ())
            self.field.addWidget (self.hint)

    def onChanged (self):
        self.save ()
        self.changed.emit ()


class BoolControl (Control):

    def setupUi (self):
        self.label = None
        self.input = QCheckBox (self.option.name, self.parent ())
        self.input.setToolTip (self.option.description)
        self.input.stateChanged.connect (self.onChanged)
        super (BoolControl, self).setupUi ()

    def load (self):
        self.input.setChecked (self.option.value)

    def save (self):
        self.option.value = self.input.isChecked ()


class FloatControl (Control):

    def setupUi (self):
        self.label = QLabel (self.option.name, self.parent ())
        self.input = QDoubleSpinBox (self.parent ())
        self.input.setSingleStep (0.1)
        self.input.setToolTip (self.option.description)
        self.input.valueChanged.connect (self.onChanged)
        super (FloatControl, self).setupUi ()

    def load (self):
        self.input.setValue (self.option.value)

    def save (self):
        self.option.value = self.input.value ()


class EnumControl (Control):

    def setupUi (self):
        self.label = QLabel (self.option.name, self.parent ())
        self.input = QComboBox (self.parent ())
        self.index = {}
        for i, (idx, item) in enumerate (self.option.items.items ()):
            self.input.addItem (item, idx)
            self.index [idx] = i
        self.input.setToolTip (self.option.description)
        self.input.currentIndexChanged.connect (self.onChanged)
        super (EnumControl, self).setupUi ()

    def load (self):
        try:
            self.input.setCurrentIndex (self.index [self.option.value])
        except:
            self.input.setCurrentIndex (0)

    def save (self):
        self.option.value = self.input.itemData (self.input.currentIndex ())


class IntControl (Control):

    def setupUi (self):
        self.label = QLabel (self.option.name, self.parent ())
        self.input = QSpinBox (self.parent ())
        self.input.setMinimum (self.min ())
        self.input.setMaximum (self.max ())
        self.input.setToolTip (self.option.description)
        self.input.valueChanged.connect (self.onChanged)
        super (IntControl, self).setupUi ()

    _bounds = {
        'uint8': (0x00, 0xff),
        'uint16': (0x00, 0xff),
    }

    def min (self):
        if self.option.min is not None:
            return self.option.min
        return self._bounds [self.option.type][0]

    def max (self):
        if self.option.max is not None:
            return self.option.max
        return self._bounds [self.option.type][1]

    def load (self):
        self.input.setValue (self.option.value)

    def save (self):
        self.option.value = self.input.value ()


class StrControl (Control):

    def setupUi (self):
        self.label = QLabel (self.option.name, self.parent ())
        self.input = QLineEdit (self.parent ())
        self.input.setMaxLength (self.option.length)
        self.input.setToolTip (self.option.description)
        self.input.editingFinished.connect (lambda: self.changed.emit ())
        super (StrControl, self).setupUi ()

    def load (self):
        self.input.setText (self.option.value)

    def save (self):
        self.option.value = self.input.text ()
