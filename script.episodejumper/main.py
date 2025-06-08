# -*- coding: utf-8 -*-
import xbmc
import xbmcaddon
import xbmcgui
import json
import sys
import traceback
import re

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

def get_tvshowid_by_title(tvshowtitle):
    try:
        query = {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetTVShows",
            "params": {"filter": {"field": "title", "operator": "is", "value": tvshowtitle}},
            "id": 1
        }
        response = xbmc.executeJSONRPC(json.dumps(query))
        data = json.loads(response)
        shows = data.get("result", {}).get("tvshows", [])
        if shows:
            return shows[0]["tvshowid"]
    except Exception as e:
        log(f"Fehler beim Ermitteln der TVShowID: {repr(e)}", level='ERROR')
    return None

def get_episode_upnext(tvshowid, season, episode, direction="next"):
    try:
        if direction == "next":
            operator = "greaterthan"
            sort_order = "ascending"
            fallback_season_operator = "greaterthan"
            fallback_episode = "1"
        else:
            operator = "lessthan"
            sort_order = "descending"
            fallback_season_operator = "lessthan"
            fallback_episode = None

        filters_same_season = {
            "and": [
                {"field": "tvshowid", "operator": "is", "value": tvshowid},
                {"field": "season", "operator": "is", "value": str(season)},
                {"field": "episode", "operator": operator, "value": str(episode)}
            ]
        }
        query = {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetEpisodes",
            "params": {
                "filter": filters_same_season,
                "properties": ["file", "season", "episode", "playcount"],
                "sort": {"order": sort_order, "method": "episode"},
                "limits": {"start": 0, "end": 1}
            },
            "id": 1
        }
        response = xbmc.executeJSONRPC(json.dumps(query))
        data = json.loads(response)
        episodes = data.get("result", {}).get("episodes", [])
        if episodes:
            return episodes[0]["file"]

        if direction == "next":
            filters_next_season = {
                "and": [
                    {"field": "tvshowid", "operator": "is", "value": tvshowid},
                    {"field": "season", "operator": fallback_season_operator, "value": str(season)},
                    {"field": "episode", "operator": "is", "value": fallback_episode}
                ]
            }
            query["params"]["filter"] = filters_next_season
            query["params"]["sort"] = {"order": "ascending", "method": "season"}
        else:
            prev_season_query = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetEpisodes",
                "params": {
                    "filter": {
                        "and": [
                            {"field": "tvshowid", "operator": "is", "value": tvshowid},
                            {"field": "season", "operator": fallback_season_operator, "value": str(season)}
                        ]
                    },
                    "properties": ["season"],
                    "sort": {"order": "descending", "method": "season"},
                    "limits": {"start": 0, "end": 1}
                },
                "id": 1
            }
            response_prev = xbmc.executeJSONRPC(json.dumps(prev_season_query))
            data_prev = json.loads(response_prev)
            prev_episodes = data_prev.get("result", {}).get("episodes", [])
            if not prev_episodes:
                return None
            prev_season_num = prev_episodes[0]["season"]
            filters_prev_season = {
                "and": [
                    {"field": "tvshowid", "operator": "is", "value": tvshowid},
                    {"field": "season", "operator": "is", "value": str(prev_season_num)}
                ]
            }
            query["params"]["filter"] = filters_prev_season
            query["params"]["sort"] = {"order": "descending", "method": "episode"}

        response = xbmc.executeJSONRPC(json.dumps(query))
        data = json.loads(response)
        episodes = data.get("result", {}).get("episodes", [])
        if episodes:
            return episodes[0]["file"]

    except Exception as e:
        log(f"Fehler bei Up Next Episode-Suche ({direction}): {repr(e)}", level='ERROR')
    return None

