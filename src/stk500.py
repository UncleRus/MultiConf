# -*- coding: utf-8 -*-

from PySide.QtCore import QObject, Signal, QThread
from PySide.QtGui import QApplication
import serial
import sys
from utils import Setting
import time
import struct
import random
import intelhex
from io import BytesIO


__all__ = ['Arduino']


class const (object):

    RESP_STK_OK = b'\x10'
    RESP_STK_FAILED = b'\x11'
    RESP_STK_UNKNOWN = b'\x12'
    RESP_STK_NODEVICE = b'\x13'
    RESP_STK_INSYNC = b'\x14'
    RESP_STK_NOSYNC = b'\x15'

    RESP_ADC_CHANNEL_ERROR = b'\x16'
    RESP_ADC_MEASURE_OK = b'\x17'
    RESP_PWM_CHANNEL_ERROR = b'\x18'
    RESP_PWM_ADJUST_OK = b'\x19'

    SYNC_CRC_EOP = b'\x20'  # 'SPACE'

    CMD_STK_GET_SYNC = b'\x30'
    CMD_STK_GET_SIGN_ON = b'\x31'

    CMD_STK_SET_PARAMETER = b'\x40'
    CMD_STK_GET_PARAMETER = b'\x41'
    CMD_STK_SET_DEVICE = b'\x42'
    CMD_STK_SET_DEVICE_EXT = b'\x45'

    CMD_STK_ENTER_PROGMODE = b'\x50'
    CMD_STK_LEAVE_PROGMODE = b'\x51'
    CMD_STK_CHIP_ERASE = b'\x52'
    CMD_STK_CHECK_AUTOINC = b'\x53'
    CMD_STK_LOAD_ADDRESS = b'\x55'
    CMD_STK_UNIVERSAL = b'\x56'
    CMD_STK_UNIVERSAL_MULTI = b'\x57'

    CMD_STK_PROG_FLASH = b'\x60'
    CMD_STK_PROG_DATA = b'\x61'
    CMD_STK_PROG_FUSE = b'\x62'
    CMD_STK_PROG_LOCK = b'\x63'
    CMD_STK_PROG_PAGE = b'\x64'
    CMD_STK_PROG_FUSE_EXT = b'\x65'

    CMD_STK_READ_FLASH = b'\x70'
    CMD_STK_READ_DATA = b'\x71'
    CMD_STK_READ_FUSE = b'\x72'
    CMD_STK_READ_LOCK = b'\x73'
    CMD_STK_READ_PAGE = b'\x74'
    CMD_STK_READ_SIGN = b'\x75'
    CMD_STK_READ_OSCCAL = b'\x76'
    CMD_STK_READ_FUSE_EXT = b'\x77'
    CMD_STK_READ_OSCCAL_EXT = b'\x78'

    PARAM_STK_HW_VER = b'\x80'  # ' ' - R
    PARAM_STK_SW_MAJOR = b'\x81'  # ' ' - R
    PARAM_STK_SW_MINOR = b'\x82'  # ' ' - R
    PARAM_STK_LEDS = b'\x83'  # ' ' - R/W
    PARAM_STK_VTARGET = b'\x84'  # ' ' - R/W
    PARAM_STK_VADJUST = b'\x85'  # ' ' - R/W
    PARAM_STK_OSC_PSCALE = b'\x86'  # ' ' - R/W
    PARAM_STK_OSC_CMATCH = b'\x87'  # ' ' - R/W
    PARAM_STK_RESET_DURATION = b'\x88'  # ' ' - R/W
    PARAM_STK_SCK_DURATION = b'\x89'  # ' ' - R/W

    PARAM_STK_BUFSIZEL = b'\x90'  # ' ' - R/W, Range {0..255}
    PARAM_STK_BUFSIZEH = b'\x91'  # ' ' - R/W, Range {0..255}
    PARAM_STK_DEVICE = b'\x92'  # ' ' - R/W, Range {0..255}
    PARAM_STK_PROGMODE = b'\x93'  # ' ' - 'P' or 'S'
    PARAM_STK_PARAMODE = b'\x94'  # ' ' - TRUE or FALSE
    PARAM_STK_POLLING = b'\x95'  # ' ' - TRUE or FALSE
    PARAM_STK_SELFTIMED = b'\x96'  # ' ' - TRUE or FALSE
    PARAM_STK500_TOPCARD_DETECT = b'\x98'  # ' ' - Detect top-card attached

    STATE_STK_INSYNC = b'\x01'  # INSYNC status bit, '1' - INSYNC
    STATE_STK_PROGMODE = b'\x02'  # Programming mode,  '1' - PROGMODE
    STATE_STK_STANDALONE = b'\x04'  # Standalone mode,   '1' - SM mode
    STATE_STK_RESET = b'\x08'  # RESET button,      '1' - Pushed
    STATE_STK_PROGRAM = b'\x10'  # Program button, '   1' - Pushed
    STATE_STK_LEDG = b'\x20'  # Green LED status,  '1' - Lit
    STATE_STK_LEDR = b'\x40'  # Red LED status,    '1' - Lit
    STATE_STK_LEDBLINK = b'\x80'  # LED blink ON/OFF,  '1' - Blink

    MEM_EEPROM = 0x45
    MEM_FLASH = 0x46


