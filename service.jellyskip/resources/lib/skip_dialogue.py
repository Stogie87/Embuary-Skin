import xbmcgui
import xbmc
import xbmcaddon
import json
import re
import traceback
import time
import helper.utils as utils
from helper import LazyLogger

OK_BUTTON = 2101
ACTION_PREVIOUS_MENU = 10
ACTION_BACK = 92
MIN_REMAINING_SECONDS = 5
LOG = LazyLogger(__name__)

# -- Start: Robuste Episode-Jumper-Logik (direkt eingebaut) --
PAUSE_BEFORE_JUMP_SEC = 0.2
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

def get_episode_from_kodi_library_by_tvshowid(tvshowid, season, episode, direction="next"):
    try:
        query = {
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetEpisodes",
            "params": {
                "filter": {"field": "tvshowid", "operator": "is", "value": tvshowid},
                "properties": ["file", "season", "episode", "playcount"],
                "sort": {"order": "ascending", "method": "season", "ignorearticle": True}
            },
            "id": 1
        }
        query['params']['sort'] = {
            "order": "ascending",
            "method": "episode",
            "ignorearticle": True
        }
        response = xbmc.executeJSONRPC(json.dumps(query))
        data = json.loads(response)
        episodes = data.get("result", {}).get("episodes", [])
        episodes = sorted(episodes, key=lambda x: (int(x["season"]), int(x["episode"])))
        for idx, ep in enumerate(episodes):
            if int(ep["season"]) == int(season) and int(ep["episode"]) == int(episode):
                next_idx = idx + 1 if direction == "next" else idx - 1
                if 0 <= next_idx < len(episodes):
                    return episodes[next_idx]["file"]
                else:
                    return None
        return None
    except Exception as e:
        log(f"Fehler beim Abrufen der Episode (TVShowID): {repr(e)}", level='ERROR')
        return None

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
        query['params']['sort'] = {
            "order": "ascending",
            "method": "episode",
            "ignorearticle": True
        }
        response = xbmc.executeJSONRPC(json.dumps(query))
        data = json.loads(response)
        episodes = data.get("result", {}).get("episodes", [])
        episodes = sorted(episodes, key=lambda x: (int(x["season"]), int(x["episode"])))
        for idx, ep in enumerate(episodes):
            if int(ep["season"]) == int(season) and int(ep["episode"]) == int(episode):
                next_idx = idx + 1 if direction == "next" else idx - 1
                if 0 <= next_idx < len(episodes):
                    return episodes[next_idx]["file"]
                else:
                    return None
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
        result = xbmc.executeJSONRPC(json.dumps(query))
        if '"error"' in result:
            log(f"SetEpisodeDetails Fehler: {result}", "ERROR")
            return False
        log(f"Setze playcount für episodeid {episodeid} auf {playcount}", "INFO")
        return True
    except Exception as e:
        log(f"Fehler beim Setzen des playcount: {repr(e)}", "ERROR")
        return False

def get_episode_from_playlist(direction="next"):
    try:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pos = playlist.getposition()
        if pos == -1:
            return None
        if direction == "next" and pos + 1 < playlist.size():
            return playlist[pos + 1].getfilename()
        elif direction == "previous" and pos - 1 >= 0:
            return playlist[pos - 1].getfilename()
        return None
    except Exception as e:
        log(f"Fehler beim Playlist-Check: {repr(e)}", level='ERROR')
        return None

def is_kodi_library_episode(filepath):
    return filepath and not filepath.lower().startswith("plugin://")

def jump_to_end_and_wait(player):
    try:
        total_time = player.getTotalTime()
        if total_time > 1:
            seek_time = max(0, total_time - 1)
            player.seekTime(seek_time)
            xbmc.sleep(1500)
            log("Habe 1,5 Sekunden vor Episodenende gespult und gewartet.", "DEBUG")
    except Exception as e:
        log(f"Fehler beim Vorspulen ans Ende: {repr(e)}", "ERROR")

def pause_and_wait(player, seconds):
    try:
        player.pause()
        log(f"Playback pausiert, warte {seconds} Sekunden...", "DEBUG")
        xbmc.sleep(int(seconds * 1000))
    except Exception as e:
        log(f"Fehler beim Pausieren: {repr(e)}", "ERROR")

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
        log(f"Versuche staffelübergreifend: {test_path}", "INFO")
        return test_path
    return None

