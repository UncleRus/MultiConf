#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *
import ui


CHAR_WIDTH = 12
CHAR_HEIGHT = 18


class Char (QImage):

    colors = (
        qRgb (0, 0, 0),
        qRgba (128, 128, 128, 0),
        qRgb (255, 255, 255),
        qRgba (128, 128, 128, 0),
    )

    def __init__ (self, data):
        super (Char, self).__init__ (CHAR_WIDTH, CHAR_HEIGHT, QImage.Format.Format_Indexed8)
        for i, c in enumerate (self.colors):
            self.setColor (i, c)

        for r in xrange (CHAR_HEIGHT):
            for c in xrange (CHAR_WIDTH / 4):
                byte = data [r * 3 + c]
                for s in xrange (3, -1, -1):
                    color = (byte >> (s * 2)) & 0x03
                    x = c * 4 + 3 - s
                    self.setPixel (x, r, color)


class Font (object):

    def __init__ (self, file):
        self.load (file)

    def load (self, file):
        if file.readline ().strip () != 'MAX7456':
            raise IOError ('Unknown file format')
        data = [int (file.readline ().strip (), 2) for _ in xrange (16384)]
        self.chars = [Char (data [i * 64 : i * 64 + 64]) for i in xrange (256)]

    def write (self, textbuf, dest = None):
        if isinstance (textbuf, (bytes, bytearray)):
            textbuf = (textbuf,)

        if not dest:
            maxlen = max ((len (line) for line in textbuf))
            dest = QImage (QSize (maxlen * CHAR_WIDTH, len (textbuf) * CHAR_HEIGHT), QImage.Format_ARGB32_Premultiplied)
            dest.fill (qRgba (0, 0, 0, 0))

        painter = QPainter (dest)
        pos = QPoint (0, 0)
        for line in textbuf:
            pos.setX (0)
            for c in bytearray (line):
                painter.drawImage (pos, self.chars [c])
                pos.setX (pos.x () + CHAR_WIDTH)
            pos.setY (pos.y () + CHAR_HEIGHT)
        painter.end ()

        return dest


class PanelType (object):

    @classmethod
    def create (cls, struct):
        return cls (
            name = struct ['name'],
            description = struct ['descr'],
            size = struct ['size'],
            textbuf = struct ['filler'],
            minSize = struct ['min_size']
        )

    def __init__ (self, name, description, size, textbuf, minSize = None):
        self.name = name
        self.description = description
        self.width, self.height = size
        self.textbuf = textbuf
        self.minWidth, self.minHeight = minSize or size

    def rect (self, offset):
        return QRect (0, 0, self.width, self.height).translated (offset)


class Panel (QGraphicsItem):

    def __init__ (self, scene, fixedFont, panelType):
        super (Panel, self).__init__ ()
        self.overlapped = False
        self.setFlag (QGraphicsItem.ItemIsSelectable, True)
        self.fixedFont = None
        self.panelType = None
        self.dragging = False
        self.setFixedFont (fixedFont)
        self.setPanelType (panelType)
        scene.addItem (self)

    def setFixedFont (self, value):
        self.fixedFont = value
        self.updatePixmap ()

    def setPanelType (self, value):
        self.panelType = value
        self.updatePixmap ()

    def updatePixmap (self):
        if self.fixedFont and self.panelType:
            self._rect = QRectF (0, 0, self.panelType.width * CHAR_WIDTH, self.panelType.height * CHAR_HEIGHT)
            self.pixmap = QPixmap.fromImage (self.fixedFont.write (self.panelType.textbuf))

    def screenPos (self):
        return self.scene ().toScreenPos (self.pos ())

    def setScreenPos (self, pos):
        self.setPos (self.scene ().toScenePos (pos))

    def boundingRect (self):
        return self._rect

    def paint (self, painter, option, widget):
        painter.drawPixmap (0, 0, self.pixmap)
        if self.overlapped:
            painter.setPen (QPen (Qt.red, 0, Qt.SolidLine))
            painter.drawRect (self._rect)
        if self.isSelected ():
            painter.setPen (QPen (Qt.white, 0, Qt.DashLine))
            painter.drawRect (self._rect)

    def mousePressEvent (self, e):
        super (Panel, self).mousePressEvent (e)
        if e.button () == Qt.LeftButton:
            self.dragging = True
            self.dragStartPos = self.scene ().position ()

    def mouseReleaseEvent (self, e):
        super (Panel, self).mouseReleaseEvent (e)
        self.dragging = False

    def mouseMoveEvent (self, e):
        if not self.dragging or not self.scene ():
            return
        pos = self.pos () + self.scene ().position () - self.dragStartPos
        self.dragStartPos = self.scene ().position ()
        self.scene ().movePanel (self, pos)
        self.scene ().invalidate ()

    def itemChange (self, change, value):
        if self.scene ():
            if change == self.ItemSceneHasChanged:
                self.updateOverlapped ()
            elif change == self.ItemSelectedHasChanged:
                self.scene ().invalidate ()
        return super (Panel, self).itemChange (change, value)

    def updateOverlapped (self):
        scrPos = self.screenPos ()
        scrRect = self.panelType.rect (scrPos)
        for panel in self.scene ().items ():
            if panel == self:
                continue
            self.overlapped = scrRect.intersects (panel.panelType.rect (panel.screenPos ()))
            if self.overlapped:
                break
        if not self.overlapped:
            ovlX = self.scene ().cols - self.panelType.width
            ovlY = self.scene ().rows - self.panelType.height
            self.overlapped = scrPos.x () > ovlX or scrPos.y () > ovlY
        self.update ()