def get_episode_fallback(tvshowtitle, season, episode, direction="next"):
    try:
        if direction == "next":
            operator = "greaterthan"
            sort_order = "ascending"
            fallback_season_operator = "greaterthan"
            fallback_episode = "1"
        else:
            operator = "lessthan"
            sort_order = "descending"
            fallback_season_operator = "lessthan"
            fallback_episode = None

        filters_same_season = {
            "and": [
                {"field": "tvshow", "operator": "is", "value": tvshowtitle},
                {"field": "season", "operator": "is", "value": str(season)},
                {"field": "episode", "operator": operator, "value": str(episode)}
            ]
        }
        query = {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetEpisodes",
            "params": {
                "filter": filters_same_season,
                "properties": ["file", "season", "episode", "playcount"],
                "sort": {"order": sort_order, "method": "episode"},
                "limits": {"start": 0, "end": 1}
            },
            "id": 1
        }
        response = xbmc.executeJSONRPC(json.dumps(query))
        data = json.loads(response)
        episodes = data.get("result", {}).get("episodes", [])
        if episodes:
            return episodes[0]["file"]

        if direction == "next":
            filters_next_season = {
                "and": [
                    {"field": "tvshow", "operator": "is", "value": tvshowtitle},
                    {"field": "season", "operator": fallback_season_operator, "value": str(season)},
                    {"field": "episode", "operator": "is", "value": fallback_episode}
                ]
            }
            query["params"]["filter"] = filters_next_season
            query["params"]["sort"] = {"order": "ascending", "method": "season"}
        else:
            prev_season_query = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetEpisodes",
                "params": {
                    "filter": {
                        "and": [
                            {"field": "tvshow", "operator": "is", "value": tvshowtitle},
                            {"field": "season", "operator": fallback_season_operator, "value": str(season)}
                        ]
                    },
                    "properties": ["season"],
                    "sort": {"order": "descending", "method": "season"},
                    "limits": {"start": 0, "end": 1}
                },
                "id": 1
            }
            response_prev = xbmc.executeJSONRPC(json.dumps(prev_season_query))
            data_prev = json.loads(response_prev)
            prev_episodes = data_prev.get("result", {}).get("episodes", [])
            if not prev_episodes:
                return None
            prev_season_num = prev_episodes[0]["season"]
            filters_prev_season = {
                "and": [
                    {"field": "tvshow", "operator": "is", "value": tvshowtitle},
                    {"field": "season", "operator": "is", "value": str(prev_season_num)}
                ]
            }
            query["params"]["filter"] = filters_prev_season
            query["params"]["sort"] = {"order": "descending", "method": "episode"}

        response = xbmc.executeJSONRPC(json.dumps(query))
        data = json.loads(response)
        episodes = data.get("result", {}).get("episodes", [])
        if episodes:
            return episodes[0]["file"]
    except Exception as e:
        log(f"Fehler bei klassischer Episode-Suche ({direction}): {repr(e)}", level='ERROR')
    return None

def find_episode(tvshowtitle, season, episode, direction="next"):
    tvshowid = get_tvshowid_by_title(tvshowtitle)
    if tvshowid:
        file = get_episode_upnext(tvshowid, season, episode, direction)
        if file:
            log(f"{direction.capitalize()} Episode via TVShowID (Up Next Style) gefunden.", "DEBUG")
            return file
    file = get_episode_fallback(tvshowtitle, season, episode, direction)
    if file:
        log(f"{direction.capitalize()} Episode klassisch per Serienname gefunden.", "DEBUG")
        return file
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

def is_kodi_library_episode(filepath):
    return filepath and not filepath.lower().startswith("plugin://")

def jump_to_end_and_wait(player):
    try:
        total_time = player.getTotalTime()
        if total_time > 1:
            seek_time = max(0, total_time - 1)
            player.seekTime(seek_time)
            xbmc.sleep(500)
            log("Habe ans Episodenende gespult und 0,5 Sekunden gewartet.", "DEBUG")
    except Exception as e:
        log(f"Fehler beim Vorspulen ans Ende: {repr(e)}", "ERROR")

def collect_episode_info():
    info = {
        "tvshowtitle": xbmc.getInfoLabel('VideoPlayer.TVShowTitle'),
        "season": xbmc.getInfoLabel('VideoPlayer.Season'),
        "episode": xbmc.getInfoLabel('VideoPlayer.Episode'),
        "file": xbmc.getInfoLabel('VideoPlayer.Filenameandpath')
    }
    log(f"Aktuelle Wiedergabe: {info}", level='DEBUG')
    return info

def extract_season_episode_from_path(path):
    if not path:
        return None, None
    match = re.search(r'[Ss](\d{1,2})[Eex](\d{1,2})', path)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def guess_next_episode_path(current_path, direction="next"):
    season, episode = extract_season_episode_from_path(current_path)
    if season is None or episode is None:
        return None

    if direction == "next":
        next_season, next_episode = season, episode + 1
    else:
        next_season, next_episode = season, episode - 1

    def build_pattern(s, e):
        return re.sub(r'([Ss])(\d{1,2})([Eex])(\d{1,2})',
                      r'\1{:02d}\3{:02d}'.format(s, e),
                      current_path, count=1)

    test_path = build_pattern(next_season, next_episode)

    if test_path != current_path:
        log(f"Versuche staffelübergreifend per Dateiname: {test_path}", "INFO")
        return test_path
    return None

