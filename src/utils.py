# -*- coding: utf-8 -*-

from PySide.QtCore import QSettings, QThread, Signal
from PySide.QtGui import QApplication
import ast
import sys
import glob
import serial


class Setting (object):

    settings = None
    _types = {
        bool: lambda x: x.lower () in ('true', 'yes', '1') if isinstance (x, basestring) else x,
        dict: lambda x: ast.literal_eval (x)
    }

    @classmethod
    def init (cls):
        if not cls.settings:
            cls.settings = QSettings ()
        print cls.settings.fileName ()

    def __init__ (self, key, default = None, type_ = None):
        self.init ()
        self.key = key
        self.default = default
        self.type = type_ or type (default)
        if not self.type:
            raise TypeError ('Undefined option type')

    def __get__ (self, owner, cls):
        return self._types.get (self.type, self.type) (self.settings.value (self.key, self.default))

    def __set__ (self, owner, value):
        self.settings.setValue (self.key, value)


class SimpleThread (QThread):

    errorOccured = Signal (str)

    def __init__ (self, target, args = (), kwargs = {}, parent = None):
        super (SimpleThread, self).__init__ (parent)
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.running = False

    def runWait (self):
        self.running = True
        self.start ()
        while self.running:
            QApplication.processEvents ()
        self.deleteLater ()
        return self.result

    def run (self):
        print 'SimpleThread run'
        try:
            self.result = self.target (*self.args, **self.kwargs)
        except Exception as e:
            self.errorOccured.emit (str (e).decode ('utf-8'))
        self.running = False


callAsync = lambda func, *args, **kwargs: SimpleThread (target = func, args = args, kwargs = kwargs).runWait ()


def serialPorts ():
    if sys.platform.startswith ('win'):
        ports = ['COM' + str (i + 1) for i in range (256)]

    elif sys.platform.startswith ('linux') or sys.platform.startswith ('cygwin'):
        # this is to exclude your current terminal "/dev/tty"
        ports = glob.glob ('/dev/tty[A-Za-z]*')

    elif sys.platform.startswith ('darwin'):
        ports = glob.glob ('/dev/tty.*')

    else:
        raise EnvironmentError ('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial (port)
            s.close ()
            result.append (port)
        except (OSError, serial.SerialException):
            pass
    return result

ports = serialPorts ()