def skip_to_next_episode():
    try:
        direction = "next"
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

        episode_path = None

        pause_and_wait(player, PAUSE_BEFORE_JUMP_SEC)

        tvshowid = get_tvshowid_by_title(tvshowtitle)
        if tvshowid and season.isdigit() and episode.isdigit():
            episode_path = get_episode_from_kodi_library_by_tvshowid(tvshowid, season, episode, direction)
            if episode_path:
                log(f"Episode ({direction}) per TVShowID gefunden: {episode_path}", level='INFO')

        if not episode_path and tvshowtitle and season.isdigit() and episode.isdigit():
            episode_path = get_episode_from_kodi_library(tvshowtitle, season, episode, direction)
            if episode_path:
                log(f"Episode ({direction}) aus Kodi-Library (per Name): {episode_path}", level='INFO')

        if not episode_path:
            episode_path = get_episode_from_playlist(direction)
            if episode_path:
                log(f"Episode ({direction}) aus Playlist: {episode_path}", level='INFO')

        if not episode_path:
            episode_path = guess_next_episode_path(current_file, direction)
            if episode_path and episode_path != current_file:
                log(f"Episode ({direction}) staffelübergreifend per Dateinamen geraten: {episode_path}", level='INFO')

        if not episode_path:
            log(f"{direction.capitalize()} Episode konnte nicht gefunden werden.", level='ERROR')
            label = "Nächste" if direction == "next" else "Vorherige"
            msg = f"{label} Episode konnte nicht gefunden werden. Vermutlich ist das {'Staffel-' if season else ''}Finale erreicht."
            show_error_dialog(msg)
            return

        # --- Status-Handling ---
        marked = False
        if is_kodi_library_episode(current_file):
            episodeid = get_episodeid_from_kodi_library(tvshowtitle, season, episode)
            if episodeid:
                marked = set_episode_playcount(episodeid, 1)
        if not marked:
            jump_to_end_and_wait(player)

        # --- Episode abspielen ---
        try:
            player.play(episode_path)
            log(f"Gestartet: {episode_path}", level='INFO')
        except Exception as e:
            log(f"Fehler beim Starten der Episode: {repr(e)}", level='ERROR')
            show_error_dialog("Fehler beim Starten der Episode.")

    except Exception as e:
        tb = traceback.format_exc()
        log(f"Exception im skip_to_next_episode: {repr(e)}\n{tb}", level='ERROR')
        show_error_dialog("Unerwarteter Fehler beim Überspringen. Siehe Logdatei.")

# -- Ende: Robuste Episode-Jumper-Logik --

class SkipSegmentDialogue(xbmcgui.WindowXMLDialog):

    def __init__(self, xmlFile, resourcePath, seek_time_seconds, segment_type):
        try:
            self.seek_time_seconds = seek_time_seconds
            self.segment_type = segment_type
            self.player = xbmc.Player()
        except Exception as e:
            LOG.error(f"Init failed: {e}")
            self.seek_time_seconds = 0
            self.segment_type = ""
            self.player = None

    def onInit(self):
        try:
            language = xbmc.getLanguage(xbmc.ISO_639_1)

            skip_translations = {
                "de": "Überspringe", "fr": "Passer", "es": "Saltar", "it": "Salta",
                "nl": "Overslaan", "pt": "Pular", "pl": "Pomiń", "sv": "Hoppa över",
                "ru": "Пропустить", "tr": "Atla", "en": "Skip"
            }
            segment_translations = {
                "intro": {
                    "de": "Intro", "fr": "l’intro", "es": "la introducción", "it": "l’introduzione", "en": "Intro"
                },
                "ads": {
                    "de": "Werbung", "fr": "la pub", "es": "los anuncios", "en": "Ads"
                },
                "outro": {
                    "de": "Outro", "fr": "la fin", "es": "el outro", "en": "Outro"
                }
            }

            prefix = skip_translations.get(language, "Skip")
            segment_key = str(self.segment_type or "").lower()
            translated_segment = segment_translations.get(segment_key, {}).get(language, self.segment_type)

            skip_label = f"{prefix} {translated_segment}"
            try:
                skip_button = self.getControl(OK_BUTTON)
                skip_button.setLabel(skip_label)
            except Exception as e:
                LOG.error(f"Set button label failed: {e}")

        except Exception as e:
            LOG.error(f"onInit failed: {e}")

        self.schedule_close_action()

    def get_seconds_till_segment_end(self):
        try:
            if not self.player:
                LOG.error("Player not initialized")
                return 0
            return max(0, self.seek_time_seconds - self.player.getTime())
        except Exception as e:
            LOG.error(f"get_seconds_till_segment_end failed: {e}")
            return 0

    def schedule_close_action(self):
        try:
            seconds_till_segment_end = self.get_seconds_till_segment_end()
            if seconds_till_segment_end > 0:
                utils.run_threaded(self.on_automatic_close, delay=seconds_till_segment_end, kwargs={})
        except Exception as e:
            LOG.error(f"schedule_close_action failed: {e}")

    def on_automatic_close(self):
        try:
            self.close()
            LOG.info("JellySkip: Auto closing dialogue")
            xbmc.executebuiltin("NotifyAll(service.jellyskip, Jellyskip.DialogueClosed, {})")
        except Exception as e:
            LOG.error(f"on_automatic_close failed: {e}")

    def onAction(self, action):
        try:
            if action == ACTION_PREVIOUS_MENU or action == ACTION_BACK:
                self.close()
        except Exception as e:
            LOG.error(f"onAction failed: {e}")

    def onControl(self, control):
        pass

    def onFocus(self, control):
        pass

    def onClick(self, control):
        try:
            if not self.player or not self.player.isPlaying():
                LOG.warn("onClick: Player not playing, closing dialog")
                self.close()
                return

            if control == OK_BUTTON:
                try:
                    total_time = self.player.getTotalTime()
                    remaining_seconds = total_time - self.seek_time_seconds

                    if remaining_seconds < MIN_REMAINING_SECONDS:
                        self.player.seekTime(total_time - MIN_REMAINING_SECONDS)
                    else:
                        self.player.seekTime(self.seek_time_seconds)
                except Exception as e:
                    LOG.error(f"Seek failed: {e}")

                # Nur für Outro: Robuste Episodejumper-Logik direkt starten!
                if str(self.segment_type).lower() == "outro":
                    skip_to_next_episode()

            self.close()
        except Exception as e:
            LOG.error(f"onClick failed: {e}")
