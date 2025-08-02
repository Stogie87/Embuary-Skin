import xbmc
import xbmcaddon

from helper import LazyLogger
import player
import helper.utils as utils

from jellyfin.jellyfin_grabber import JellyfinHack
from skip_dialogue import SkipSegmentDialogue
from dialogue_handler import dialogue_handler

addonInfo = xbmcaddon.Addon().getAddonInfo
addonPath = utils.translate_path(addonInfo('path'))

jf_hack = JellyfinHack()
LOG = LazyLogger(__name__)

class JellySkipMonitor(xbmc.Monitor):

    def __init__(self):
        try:
            xbmc.Monitor.__init__(self)
            self.player = player.JellySkipPlayer(self)
            LOG.info('Init monitor')
        except Exception as e:
            LOG.error(f"Monitor init failed: {e}")
            self.player = None

    def start(self, **kwargs):
        LOG.info('Starting JellySkipMonitor')
        try:
            while not self.abortRequested():
                self.waitForAbort(1)
        except Exception as e:
            LOG.error(f"Error in main loop: {e}")
        self.stop()

    def _event_handler_player_change_playback(self, **_kwargs):
        LOG.info('JellySkipMonitor: player general event')
        try:
            self.start_tracking()
        except Exception as e:
            LOG.error(f"_event_handler_player_change_playback failed: {e}")

    def _event_handler_player_stop(self, **_kwargs):
        LOG.info('JellySkipMonitor: player stop event')
        try:
            jf_hack.reset_itemid()
            dialogue_handler.cancel_scheduled()
            if hasattr(self, 'outro_check_timer') and self.outro_check_timer:
                self.outro_check_timer.cancel()
                self.outro_check_timer = None
            LOG.info('JellySkipMonitor: reset itemid')
        except Exception as e:
            LOG.error(f"_event_handler_player_stop failed: {e}")

    def _event_handler_player_start(self, **_kwargs):
        LOG.info('JellySkipMonitor: player start event')
        try:
            jf_hack.reset_itemid()
            dialogue_handler.cancel_scheduled()
            self.start_tracking()  # Diese Zeile hinzufügen
        except Exception as e:
            LOG.error(f"_event_handler_player_start failed: {e}")

    def _event_handler_jellyskip_dialogue_closed(self, **_kwargs):
        LOG.info('JellySkipMonitor: player dialogue closed event')
        try:
            # 1. Sofort tracking für das nächste Segment starten
            self.start_tracking(only_upcoming=True)

            # 2. Zusätzlich: Timer für erneute Überprüfung vor dem erwarteten Outro setzen
            player = xbmc.Player()
            if player.isPlayingVideo():
                total_time = player.getTotalTime()
                current_time = player.getTime()
                # 30 Sekunden vor Ende erneut prüfen (oder früher, falls Video kürzer ist)
                time_till_outro_check = max(1, total_time - current_time - 30)

                # Timer für erneute Überprüfung setzen
                self.outro_check_timer = utils.run_threaded(  # Hier Timer speichern
                    self.ensure_outro_tracking,
                    delay=time_till_outro_check,
                    kwargs={}
                )
                LOG.info(f"Scheduled outro check in {time_till_outro_check} seconds")
        except Exception as e:
            LOG.error(f"_event_handler_jellyskip_dialogue_closed failed: {e}")

    EVENTS_MAP = {
        'Other.UserDataChanged': jf_hack.event_handler_jellyfin_userdatachanged,
        'Other.Jellyskip.DialogueClosed': _event_handler_jellyskip_dialogue_closed,
        'Player.OnPause': _event_handler_player_change_playback,
        'Player.OnResume': _event_handler_player_change_playback,
        'Player.OnSpeedChanged': _event_handler_player_change_playback,
        'Player.OnSeek': _event_handler_player_change_playback,
        'Player.OnStop': _event_handler_player_stop,
        'Player.OnPlay': _event_handler_player_start,
        'Player.OnAVChange': _event_handler_player_change_playback,
    }

    def stop(self):
        LOG.info('Stopping JellySkipMonitor')

    def ensure_outro_tracking(self):
        """Spezielle Methode um sicherzustellen, dass das Outro-Segment erkannt wird"""
        try:
            if not self.player or not self.player.isPlayingVideo():
                LOG.info("Player nicht mehr aktiv, Outro-Check übersprungen")
                return

            # Prüfen, ob wir uns nahe am Ende befinden
            total_time = self.player.getTotalTime()
            current_time = self.player.getTime()

            # Wenn noch mehr als 35 Sekunden bis zum Ende, erneut timer setzen
            if total_time - current_time > 35:
                LOG.info(f"Noch {total_time - current_time} Sekunden bis Ende, verschiebe Outro-Check")
                time_till_outro_check = max(1, total_time - current_time - 30)
                self.outro_check_timer = utils.run_threaded(
                    self.ensure_outro_tracking,
                    delay=time_till_outro_check,
                    kwargs={}
                )
                return

            LOG.info("Performing scheduled outro check")
            # Hier explizit only_upcoming=False setzen, um alle Segmente zu prüfen
            self.start_tracking(only_upcoming=False)
        except Exception as e:
            LOG.error(f"ensure_outro_tracking failed: {e}")

    def onNotification(self, sender, method, data=None):
        """
        Handler for Kodi events and data transfer from plugins.
        """
        try:
            sender = utils.from_bytes(sender)
            method = utils.from_bytes(method)
            data = utils.from_bytes(data) if data else ''

            # NEU: Universeller Handler für alle Player-Events
            if method.startswith('Player.'):
                LOG.info(f"Player Event erkannt: {method}")
                if method not in self.EVENTS_MAP:
                    LOG.info(f"Zusätzliches Player-Event abgefangen: {method}")
                    # Trigger start_tracking für jedes Player-Event
                    if self.player and self.player.isPlayingVideo():
                        self.start_tracking()

            handler = JellySkipMonitor.EVENTS_MAP.get(method)
            if not handler:
                LOG.debug(f"No handler for method {method}")
                return

            LOG.info(f"Notification: sender={sender}, method={method}, data={data}")

            # Handler-Aufruf in try/except hüllen
            try:
                handler(self, sender=sender, data=data)
            except Exception as e:
                LOG.error(f"Handler for method {method} failed: {e}")

            if method == 'Other.UserDataChanged':
                # Robust warten auf korrekte ItemID
                waited = 0
                while not jf_hack.has_itemid():
                    self.waitForAbort(1)
                    waited += 1
                    if waited > 10:  # nach 10 Sekunden abbrechen
                        LOG.error("Timeout: No itemid available after 10s")
                        return

                LOG.info('JellySkipMonitor: getting media segments')

                try:
                    if not self.player or not self.player.isPlayingVideo() or not jf_hack.has_itemid():
                        LOG.warn("Not playing video or no itemid after event")
                        return

                    jf_hack._fetch_media_segments()
                    self.start_tracking()
                except Exception as e:
                    LOG.error(f"Fetching media segments failed: {e}")

        except Exception as e:
            LOG.error(f"onNotification failed: {e}")

    def start_tracking(self, only_upcoming=False):
        try:
            if not self.player or not self.player.isPlayingVideo():
                LOG.info('Not playing video')
                return

            time_seconds = 0
            duration_seconds = 0
            try:
                time_seconds = self.player.getTime()
                duration_seconds = self.player.getTotalTime()
            except Exception as e:
                LOG.error(f"Failed to get player times: {e}")

            try:
                media_segments = jf_hack.get_media_segments()
            except Exception as e:
                LOG.error(f"Failed to get media segments: {e}")
                media_segments = None

            if not media_segments:
                LOG.info('No media segments')
                # Close any open dialogues, if any
                try:
                    dialogue_handler.close_gui()
                except Exception as e:
                    LOG.error(f"dialogue_handler.close_gui() failed: {e}")
                return

            LOG.info(f"Start tracking: time={time_seconds}, duration={duration_seconds}")

            try:
                next_item = media_segments.get_next_item(time_seconds, only_upcoming)
            except Exception as e:
                LOG.error(f"media_segments.get_next_item failed: {e}")
                next_item = None

            if not next_item:
                # Close any open dialogues, if any
                try:
                    dialogue_handler.close_gui()
                except Exception as e:
                    LOG.error(f"dialogue_handler.close_gui() failed: {e}")
                LOG.info('Stopping all dialogue, because no next item')
                return

            LOG.info(f"Next item: {next_item}")

            try:
                dialogue_handler.schedule_skip_gui(next_item, time_seconds)
            except Exception as e:
                LOG.error(f"dialogue_handler.schedule_skip_gui failed: {e}")

        except Exception as e:
            LOG.error(f"start_tracking failed: {e}")