class Screen (QGraphicsScene):

    def __init__ (self, cols, rows, bgImage = None, parent = None):
        super (Screen, self).__init__ (parent)
        self.setScreenSize (cols, rows)
        self.setBgImage (bgImage)
        self._screenPos = QPoint (0, 0)
        self._position = QPoint (0, 0)

    def setScreenSize (self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.setSceneRect (0, 0, self.cols * CHAR_WIDTH, self.rows * CHAR_HEIGHT)

    def setBgImage (self, image):
        self.bgImage = image
        rect = self.sceneRect ().toRect ()
        bgBuf = QImage (rect.size (), QImage.Format_ARGB32_Premultiplied)
        painter = QPainter (bgBuf)
        if image:
            painter.drawImage (rect, image.scaled (rect.size (), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        else:
            painter.fillRect (rect, Qt.gray)
        painter.end ()
        self.bgPixmap = QPixmap.fromImage (bgBuf)
        self.update ()

    def closestPos (self, point):
        return QPoint (
            round (point.x () / CHAR_WIDTH) * CHAR_WIDTH,
            round (point.y () / CHAR_HEIGHT) * CHAR_HEIGHT
        )

    def toScreenPos (self, point):
        return QPoint (
            round (point.x () / CHAR_WIDTH),
            round (point.y () / CHAR_HEIGHT)
        )

    def toScenePos (self, point):
        return QPoint (point.x () * CHAR_WIDTH, point.y () * CHAR_HEIGHT)

    def position (self):
        return self._position

    def screenPos (self):
        return self._screenPos

    def drawBackground (self, painter, rect):
        painter.fillRect (rect, Qt.gray)

        rect = rect.intersected (self.sceneRect ())

        painter.drawPixmap (rect, self.bgPixmap, rect)
        painter.setPen (QPen (Qt.darkGray, 0, Qt.DotLine))
        painter.drawLines ([QLineF (0, y, rect.width (), y) for y in xrange (0, int (rect.height ()), CHAR_HEIGHT)])
        painter.drawLines ([QLineF (x, 0, x, rect.height ()) for x in xrange (0, int (rect.width ()), CHAR_WIDTH)])

    def mouseMoveEvent (self, e):
        if self.sceneRect ().contains (e.scenePos ()):
            self._position = self.closestPos (e.scenePos ())
            self._screenPos = self.toScreenPos (e.scenePos ())
        super (Screen, self).mouseMoveEvent (e)

    def movePanel (self, panel, target):
        tgtPos = self.toScreenPos (target)
        maxX = self.cols - panel.panelType.minWidth
        maxY = self.rows - panel.panelType.minHeight
        if tgtPos.x () < 0:
            tgtPos.setX (0)
        elif tgtPos.x () > maxX:
            tgtPos.setX (maxX)
        if tgtPos.y () < 0:
            tgtPos.setY (0)
        elif tgtPos.y () > maxY:
            tgtPos.setY (maxY)
        panel.setScreenPos (tgtPos)
        for p in self.items ():
            p.updateOverlapped ()

    def deleteSelected (self):
        for panel in self.items ():
            if panel.isSelected ():
                self.removeItem (panel)

    def keyPressEvent (self, e):
        if e.key () == Qt.Key_Delete:
            self.deleteSelected ()


class ScreenEditor (QGraphicsView):

    def __init__ (self, screen, owner = None):
        super (ScreenEditor, self).__init__ (screen, owner)
        self.setMouseTracking (True)

    def resizeEvent (self, e):
        size = self.sceneRect ().size ().toSize ()
        if e.size ().width () < size.width () or e.size ().height () < size.height ():
            super (ScreenEditor, self).resizeEvent (e)
        else:
            self.fitInView (self.sceneRect (), Qt.KeepAspectRatio)


class ScreenTab (QWidget):

    def __init__ (self, proc, parent = None):
        super (ScreenTab, self).__init__ (parent)
        self.proc = proc
        l = QVBoxLayout (self)
        self.screen = Screen (30, 16, QImage (':/res/background.jpg'), self)
        self.view = ScreenEditor (self.screen, self)
        l.addWidget (self.view)

    def refresh (self, state):
        pass


class ScreensWidget (ui.Scrollable):

    MAX_SCREENS = 8

    changed = Signal ()

    def __init__ (self, name, proc, parent = None):
        self.proc = proc
        self.button = ui.SquareButton (name, _(name))
        self.button.toggled.connect (lambda state: self.parent ().setCurrentWidget (self))

        self.proc.connectionChanged.connect (self.refresh)
        super (ScreensWidget, self).__init__ (parent)

    def setupUi (self):
        super (ScreensWidget, self).setupUi ()
        self.layout ().setContentsMargins (0, 0, 0, 0)

        self.lMain = QHBoxLayout (self.content)
        self.lMain.setContentsMargins (0, 0, 0, 0)

        self.panels = QListWidget (self)
        self.panels.setMaximumWidth (200)
        self.panels.setMinimumWidth (200)

        self.tabWidget = QTabWidget (self.content)
        self.tabs = []
        for i in xrange (self.MAX_SCREENS):
            tab = ScreenTab (self.proc, self)
            self.tabWidget.addTab (tab, 'Screen %d' % (i + 1))
            self.tabs.append (tab)

        self.lMain.addWidget (self.panels)
        self.lMain.addWidget (self.tabWidget)

        self.refresh (False)

    def refresh (self, state):
        if not state:
            self.clear ()
        else:
            self.load ()
        # TODO: Убрать!
        #self.button.setEnabled (state)

    def clear (self):
        self.panels.clear ()

    def load (self):
        print self