def needConnection (func):
    def wrapped (*args, **kwargs):
        self = args [0]
        try:
            if not self.serial.isOpen ():
                raise IOError (_('Not connected'))
            return func (*args, **kwargs)
        except Exception as e:
            self.setError (e)
            return None
    return wrapped


def dump (data):
    return ' '.join (('%02x' % ord (b) for b in data))


def getByte (bytes_, i = 0):
    return bytes_ [i] if isinstance (bytes_ [i], int) else ord (bytes_ [i])


class Arduino (QObject):

    timeout = Setting ('Arduino/Timeout', 5.0)

    errorOccured = Signal (str)
    changed = Signal (str)
    progressUpdated = Signal (int)

    def __init__ (self, parent = None):
        super (Arduino, self).__init__ (parent)
        self.serial = serial.Serial ()
        self.waiting = False

    def readBytes (self, length):
        stop = time.time () + self.timeout

        if length is None:
            res = bytearray ()
            while True:
                if time.time () > stop:
                    raise IOError (_('Sync timeout'))
                if self.serial.inWaiting () > 0:
                    b = self.serial.read ()
                    res.append (b)
                    if b == const.RESP_STK_OK:
                        return bytes (res)
                QApplication.processEvents ()

        while self.serial.inWaiting () < length:
            if time.time () > stop:
                raise IOError (_('Sync timeout'))
            QApplication.processEvents ()
        return self.serial.read (length)

    def sync (self, length = 0):
        res = self.readBytes (None if length is None else length + 2)
        #print 'RECV (%02x):' % len (res), dump (res)
        if res [0] != const.RESP_STK_INSYNC or res [-1] != const.RESP_STK_OK:
            raise IOError (_('Out of sync'))
        return res [1:-1]

    def execute (self, cmd, resLength = 0):
        #print 'SENT: (%02x):' % len (cmd + const.SYNC_CRC_EOP), dump (cmd + const.SYNC_CRC_EOP)
        self.serial.write (cmd)
        self.serial.write (const.SYNC_CRC_EOP)
        QThread.msleep (50)
        return self.sync (resLength)

    def getParameter (self, parameter, size = 1):
        return self.execute (const.CMD_STK_GET_PARAMETER + parameter, size)

    def iterateCommand (self, state, address, length, func, buffer_size):
        loops = length / buffer_size
        tail = length % buffer_size
        if tail:
            loops += 1
        result = bytearray ()
        self.changed.emit (_(state))
        self.progressUpdated.emit (0)
        for i in xrange (loops):
            offset = i * buffer_size
            self.setAddress (address + offset)
            result += func (offset, tail if tail and i == loops - 1 else buffer_size)
            self.progressUpdated.emit (100.0 / loops * (i + 1))
            QApplication.processEvents ()
        self.changed.emit (_('Done'))
        self.progressUpdated.emit (100)
        return bytes (result)

    def readMemory (self, address, length, eeprom = False):
        return self.iterateCommand (
            'Reading %s' % ('EEPROM' if eeprom else 'flash'),
            address,
            length,
            lambda _, size: self.execute (const.CMD_STK_READ_PAGE + struct.pack ('>HB', size, const.MEM_EEPROM if eeprom else const.MEM_FLASH), size),
            0x100
        )

    def writeMemory (self, address, data, eeprom = False):
        return self.iterateCommand (
            'Writing %s' % ('EEPROM' if eeprom else 'flash'),
            address,
            len (data),
            lambda offs, size: self.execute (const.CMD_STK_PROG_PAGE + struct.pack ('>HB', size, const.MEM_EEPROM if eeprom else const.MEM_FLASH) + data [offs:offs + size], 0),
            0x80
        )

    def setError (self, e):
        self.changed.emit (_('Error'))
        self.errorOccured.emit (str (e).decode ('utf-8'))

    def reset (self):
        self.serial.setDTR (False)
        self.serial.setRTS (False)
        QThread.msleep (250)
        self.serial.setDTR (True)
        self.serial.setRTS (True)
        QThread.msleep (50)

    def open (self, port, baudrate = 115200):
        try:
            self.serial.port = port
            self.serial.baudrate = baudrate
            self.serial.parity = serial.PARITY_NONE
            self.serial.stopbits = serial.STOPBITS_ONE
            self.serial.datasize = serial.EIGHTBITS
            self.serial.timeout = self.timeout
            self.serial.open ()

            self.reset ()

            for _ in xrange (10):
                self.serial.write (const.CMD_STK_GET_SYNC + const.SYNC_CRC_EOP)
                self.serial.flushInput ()
                QThread.msleep (10)

            self.waiting = True
            while self.waiting:
                self.serial.flushInput ()
                self.serial.write (const.CMD_STK_GET_SYNC + const.SYNC_CRC_EOP)
                QThread.msleep (random.randrange (500, 1000))
                QApplication.processEvents ()
                if self.serial.inWaiting () < 2:
                    continue
                if self.readBytes (2) == const.RESP_STK_INSYNC + const.RESP_STK_OK:
                    break
            self.changed.emit (_('Connected'))
            self.progressUpdated.emit (0)
            return True
        except Exception as e:
            try:
                self.serial.close ()
            except:
                pass
            self.setError (e)
            return False

    def cancel (self):
        self.waiting = False

    def close (self):
        self.serial.close ()
        self.changed.emit (_('Disconnected'))
        self.progressUpdated.emit (0)

    @needConnection
    def getSignOn (self):
        '''
        Not supported by Optiboot
        '''
        return self.execute (const.CMD_STK_GET_SIGN_ON, None)

    @needConnection
    def getBootloaderVersion (self):
        '''
        4.4 on optiboot
        '''
        return (
            getByte (self.getParameter (const.PARAM_STK_SW_MAJOR)),
            getByte (self.getParameter (const.PARAM_STK_SW_MINOR))
        )

    @needConnection
    def readSignature (self):
        return struct.unpack ('>I', b'\x00' + self.execute (const.CMD_STK_READ_SIGN, 3))[0]

    @needConnection
    def setAddress (self, address):
        self.execute (const.CMD_STK_LOAD_ADDRESS + struct.pack ('<H', address >> 1))

    @needConnection
    def enterProgMode (self):
        self.execute (const.CMD_STK_ENTER_PROGMODE)

    @needConnection
    def leaveProgMode (self):
        self.execute (const.CMD_STK_LEAVE_PROGMODE)

    @needConnection
    def downloadEeprom (self, address, length):
        return self.readMemory (address, length, True)

    @needConnection
    def uploadEeprom (self, address, data):
        return self.writeMemory (address, data, True)

    @needConnection
    def downloadFlash (self, address, length):
        return self.readMemory (address, length, False)

    @needConnection
    def uploadFlash (self, address, data):
        return self.writeMemory (address, data, False)

    @needConnection
    def uploadHex (self, file):
        buffer = BytesIO ()
        intelhex.hex2bin (file, buffer)
        bin = buffer.getvalue ()
        self.uploadFlash (0, bin)
        if self.downloadFlash (0, len (bin)) != bin:
            raise IOError (_('Verification failed'))

