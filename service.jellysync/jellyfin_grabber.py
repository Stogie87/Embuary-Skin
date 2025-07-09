# -*- coding: utf-8 -*-
# GNU General Public License v2.0
import json
import urllib.request
import xbmcvfs
import os

class JellyfinGrabber:
    def __init__(self):
        self._jellyfin_server = None
        self._jellyfin_apikey = None
        self._jellyfin_userid = None
        self._setup_jellyfin_server()

    def _setup_jellyfin_server(self):
        # Lade die Konfigurationsdaten des Jellyfin-Addons
        config_path = xbmcvfs.translatePath("special://profile/addon_data/plugin.video.jellyfin/data.json")
        if not xbmcvfs.exists(config_path):
            raise Exception("Jellyfin-Config nicht gefunden: %s" % config_path)
        with open(config_path, "r", encoding="utf-8") as f:
            jf_servers = json.load(f)
        self._jellyfin_apikey = jf_servers["Servers"][0]["AccessToken"]
        self._jellyfin_server = jf_servers["Servers"][0]["address"].rstrip("/")
        self._jellyfin_userid = jf_servers["Servers"][0]["UserId"]

    def set_watched_status(self, item_id):
        """Markiert ein Item als gesehen."""
        api_endpoint = f"/Users/{self._jellyfin_userid}/PlayedItems/{item_id}"
        url = self._jellyfin_server + api_endpoint
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": f"MediaBrowser Token={self._jellyfin_apikey}",
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status in (200, 204)
        except Exception as e:
            print(f"Fehler beim Setzen auf 'gesehen': {e}")
            return False

    def unset_watched_status(self, item_id):
        """Markiert ein Item als ungesehen."""
        api_endpoint = f"/Users/{self._jellyfin_userid}/PlayedItems/{item_id}"
        url = self._jellyfin_server + api_endpoint
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": f"MediaBrowser Token={self._jellyfin_apikey}",
            },
            method="DELETE"
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status in (200, 204)
        except Exception as e:
            print(f"Fehler beim Setzen auf 'ungesehen': {e}")
            return False

    def get_jellyfin_userid(self):
        return self._jellyfin_userid

    def get_jellyfin_server(self):
        return self._jellyfin_server

    def get_jellyfin_apikey(self):
        return self._jellyfin_apikey
