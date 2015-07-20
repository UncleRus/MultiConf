# -*- coding: utf-8 -*-

from PySide.QtGui import *
from utils import Setting
import os
import os.path as osp


if os.name == 'nt':
    from knownpaths import get_path, FOLDERID
    DATA_PATH = osp.join (get_path (FOLDERID.ProgramData), QApplication.organizationName (), QApplication.applicationName ())
else:
    DATA_PATH = QDesktopServices.storageLocation (QDesktopServices.DataLocation)


class _Settings (object):

    port = Setting ('Port', 'COM5' if os.name == 'nt' else '/dev/ttyUSB0')
    baudrate = Setting ('Baudrate', 57600)
    stkBaudrate = Setting ('ArduinoBaudrate', 115200)
    dataPath = Setting ('dataPath', DATA_PATH)
    productName = Setting ('productName', 'MultiOSD')
    repositoryUrl = Setting ('repositoryUrl', 'https://api.github.com/repos/%s/MultiOSD/releases' % QApplication.organizationName ())
    connectionTimeout = Setting ('connectionTimeout', 5)
    chipSignature = Setting ('chipSignature', 0x001e950f)

settings = _Settings ()
