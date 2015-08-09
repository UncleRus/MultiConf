# -*- coding: utf-8 -*-

from PySide.QtCore import QSettings
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

