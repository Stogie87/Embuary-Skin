import xbmc
import xbmcaddon
import xbmcgui
import json
import sys
import traceback

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')

LOGLEVELS = {
    'INFO': xbmc.LOGINFO,
    'WARNING': xbmc.LOGWARNING,
    'ERROR': xbmc.LOGERROR,
    'DEBUG': xbmc.LOGDEBUG,
    'FATAL': xbmc.LOGFATAL
}

def log(msg, level='INFO'):
    xbmc.log(f'[{ADDON_ID}] {msg}', LOGLEVELS.get(level.upper(), xbmc.LOGINFO))

def show_error_dialog(message):
    xbmcgui.Dialog().notification("Episode Jumper", message, xbmcgui.NOTIFICATION_ERROR)

def get_episode_from_kodi_library(tvshowtitle, season, episode, direction="next"):
    try:
        query = {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetEpisodes",
            "params": {
                "filter": {"field": "tvshow", "operator": "is", "value": tvshowtitle},
                "properties": ["file", "season", "episode", "playcount"],
                "sort": {"order": "ascending", "method": "season", "ignorearticle": True}
            },
            "id": 1
        }
        response = xbmc.executeJSONRPC(json.dumps(query))
        data = json.loads(response)
        episodes = data.get("result", {}).get("episodes", [])
        for idx, ep in enumerate(episodes):
            if ep["season"] == int(season) and ep["episode"] == int(episode):
                if direction == "next":
                    if idx+1 < len(episodes):
                        return episodes[idx+1]["file"]
                elif direction == "previous":
                    if idx-1 >= 0:
                        return episodes[idx-1]["file"]
        return None
    except Exception as e:
        log(f"Fehler beim Abrufen der Episode: {repr(e)}", level='ERROR')
        return None

def get_episodeid_from_kodi_library(tvshowtitle, season, episode):
    try:
        query = {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetEpisodes",
            "params": {
                "filter": {
                    "and": [
                        {"field": "tvshow", "operator": "is", "value": tvshowtitle},
                        {"field": "season", "operator": "is", "value": str(season)},
                        {"field": "episode", "operator": "is", "value": str(episode)}
                    ]
                },
                "properties": ["episodeid", "file", "season", "episode", "playcount"]
            },
            "id": 1
        }
        response = xbmc.executeJSONRPC(json.dumps(query))
        data = json.loads(response)
        episodes = data.get("result", {}).get("episodes", [])
        if episodes:
            return episodes[0]["episodeid"]
        return None
    except Exception as e:
        log(f"Fehler beim Abrufen der episodeid: {repr(e)}", level='ERROR')
        return None

def set_episode_playcount(episodeid, playcount):
    try:
        query = {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.SetEpisodeDetails",
            "params": {
                "episodeid": episodeid,
                "playcount": playcount
            },
            "id": 1
        }
        xbmc.executeJSONRPC(json.dumps(query))
        log(f"Setze playcount für episodeid {episodeid} auf {playcount}", "INFO")
    except Exception as e:
        log(f"Fehler beim Setzen des playcount: {repr(e)}", "ERROR")

def get_episode_from_playlist(direction="next"):
    try:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pos = playlist.getposition()
        if pos == -1:
            return None
        if direction == "next":
            if pos + 1 < playlist.size():
                return playlist[pos + 1].getfilename()
        elif direction == "previous":
            if pos - 1 >= 0:
                return playlist[pos - 1].getfilename()
        return None
    except Exception as e:
        log(f"Fehler beim Playlist-Check: {repr(e)}", level='ERROR')
        return None

def is_kodi_library_episode(filepath):
    # Prüfe, ob Datei wie eine lokale Datei aussieht (z.B. Pfad beginnt nicht mit plugin://)
    return filepath and not filepath.startswith("plugin://")

def jump_to_end_and_wait(player):
    try:
        total_time = player.getTotalTime()
        if total_time > 1:
            seek_time = max(0, total_time - 1)  # 1 Sekunde vor Schluss
            player.seekTime(seek_time)
            xbmc.sleep(1500)  # 1,5 Sekunden warten
            log("Habe 1 Sekunde vor Episodenende gespult und gewartet.", "DEBUG")
    except Exception as e:
        log(f"Fehler beim Vorspulen ans Ende: {repr(e)}", "ERROR")

def main():
    try:
        direction = "next"
        if len(sys.argv) > 1:
            if sys.argv[1].lower() in ["previous", "next"]:
                direction = sys.argv[1].lower()

        log(f"Script gestartet, Richtung: {direction}", level='INFO')
        player = xbmc.Player()
        if not player.isPlaying():
            log("Kein aktives Playback. Keine Episode kann gestartet werden.", level='WARNING')
            show_error_dialog("Kein aktives Playback – keine Episode kann gestartet werden.")
            return

        tvshowtitle = xbmc.getInfoLabel('VideoPlayer.TVShowTitle')
        season = xbmc.getInfoLabel('VideoPlayer.Season')
        episode = xbmc.getInfoLabel('VideoPlayer.Episode')
        current_file = xbmc.getInfoLabel('VideoPlayer.Filenameandpath')

        log(f"Metadaten: Serie={tvshowtitle}, Staffel={season}, Episode={episode}, Datei={current_file}", level='DEBUG')

        episode_path = None

        # Hole das Ziel (nächste/vorherige Episode)
        if tvshowtitle and season and episode:
            episode_path = get_episode_from_kodi_library(tvshowtitle, season, episode, direction)
            if episode_path:
                log(f"Episode ({direction}) aus Kodi-Library: {episode_path}", level='INFO')

        if not episode_path:
            episode_path = get_episode_from_playlist(direction)
            if episode_path:
                log(f"Episode ({direction}) aus Playlist: {episode_path}", level='INFO')

        if not episode_path:
            log(f"{direction.capitalize()} Episode konnte nicht gefunden werden.", level='ERROR')
            label = "Nächste" if direction == "next" else "Vorherige"
            show_error_dialog(f"{label} Episode konnte nicht gefunden werden.")
            return

        # --- Status-Handling ---
        if direction == "next":
            # Immer: Vorspulen ans Ende (1 Sekunde vor Schluss) und warten!
            jump_to_end_and_wait(player)
            # Zusätzlich: Für Kodi-Library Episoden den Status setzen
            if is_kodi_library_episode(current_file):
                episodeid = get_episodeid_from_kodi_library(tvshowtitle, season, episode)
                if episodeid:
                    set_episode_playcount(episodeid, 1)  # Gesehen
        elif direction == "previous":
            # NICHT vorspulen, nur Status "ungesehen" setzen (nur bei Kodi-Library)
            if is_kodi_library_episode(current_file):
                episodeid = get_episodeid_from_kodi_library(tvshowtitle, season, episode)
                if episodeid:
                    set_episode_playcount(episodeid, 0)  # Ungesehen

        # Springe zur gewünschten Episode
        try:
            player.play(episode_path)
            log(f"Gestartet: {episode_path}", level='INFO')
        except Exception as e:
            log(f"Fehler beim Starten der Episode: {repr(e)}", level='ERROR')
            show_error_dialog("Fehler beim Starten der Episode.")

    except Exception as e:
        tb = traceback.format_exc()
        log(f"Exception im Skript: {repr(e)}\n{tb}", level='ERROR')
        show_error_dialog("Unerwarteter Fehler. Siehe Logdatei für Details.")

if __name__ == '__main__':
    main()
