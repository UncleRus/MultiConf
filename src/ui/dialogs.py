# -*- coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *


class AsyncProcess (QThread):

    progressUpdated = Signal (int)
    changed = Signal (str)
    errorOccured = Signal (str)
    bannerUpdated = Signal (str)

    def __init__ (self, target, parent, changeCursor = False):
        super (AsyncProcess, self).__init__ (parent)
        self.target = target
        self.changeCursor = changeCursor
        self.finished.connect (self.deleteLater)

    def run (self):
        try:
            if self.changeCursor:
                QApplication.setOverrideCursor (Qt.WaitCursor)
            self.target ()
        except Exception as e:
            raise
            self.errorOccured.emit (str (e).decode ('utf-8'))
        finally:
            if self.changeCursor:
                QApplication.restoreOverrideCursor ()


class ProcessDialog (QDialog):

    def __init__ (self, parent):
        super (ProcessDialog, self).__init__ (parent, Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowMinMaxButtonsHint)
        self.setupUi ()

    def setupUi (self):
        l = QVBoxLayout (self)
        self.lBanner = QLabel (self)
        self.lBanner.setStyleSheet ('font-size: 12pt; padding-top: 16px; padding-bottom: 16px;')
        l.addWidget (self.lBanner)
        self.pbProgress = QProgressBar (self)
        l.addWidget (self.pbProgress)
        self.lStatus = QLabel (self)
        l.addWidget (self.lStatus)

        bl = QHBoxLayout ()
        bl.addStretch ()
        self.bContinue = QPushButton (self)
        self.bContinue.clicked.connect (self.onContinueClicked)
        bl.addWidget (self.bContinue)

        self.bCancel = QPushButton (self)
        self.bCancel.clicked.connect (self.onCancelClicked)
        bl.addWidget (self.bCancel)

        l.addLayout (bl)
        self.resize (400, 200)

        self.reset ()

    def keyPressEvent (self, event):
        if not self.bCancel.isEnabled () and event.key () in (Qt.Key_Escape, Qt.Key_Enter):
            event.ignore ()
            return
        super (ProcessDialog, self).keyPressEvent (event)

    def setupProcess (self):
        self.process.bannerUpdated.connect (self.lBanner.setText)
        self.process.started.connect (self.lockInterface)
        self.process.finished.connect (self.unlockInterface)
        self.process.terminated.connect (self.reset)
        self.process.errorOccured.connect (self.showError)
        self.process.changed.connect (self.setStatus)
        self.process.progressUpdated.connect (self.updateProgress)

    def reset (self):
        self.bContinue.setText (_('Continue'))
        self.bContinue.setEnabled (True)
        self.bCancel.setText (_('Cancel'))
        self.bCancel.setEnabled (True)
        self.bCancel.show ()
        self.finished = False

    def lockInterface (self):
        # process started
        self.bContinue.setEnabled (False)
        self.bCancel.setEnabled (False)

    def unlockInterface (self):
        # process finished
        self.bContinue.hide ()
        self.bCancel.setText (_('Close'))
        self.bCancel.setEnabled (True)
        QApplication.restoreOverrideCursor ()
        self.finished = True

    def showError (self, error):
        QMessageBox.critical (self, _('Firmware upload error'), error)
        self.lStatus.setText ('Error: %s' % error)
        self.reset ()

    def setStatus (self, message):
        self.lStatus.setText (message)

    def updateProgress (self, value):
        self.pbProgress.setValue (value)

    def onContinueClicked (self):
        self.start ()

    def onCancelClicked (self):
        if self.finished:
            self.accept ()
        else:
            self.reject ()

