# -*- coding: utf-8 -*-

from PySide.QtCore import *
from PySide.QtGui import *

import os.path as osp
import os
import json
from settings import settings
import requests
import time


class DataStorage (QObject):

    FONT_NAME = 'font.mcm'
    MAP_NAME = 'map.json'

    updated = Signal (bool)

    def __init__ (self, parent = None):
        super (DataStorage, self).__init__ (parent)
        print settings.dataPath
        if not osp.exists (settings.dataPath):
            os.makedirs (settings.dataPath)
        self.indexFile = osp.join (settings.dataPath, 'releases.json')
        print self.indexFile
        self.releases = json.load (open (self.indexFile, 'rb')) if osp.isfile (self.indexFile) else []
        self.updateMaps ()

    def download (self, url, filename, rjson = False, force = False):
        if not url:
            return None

        QApplication.setOverrideCursor (Qt.WaitCursor)
        try:
            if not force and filename and osp.isfile (filename):
                return json.load (open (filename, 'rb')) if rjson else None

            res = requests.get (url)
            if res.status_code != 200:
                raise (self.tr ('Cannot download %s') % url)

            if filename:
                with open (filename, 'wb') as f:
                    f.write (res.text.encode ('utf-8'))

            return json.loads (res.text.encode ('utf-8')) if rjson else None
        except Exception as e:
            QMessageBox.critical (self, self.tr ('Error'), str (e).decode ('utf-8'))
            return None
        finally:
            QApplication.restoreOverrideCursor ()

    def updateMaps (self):
        for i, rel in enumerate (self.releases):
            map = {a ['name']: a for a in rel ['assets']}.get (self.MAP_NAME)
            if not map:
                del self.releases [i]
            path = osp.join (settings.dataPath, rel ['name'])
            if not osp.exists (path):
                os.makedirs (path)
            rel ['struct'] = self.download (map ['browser_download_url'], osp.join (path, self.MAP_NAME), True)
        self.versions = {rel ['name']: rel for rel in self.releases}

    def update (self):
        releases = self.download (settings.repositoryUrl, None, True, True)
        if ({rel ['id']: rel ['name'] for rel in releases} == \
            {rel ['id']: rel ['name'] for rel in self.releases}):
            self.updated.emit (False)
            return

        self.releases = sorted (releases, key = lambda rel: time.strptime (rel ['published_at'], '%Y-%m-%dT%H:%M:%SZ'))[::-1]
        with open (self.indexFile, 'wb') as f:
            json.dump (self.releases, f)
        self.updateMaps ()
        self.updated.emit (True)

    def latest (self):
        return self.releases [0] if self.releases else None

    def isEmpty (self):
        return not bool (self.releases)

    def getAsset (self, release, name):
        asset = {a ['name']: a for a in release ['assets']}.get (name)
        if not asset:
            QMessageBox.critical (self, self.tr ('Error'), self.tr ('Cannot find asset "%s" in release "%s"' % (name, release ['name'])))
        return asset ['browser_download_url']

    def getHex (self, relIdx, build):
        release = self.releases [relIdx]
        product = release ['struct']['product']
        filename = '%s_%s.hex' % (product ['name'], '_'.join ((b.lower () for b in product ['builds'][build])))
        res = osp.join (settings.dataPath, product ['version'], filename)
        self.download (self.getAsset (release, filename), res, False, False)
        return res if osp.isfile (res) else None

    def getMap (self, version):
        if self.isEmpty ():
            self.update ()
        return self.versions [version]['struct']

    def getFont (self, relIdx):
        res = osp.join (settings.dataPath, self.releases [relIdx]['name'], self.FONT_NAME)
        self.download (self.getAsset (self.releases [relIdx], self.FONT_NAME), res, False, False)
        return res if osp.isfile (res) else None


storage = DataStorage ()
