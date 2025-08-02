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


def get_localized_error_message(code):
    language = xbmc.getLanguage(xbmc.ISO_639_1)[:2]

    translations = {
        "no_playback": {
            "de": "Kein aktives Playback – keine Episode kann gestartet werden.",
            "en": "No active playback – cannot start episode.",
            "fr": "Aucune lecture active – impossible de lancer l'épisode.",
            "es": "No hay reproducción activa: no se puede iniciar el episodio.",
            "it": "Nessuna riproduzione attiva: impossibile avviare l'episodio.",
            "tr": "Etkin bir oynatma yok – bölüm başlatılamıyor.",
            "ru": "Нет активного воспроизведения — не удаётся запустить эпизод."
        },
        "play_error": {
            "de": "Fehler beim Starten der Episode.",
            "en": "Error starting the episode.",
            "fr": "Erreur lors du démarrage de l'épisode.",
            "es": "Error al iniciar el episodio.",
            "it": "Errore durante l'avvio dell'episodio.",
            "tr": "Bölüm başlatılırken hata oluştu.",
            "ru": "Ошибка при запуске эпизода."
        },
        "unexpected_error": {
            "de": "Unerwarteter Fehler. Siehe Logdatei für Details.",
            "en": "Unexpected error. See log file for details.",
            "fr": "Erreur inattendue. Voir le journal pour plus de détails.",
            "es": "Error inesperado. Consulta el registro para más detalles.",
            "it": "Errore imprevisto. Vedi il file di log per i dettagli.",
            "tr": "Beklenmeyen hata. Ayrıntılar için günlük dosyasına bakın.",
            "ru": "Неожиданная ошибка. См. журнал для подробностей."
        }
    }

    return (
            translations.get(code, {}).get(language)
            or translations.get(code, {}).get("en")
            or "Error"
    )


def get_localized_episode_not_found_message(direction):
    language = xbmc.getLanguage(xbmc.ISO_639_1)[:2]

    translations = {
        "next": {
            "de": "Keine weitere Episode gefunden.",
            "fr": "Aucun autre épisode trouvé.",
            "es": "No se encontró otro episodio.",
            "it": "Nessun altro episodio trovato.",
            "tr": "Başka bölüm bulunamadı.",
            "ru": "Другой эпизод не найден.",
            "en": "No further episode found."
        },
        "previous": {
            "de": "Keine vorherige Episode gefunden.",
            "fr": "Aucun épisode précédent trouvé.",
            "es": "No se encontró el episodio anterior.",
            "it": "Nessun episodio precedente trovato.",
            "tr": "Önceki bölüm bulunamadı.",
            "ru": "Предыдущий эпизод не найден.",
            "en": "No previous episode found."
        }
    }

    return (
            translations.get(direction, {}).get(language)
            or translations.get(direction, {}).get("en")
            or "Episode not found."
    )


def log(msg, level='INFO'):
    xbmc.log(f'[{ADDON_ID}] {msg}', LOGLEVELS.get(level.upper(), xbmc.LOGINFO))


def show_error_dialog(message):
    xbmcgui.Dialog().notification("Jellyskip", message, xbmcgui.NOTIFICATION_ERROR)


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


def quick_end_seek(player):
    """Schnellere Version, die nur zum Ende springt, ohne lange zu warten"""
    try:
        total_time = player.getTotalTime()
        if total_time > 1:
            seek_time = max(0, total_time - 0.5)  # Fast am Ende
            player.seekTime(seek_time)
            # Kurze Wartezeit um sicherzustellen, dass Kodi das als Ende erkennt
            xbmc.sleep(300)  # 300ms sollten ausreichen statt 1500ms
            log("Zum Ende der Episode gesprungen.", "DEBUG")
    except Exception as e:
        log(f"Fehler beim Vorspulen ans Ende: {repr(e)}", "ERROR")


