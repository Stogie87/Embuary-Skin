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
            LOG.info('JellySkipMonitor: reset itemid')
        except Exception as e:
            LOG.error(f"_event_handler_player_stop failed: {e}")

    def _event_handler_player_start(self, **_kwargs):
        LOG.info('JellySkipMonitor: player start event')
        try:
            jf_hack.reset_itemid()
            dialogue_handler.cancel_scheduled()
        except Exception as e:
            LOG.error(f"_event_handler_player_start failed: {e}")

    def _event_handler_jellyskip_dialogue_closed(self, **_kwargs):
        LOG.info('JellySkipMonitor: player dialogue closed event')
        try:
            # User closed dialogue, now we want to start tracking only the next upcoming segment
            self.start_tracking(only_upcoming=True)
        except Exception as e:
            LOG.error(f"_event_handler_jellyskip_dialogue_closed failed: {e}")

    EVENTS_MAP = {
        'Other.UserDataChanged': jf_hack.event_handler_jellyfin_userdatachanged,
        'Other.Jellyskip.DialogueClosed': _event_handler_jellyskip_dialogue_closed,
        # 'Player.OnPause': _event_handler_player_change_playback,
        'Player.OnResume': _event_handler_player_change_playback,
        # 'Player.OnSpeedChanged': _event_handler_player_change_playback,
        'Player.OnSeek': _event_handler_player_change_playback,
        'Player.OnStop': _event_handler_player_stop,
        'Player.OnPlay': _event_handler_player_start,
        'Player.OnAVChange': _event_handler_player_change_playback,
    }

    def stop(self):
        LOG.info('Stopping JellySkipMonitor')

    def onNotification(self, sender, method, data=None):
        """
        Handler for Kodi events and data transfer from plugins.
        """
        try:
            sender = utils.from_bytes(sender)
            method = utils.from_bytes(method)
            data = utils.from_bytes(data) if data else ''
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
