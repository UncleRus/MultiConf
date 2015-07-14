#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *
import serial
import time
import sys


class STK500 (QObject):

    def __init__ (self, parent = None):
        super (STK500, self).__init__ (parent)
        self.serial = serial.Serial ()
        self.waiting = False

    def open (self, port, baudrate = 115200):
        try:
            self.serial.port = port
            self.serial.baudrate = baudrate
            self.serial.open ()

            self.serial.setDTR (False)
            self.serial.setRTS (False)
            time.sleep (0.05)
            self.serial.setDTR (True)
            self.serial.setRTS (True)
            time.sleep (0.05)

            self.waiting = True
            while self.waiting:
                QApplication.processEvents ()
                self.serial.flushInput ()
                self.serial.write (b'\x30\x20')
                time.sleep (0.05)
                if self.serial.inWaiting () >= 2:
                    sync = self.serial.read (2)
                    if sync == b'\x14\x10':
                        return True
        except Exception as e:
            self.error.emit (repr (e))

    def cancel (self):
        self.waiting = False

    def close (self):
        self.serial.close ()

    def execute (self, cmd):
        self.serial.write ()


class Banner (QDialog):
    
    

class MainWindow (QWidget):

    def __init__ (self):
        super (MainWindow, self).__init__ ()
        self.resize (800, 600)
        self.b = QPushButton (self, 'Click!')
        self.b.clicked.connect (self.onClick)
    
    def onClick (self):

#p = STK500 ()
#p.open ('/dev/ttyUSB0')
#p.close ()

def main ():
    
    app = QApplication (sys.argv)
    
    w = MainWindow ()
    w.show ()
    
    sys.exit (app.exec_ ())
    

if __name__ == '__main__':
    main ()