def fast_mark_as_watched(tvshowtitle, season, episode):
    try:
        episodeid = get_episodeid_from_kodi_library(tvshowtitle, season, episode)
        if episodeid:
            set_episode_playcount(episodeid, 1)
            log("Fast mark as watched (Up Next Style) erfolgreich.", "DEBUG")
            return True
        else:
            log("Fast mark as watched: Keine episodeid gefunden.", "WARNING")
    except Exception as e:
        log(f"Fehler bei fast mark as watched: {repr(e)}", "ERROR")
    return False

def fast_jump_in_playlist(direction="next"):
    try:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pos = playlist.getposition()
        if pos == -1:
            return False
        if direction == "next" and pos + 1 < playlist.size():
            xbmc.executebuiltin(f"Playlist.PlayOffset(Video, {pos+1})")
            log("Playlist-Jump (next) erfolgreich.", "DEBUG")
            return True
        elif direction == "previous" and pos - 1 >= 0:
            xbmc.executebuiltin(f"Playlist.PlayOffset(Video, {pos-1})")
            log("Playlist-Jump (previous) erfolgreich.", "DEBUG")
            return True
        return False
    except Exception as e:
        log(f"Fehler beim Playlist-Jump: {repr(e)}", "ERROR")
        return False

def main():
    try:
        direction = "next"
        if len(sys.argv) > 1 and sys.argv[1].lower() in ["previous", "next"]:
            direction = sys.argv[1].lower()

        log(f"Script gestartet, Richtung: {direction}", level='INFO')
        player = xbmc.Player()
        if not player.isPlaying():
            log("Kein aktives Playback. Keine Episode kann gestartet werden.", level='WARNING')
            show_error_dialog("Kein aktives Playback – keine Episode kann gestartet werden.")
            return

        info = collect_episode_info()
        tvshowtitle = info["tvshowtitle"]
        season = info["season"]
        episode = info["episode"]
        current_file = info["file"]

        # --- SCHNELLSTE METHODE: Playlist-Jump ---
        # (funktioniert nur, wenn aktuelle Wiedergabe Teil einer Playlist ist)
        fastjump_success = fast_jump_in_playlist(direction)
        if fastjump_success:
            # Playcount/Status setzen, falls möglich
            if direction == "next" and is_kodi_library_episode(current_file):
                fast_mark_as_watched(tvshowtitle, season, episode)
            elif direction == "previous" and is_kodi_library_episode(current_file):
                episodeid = get_episodeid_from_kodi_library(tvshowtitle, season, episode)
                if episodeid:
                    set_episode_playcount(episodeid, 0)
            return  # fertig, alles erledigt!

        # --- FALLBACK: Library/Episoden-Findung wie zuvor ---
        episode_path = None
        if tvshowtitle and season.isdigit() and episode.isdigit():
            episode_path = find_episode(tvshowtitle, int(season), int(episode), direction)
            if episode_path:
                log(f"Episode ({direction}) via Kodi-Library gefunden: {episode_path}", level='INFO')

        # --- Weiterer Fallback: SxxExx im Pfad suchen ---
        if not episode_path:
            episode_path = guess_next_episode_path(current_file, direction)
            if episode_path and episode_path != current_file:
                log(f"Episode ({direction}) staffelübergreifend per Dateinamen geraten: {episode_path}", level='INFO')

        # Kein Treffer?
        if not episode_path:
            log(f"{direction.capitalize()} Episode konnte nicht gefunden werden.", level='ERROR')
            label = "Nächste" if direction == "next" else "Vorherige"
            msg = f"{label} Episode konnte nicht gefunden werden. Vermutlich ist das {'Staffel-' if season else ''}Finale erreicht."
            show_error_dialog(msg)
            return

        # --- Markieren (Fallback) ---
        if direction == "next":
            marked = False
            if is_kodi_library_episode(current_file):
                marked = fast_mark_as_watched(tvshowtitle, season, episode)
            if not marked:
                jump_to_end_and_wait(player)
        elif direction == "previous":
            if is_kodi_library_episode(current_file):
                episodeid = get_episodeid_from_kodi_library(tvshowtitle, season, episode)
                if episodeid:
                    set_episode_playcount(episodeid, 0)

        # --- Episode abspielen (Fallback) ---
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