def mark_episode_watched(tvshowtitle, season, episode):
    """Synchrone, aber optimierte Funktion zum Markieren einer Episode als gesehen"""
    try:
        if tvshowtitle and season.isdigit() and episode.isdigit():
            episodeid = get_episodeid_from_kodi_library(tvshowtitle, season, episode)
            if episodeid:
                success = set_episode_playcount(episodeid, 1)
                log(f"Playcount synchron gesetzt: {success}", "INFO")
                return success
        return False
    except Exception as e:
        log(f"Fehler beim Setzen des Playcount: {repr(e)}", "ERROR")
        return False


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


def play_episode_via_kodi_command(episode_path):
    """Optimierte Version zum Starten einer Episode über Kodi-Befehle"""
    try:
        # Verkürzte Wartezeiten
        xbmc.executebuiltin("PlayerControl(Stop)")
        xbmc.sleep(250)  # von 500ms auf 250ms reduziert

        xbmc.executebuiltin("Dialog.Close(all,true)")
        xbmc.sleep(100)  # von 200ms auf 100ms reduziert

        # Neue Episode starten
        xbmc.executebuiltin(f'PlayMedia("{episode_path}")')
        log(f"Episode über optimierten Kodi-Befehl gestartet: {episode_path}", level='INFO')
        return True
    except Exception as e:
        log(f"Fehler beim Ausführen des Kodi-Befehls: {e}", level='ERROR')
        return False


def skip_to_next_episode():
    """Optimierte, schnellere Version zum Springen zur nächsten Episode"""
    try:
        player = xbmc.Player()
        if not player.isPlaying():
            log("Kein aktives Playback. Keine Episode kann gestartet werden.", level='WARNING')
            show_error_dialog(get_localized_error_message("no_playback"))
            return

        info = collect_episode_info()
        tvshowtitle = info["tvshowtitle"]
        season = info["season"]
        episode = info["episode"]
        current_file = info["file"]

        # Vorbereitende Schritte schon mal ausführen
        xbmc.executebuiltin("Dialog.Close(all,true)")

        # Schnellere Pausenzeit
        if PAUSE_BEFORE_JUMP_SEC > 0:
            player.pause()
            xbmc.sleep(int(PAUSE_BEFORE_JUMP_SEC * 500))  # Verkürzte Wartezeit
            player.pause()  # Pause wieder aufheben

        # Optimierte Episode-Suche - schnellste Methoden zuerst
        episode_path = None

        # Methode 1: Playlist (am schnellsten)
        episode_path = get_episode_from_playlist("next")
        if episode_path:
            log(f"Episode (next) aus Playlist: {episode_path}", level='INFO')

        # Methode 2: TVShowID (wenn Playlist leer ist)
        if not episode_path and tvshowtitle and season.isdigit() and episode.isdigit():
            tvshowid = get_tvshowid_by_title(tvshowtitle)
            if tvshowid:
                episode_path = get_episode_from_kodi_library_by_tvshowid(tvshowid, season, episode, "next")
                if episode_path:
                    log(f"Episode (next) per TVShowID gefunden: {episode_path}", level='INFO')

        # Methode 3: Name (Fallback)
        if not episode_path and tvshowtitle and season.isdigit() and episode.isdigit():
            episode_path = get_episode_from_kodi_library(tvshowtitle, season, episode, "next")
            if episode_path:
                log(f"Episode (next) aus Kodi-Library (per Name): {episode_path}", level='INFO')

        # Methode 4: Dateiname-Muster (letzter Fallback)
        if not episode_path:
            episode_path = guess_next_episode_path(current_file, "next")
            if episode_path and episode_path != current_file:
                log(f"Episode (next) staffelübergreifend per Dateinamen geraten: {episode_path}", level='INFO')

        if not episode_path:
            log("Next Episode konnte nicht gefunden werden.", level='ERROR')
            msg = get_localized_episode_not_found_message("next")
            show_error_dialog(msg)
            return

        # Verbessertes Status-Handling
        if is_kodi_library_episode(current_file):
            # 1. Zum Ende der Episode springen
            quick_end_seek(player)
            # 2. Sicherstellen, dass Episode als gesehen markiert wird
            marked = mark_episode_watched(tvshowtitle, season, episode)
            if not marked:
                # Fallback: Warten um sicherzustellen, dass Kodi die Episode als gesehen erkennt
                log("Fallback-Methode: Warte um Episode als gesehen zu markieren", "INFO")
                xbmc.sleep(300)
        else:
            # Nur schnell zum Ende springen bei nicht-Bibliotheks-Dateien
            quick_end_seek(player)

        # Episode abspielen mit optimierter Methode
        try:
            success = play_episode_via_kodi_command(episode_path)

            # Fallback zur ursprünglichen Methode, falls die verbesserte fehlschlägt
            if not success:
                player.play(episode_path)
                log(f"Episode über Fallback-Methode gestartet: {episode_path}", level='INFO')

        except Exception as e:
            log(f"Fehler beim Starten der Episode: {repr(e)}", level='ERROR')
            show_error_dialog(get_localized_error_message("play_error"))

    except Exception as e:
        tb = traceback.format_exc()
        log(f"Exception im skip_to_next_episode: {repr(e)}\n{tb}", level='ERROR')
        show_error_dialog(get_localized_error_message("unexpected_error"))


