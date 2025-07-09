import xbmc
import xbmcaddon
import xbmcvfs
import sqlite3
import time
from jellyfin_grabber import JellyfinGrabber

ADDON = xbmcaddon.Addon()
MONITOR = xbmc.Monitor()

# Passe ggf. die DB-Version an (MyVideos119.db ist Kodi 21 Omega, prüfe ggf. den Namen deines DB-Files)
KODI_DB_PATH = xbmcvfs.translatePath('special://database/MyVideos131.db')

def get_all_items():
    """
    Liefert alle Episoden und Filme mit playCount und uniqueid_value (Jellyfin-ID).
    """
    items = []
    try:
        conn = sqlite3.connect(KODI_DB_PATH)
        cursor = conn.cursor()
        # Episoden
        cursor.execute("SELECT idEpisode, playCount, uniqueid_value FROM episode_view WHERE uniqueid_value IS NOT NULL")
        items += [(row[0], row[1], row[2], 'episode') for row in cursor.fetchall()]
        # Filme
        cursor.execute("SELECT idMovie, playCount, uniqueid_value FROM movie_view WHERE uniqueid_value IS NOT NULL")
        items += [(row[0], row[1], row[2], 'movie') for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        xbmc.log(f"[JellyfinSync] Fehler beim Auslesen der Kodi-DB: {e}", xbmc.LOGERROR)
    return items

class WatchedSync(MONITOR.__class__):
    def __init__(self):
        super().__init__()
        self.jf = JellyfinGrabber()
        self.last_status = {}

    def onNotification(self, sender, method, data):
        # Trigger bei manuellen Änderungen im Video-Status
        if method in ["VideoLibrary.OnUpdate", "VideoLibrary.OnScanFinished"]:
            xbmc.log("[JellyfinSync] Trigger: Sync wegen Kodi-Event", xbmc.LOGINFO)
            self.sync_all_watched()

    def sync_all_watched(self):
        items = get_all_items()
        for kodi_id, playCount, jellyfin_id, mtype in items:
            if not jellyfin_id:
                continue
            key = f"{mtype}:{jellyfin_id}"
            prev = self.last_status.get(key)
            # playCount: 0 = ungesehen, >0 = gesehen
            if prev is not None and prev == playCount:
                continue  # Keine Änderung
            # Status an Jellyfin senden
            if playCount:
                ok = self.jf.set_watched_status(jellyfin_id)
                xbmc.log(f"[JellyfinSync] Setze {key} als GESEHEN: {ok}", xbmc.LOGINFO)
            else:
                ok = self.jf.unset_watched_status(jellyfin_id)
                xbmc.log(f"[JellyfinSync] Setze {key} als UNGESEHEN: {ok}", xbmc.LOGINFO)
            self.last_status[key] = playCount

def main():
    monitor = WatchedSync()
    # Initialer Sync beim Start
    xbmc.log("[JellyfinSync] Initialer Sync...", xbmc.LOGINFO)
    monitor.sync_all_watched()
    while not monitor.abortRequested():
        if monitor.waitForAbort(15):
            break
        # Optional: regelmäßiger Sync (z.B. alle 5 Minuten)
        if int(time.time()) % 300 < 15:  # alle 5 Minuten
            monitor.sync_all_watched()

if __name__ == "__main__":
    main()
