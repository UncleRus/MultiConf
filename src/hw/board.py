# -*- coding: utf-8 -*-

import re
import time
from serial import Serial


__all__ = ['TimeoutError', 'Board']


def needs_connection (func):
    def _wrapped (*args, **kwargs):
        if not args [0].connected:
            raise IOError ('Board not found')
        return func (*args, **kwargs)
    return _wrapped


class TimeoutError (IOError):
    pass


class Board (object):

    EEPROM_SIZE = 0x400

    osd_prompt = b'osd#'

    info_regexp = re.compile (r'([A-Z]+):\s*(.*)?')

    def __init__ (self, port = '/dev/ttyUSB0', baudrate = 57600):
        self.port = port
        self.baudrate = baudrate
        self.connected = False

    def connect (self, timeout = 5):
        if self.connected:
            self.disconnect ()

        try:
            self.serial = Serial (self.port, self.baudrate, timeout = 1.0)

            _stop_at = time.time () + timeout

            while True:
                line = self.serial.readline ().strip ()
                if line == b'READY':
                    break
                if time.time () >= _stop_at:
                    raise TimeoutError ('Connection timeout')

            self.serial.write (b'config\r')
            while True:
                line = self.serial.readline ().strip ()
                if line == self.osd_prompt:
                    break

            self.connected = True
        except:
            self.serial.close ()
            raise

    def disconnect (self):
        if not self.connected:
            return
        self.serial.close ()
        self.connected = False

    @needs_connection
    def execute (self, cmd):
        self.serial.write (b'%s\r' % cmd)
        echo = self.serial.readline ().strip ()
        if echo != cmd:
            raise IOError ('Invalid board response')

    @needs_connection
    def info (self):
        version = 0
        modules = []
        panels = []

        self.execute ('info')

        _pan = False
        for line in iter (lambda: self.serial.readline ().strip (), self.osd_prompt):
            if not line:
                continue

            if _pan:
                panels.append (line.split (':')[1].strip ())
                continue

            m = self.info_regexp.match (line)
            if not m:
                raise IOError ('Unknown info response')
            if m.group (1) == 'VERSION':
                version = m.group (2)
            elif m.group (1) == 'MODULES':
                modules = m.group (2).split (' ')
            elif m.group (1) == 'PANELS':
                _pan = True

        return (version, modules, panels)

    @needs_connection
    def eeprom_read (self, callback = None):
        self.execute ('eeprom r')
        res = bytearray ()
        for i in range (self.EEPROM_SIZE / 0x10):
            while self.serial.inWaiting () < 0x10:
                time.sleep (0.1)
            data = self.serial.read (0x10)
            res.extend (bytearray (data))
            if callback:
                callback (i * 0x10)
        self.serial.readline ()
        self.serial.readline ()
        return bytearray (res)

    @needs_connection
    def eeprom_write (self, data, callback = None):
        self.execute ('eeprom w')
        for i in range (self.EEPROM_SIZE / 0x10):
            self.serial.write (bytes (data [i:i + 0x10]))
            if callback:
                callback ((i + 1) * 0x10)
        self.serial.readline ()
        self.serial.readline ()
        self.serial.readline ()

    @needs_connection
    def font_upload (self, fp, callback = None):
        self.execute ('font u')
        for i in xrange (16385):
            line = fp.readline ()
            if not line:
                raise IOError ('Invalid file format')
            self.serial.write (line)
            if callback and i % 0x100 == 0:
                callback (i)
        self.serial.write (b'\r\r')

    @needs_connection
    def font_download (self, fp, callback = None):
        self.execute ('font d')
        for i in xrange (16385):
            line = self.serial.readline ().strip ()
            if line == self.osd_prompt:
                raise IOError ('Cannot download font')
            fp.write (line)
            fp.write (b'\r\n')
            if callback and i % 0x100 == 0:
                callback (i)

    @needs_connection
    def reboot (self):
        self.execute ('reboot')

    @needs_connection
    def reset (self):
        self.execute ('reset')

    def __repr__ (self):
        return '<Board port={} connected={}, version={}, modules={}, panels={}>'.format (
            self.port, self.connected, self.version, self.modules, self.panels
        )