# -- Ende: Robuste Episode-Jumper-Logik --

class SkipSegmentDialogue(xbmcgui.WindowXMLDialog):

    def __init__(self, xmlFile, resourcePath, seek_time_seconds, segment_type):
        try:
            # super().__init__(xmlFile, resourcePath)  # Python 3-style Initialisierung, falls benötigt
            self.seek_time_seconds = seek_time_seconds
            self.segment_type = segment_type
            self.player = xbmc.Player()
            self.closing = False  # Flag zum Vermeiden von Doppel-Schließung

            # Vorausladen der nächsten Episode, wenn es sich um ein Outro handelt
            self.next_episode_path = None
            if str(segment_type).lower() == "outro":
                utils.run_threaded(self.preload_next_episode, delay=0.2, kwargs={})
        except Exception as e:
            LOG.error(f"Init failed: {e}")
            self.seek_time_seconds = 0
            self.segment_type = ""
            self.player = None
            self.closing = False
            self.next_episode_path = None

    def preload_next_episode(self):
        """Sucht die nächste Episode im Voraus mit verbesserter Performance"""
        try:
            # Frühe Prüfung, ob Dialog noch relevant ist
            if self.closing or not self.player or not self.player.isPlayingVideo():
                LOG.info("Preload abgebrochen - Dialog bereits geschlossen oder kein Video")
                return

            info = collect_episode_info()
            tvshowtitle = info["tvshowtitle"]
            season = info["season"]
            episode = info["episode"]
            current_file = info["file"]

            # Optimierte Suche: Priorisierte Reihenfolge für bessere Performance
            methods = [
                # 1. Playlist (am schnellsten)
                lambda: get_episode_from_playlist("next"),

                # 2. TVShowID (wenn verfügbar)
                lambda: (get_episode_from_kodi_library_by_tvshowid(get_tvshowid_by_title(tvshowtitle), season, episode,
                                                                   "next")
                         if tvshowtitle and season.isdigit() and episode.isdigit() and get_tvshowid_by_title(
                    tvshowtitle) else None),

                # 3. Kodi-Library nach Namen
                lambda: (get_episode_from_kodi_library(tvshowtitle, season, episode, "next")
                         if tvshowtitle and season.isdigit() and episode.isdigit() else None),

                # 4. Dateiname-Muster (letzter Fallback)
                lambda: guess_next_episode_path(current_file, "next")
            ]

            # Methoden der Reihe nach probieren bis eine erfolgreich ist
            for method in methods:
                if self.closing:  # Zwischenprüfung, ob Dialog noch relevant ist
                    return

                path = method()
                if path:
                    self.next_episode_path = path
                    LOG.info(f"Nächste Episode vorgeladen: {self.next_episode_path}")
                    return

            LOG.info("Keine nächste Episode gefunden beim Vorladen")
        except Exception as e:
            LOG.error(f"Preload next episode failed: {e}")
            self.next_episode_path = None

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
                    "de": "Intro", "fr": "l'intro", "es": "la introducción", "it": "l'introduzione", "en": "Intro"
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
            # Thread-sicheres Setzen des closing-Flags
            if hasattr(self, 'closing') and not self.closing:
                self.closing = True
                xbmc.executebuiltin("NotifyAll(service.jellyskip, Jellyskip.DialogueClosed, {})")

                # Dialog auf dem Haupt-Thread schließen
                utils.run_threaded(self._safe_close, delay=0.05, kwargs={})
        except Exception as e:
            LOG.error(f"on_automatic_close failed: {e}")

    def _safe_close(self):
        """Sichere Methode zum Schließen des Dialogs auf dem Haupt-Thread"""
        try:
            self.close()
            LOG.info("Dialog sicher geschlossen")
        except Exception as e:
            LOG.error(f"_safe_close failed: {e}")

    def show_status_notification(self, message, success=True):
        """Zeigt kurze Status-Benachrichtigung ohne Dialog-Unterbrechung"""
        try:
            icon = xbmcgui.NOTIFICATION_INFO if success else xbmcgui.NOTIFICATION_WARNING
            xbmcgui.Dialog().notification(
                "JellySkip",
                message,
                icon,
                time=1500,  # Kurze Anzeigezeit
                sound=False  # Kein Sound für bessere UX
            )
        except Exception as e:
            LOG.error(f"Status notification failed: {e}")

    def onAction(self, action):
        try:
            if action == ACTION_PREVIOUS_MENU or action == ACTION_BACK:
                if not self.closing:
                    self.closing = True
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
                if not self.closing:
                    self.closing = True
                    self.close()
                xbmc.executebuiltin("NotifyAll(service.jellyskip, Jellyskip.DialogueClosed, {})")
                return

            if control == OK_BUTTON:
                try:
                    # Aktuellen Dateipfad speichern für späteren Vergleich
                    current_file = self.player.getPlayingFile() if self.player.isPlayingVideo() else ""

                    total_time = self.player.getTotalTime()
                    remaining_seconds = total_time - self.seek_time_seconds

                    if remaining_seconds < MIN_REMAINING_SECONDS:
                        self.player.seekTime(total_time - MIN_REMAINING_SECONDS)
                    else:
                        self.player.seekTime(self.seek_time_seconds)
                except Exception as e:
                    LOG.error(f"Seek failed: {e}")

                # Nur für Outro: Optimierte Episodejumper-Logik
                if str(self.segment_type).lower() == "outro":
                    LOG.info("Starting optimized episode transition for outro")

                    # Episodeninfo sammeln, bevor Dialog geschlossen wird
                    info = collect_episode_info()
                    tvshowtitle = info["tvshowtitle"]
                    season = info["season"]
                    episode = info["episode"]

                    # Dialog schließen BEVOR wir zur nächsten Episode wechseln
                    # um Verzögerungen in der UI zu vermeiden
                    if not self.closing:
                        self.closing = True
                        self.close()
                        xbmc.executebuiltin("NotifyAll(service.jellyskip, Jellyskip.DialogueClosed, {})")

                    # Aktuelle Episode als gesehen markieren im Hintergrund
                    if is_kodi_library_episode(current_file):
                        # Schnelle Methode zum Markieren als gesehen
                        quick_end_seek(self.player)
                        utils.run_threaded(
                            lambda: mark_episode_watched(tvshowtitle, season, episode),
                            delay=0.1,
                            kwargs={}
                        )

                    # Wenn wir die nächste Episode vorgeladen haben, direkt verwenden
                    if self.next_episode_path:
                        LOG.info(f"Verwende vorgeladene Episode: {self.next_episode_path}")
                        play_episode_via_kodi_command(self.next_episode_path)
                    else:
                        # Fallback zur Standardsuche
                        LOG.info("Keine vorgeladene Episode gefunden, starte Suche")
                        skip_to_next_episode()
                    return

                # Für alle anderen Fälle normal schließen
                if not self.closing:
                    self.closing = True
                    self.close()
                xbmc.executebuiltin("NotifyAll(service.jellyskip, Jellyskip.DialogueClosed, {})")

        except Exception as e:
            LOG.error(f"onClick failed: {e}")
            if not self.closing:
                self.closing = True
                self.close()
            xbmc.executebuiltin("NotifyAll(service.jellyskip, Jellyskip.DialogueClosed, {})")
