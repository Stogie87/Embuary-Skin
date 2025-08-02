import xbmc
import xbmcaddon
import helper.utils as utils
import time

from skip_dialogue import SkipSegmentDialogue
from helper import LazyLogger
from jellyfin.media_segments import MediaSegmentItem

addonInfo = xbmcaddon.Addon().getAddonInfo
addonPath = utils.translate_path(addonInfo('path'))

LOG = LazyLogger(__name__)
SECOND_PADDING = 1
MIN_DIALOGUE_VISIBLE = 2  # Mindestanzeigezeit in Sekunden für Dialog
POSITION_TOLERANCE = 1.5  # Toleranzzeitfenster für Segmenterkennung


def get_settings():
    addon = xbmcaddon.Addon()
    enabled = addon.getSettingBool("enabled")
    skip_intro = addon.getSettingBool("skip_intro")
    skip_outro = addon.getSettingBool("skip_outro")
    return enabled, skip_intro, skip_outro


class DialogueHandler:

    def __init__(self):  # Python-Standard-Namenskonvention
        self.dialogue = None
        self.scheduled_thread = None
        self.last_item = None
        self.dialogue_opened_at = 0

    def schedule_skip_gui(self, item: MediaSegmentItem, current_seconds):
        try:
            # --- Settings-Auswertung ---
            enabled, skip_intro, skip_outro = get_settings()
            if not enabled:
                LOG.info("schedule_skip_gui: Plugin deaktiviert – kein Dialog.")
                self.close_gui()  # Dialog schließen, wenn Plugin deaktiviert
                return

            if not item:
                LOG.warn("schedule_skip_gui: No item provided.")
                return

            if item:
                seg_type = item.get_segment_type_display().lower()
                if seg_type == "intro" and not skip_intro:
                    LOG.info("schedule_skip_gui: Intro-Skip deaktiviert – kein Dialog.")
                    return
                if seg_type == "outro" and not skip_outro:
                    LOG.info("schedule_skip_gui: Outro-Skip deaktiviert – kein Dialog.")
                    return

            self.cancel_scheduled()

            # Prüfe ob wir gerade außerhalb des Segments sind und resette das Flag, damit ein erneuter Eintritt den Dialog wieder anzeigt
            if self.last_item and not self.is_last_item_segment() and self.dialogue:
                LOG.info(
                    f"Closing dialogue for {self.last_item.get_segment_type_display()} at {self.last_item.get_start_seconds()} as it is not currently playing")
                self.close_gui()

            # --- NEU: Setze last_item zurück, wenn nicht mehr im Segment ---
            if self.last_item and not self.is_last_item_segment():
                self.last_item = None

            if item.get_end_seconds() < current_seconds - POSITION_TOLERANCE:
                LOG.info(f"schedule_skip_gui: Already past segment {item}")
                return

            if item.get_start_seconds() - POSITION_TOLERANCE <= current_seconds <= item.get_end_seconds() + POSITION_TOLERANCE:
                self.open_gui(item)
            else:
                seconds_till_start = item.get_start_seconds() - current_seconds
                try:
                    self.scheduled_thread = utils.run_threaded(
                        self.on_gui_scheduled,
                        delay=max(0, seconds_till_start) + SECOND_PADDING,
                        kwargs={'item': item}
                    )
                    LOG.info(
                        f"Scheduled dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()} in {seconds_till_start} seconds")
                except Exception as e:
                    LOG.error(f"Failed to schedule threaded dialogue: {e}")
        except Exception as e:
            LOG.error(f"schedule_skip_gui failed: {e}")

    def on_gui_scheduled(self, item: MediaSegmentItem):
        try:
            # --- Settings-Auswertung auch hier ---
            enabled, skip_intro, skip_outro = get_settings()
            if not enabled:
                LOG.info("on_gui_scheduled: Plugin deaktiviert – kein Dialog.")
                return

            if item:
                seg_type = item.get_segment_type_display().lower()
                if seg_type == "intro" and not skip_intro:
                    LOG.info("on_gui_scheduled: Intro-Skip deaktiviert – kein Dialog.")
                    return
                if seg_type == "outro" and not skip_outro:
                    LOG.info("on_gui_scheduled: Outro-Skip deaktiviert – kein Dialog.")
                    return

            player = xbmc.Player()
            if not player.isPlayingVideo():  # Prüfen, ob Video noch läuft
                LOG.info("on_gui_scheduled: Video nicht mehr aktiv")
                return

            current_seconds = player.getTime()
            LOG.info(
                f"Opening scheduled dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()} as within segment")
            if item.get_start_seconds() - POSITION_TOLERANCE <= current_seconds <= item.get_end_seconds() + POSITION_TOLERANCE:
                self.open_gui(item)
                return
            LOG.info(
                f"Skipping dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()} as not within segment ({current_seconds})")
        except Exception as e:
            LOG.error(f"on_gui_scheduled failed: {e}")

    def cancel_scheduled(self):
        try:
            if self.scheduled_thread:
                self.scheduled_thread.cancel()
                self.scheduled_thread = None
            LOG.info("Cancelled existing scheduled dialogue")
        except Exception as e:
            LOG.error(f"cancel_scheduled failed: {e}")

    def close_gui(self):
        try:
            if self.dialogue:
                now = time.time()
                if now - self.dialogue_opened_at < MIN_DIALOGUE_VISIBLE:
                    time_to_wait = MIN_DIALOGUE_VISIBLE - (now - self.dialogue_opened_at)
                    LOG.info(f"Delaying close of dialogue by {time_to_wait:.2f}s to ensure min visible time")
                    # Statt sleep, einen verzögerten Thread verwenden
                    utils.run_threaded(
                        self._delayed_close,
                        delay=time_to_wait,
                        kwargs={}
                    )
                    return  # Früh zurückkehren, _delayed_close wird es erledigen
                self.dialogue.close()
                self.dialogue = None
                self.dialogue_opened_at = 0
                self.last_item = None
        except Exception as e:
            LOG.error(f"close_gui failed: {e}")

    def _delayed_close(self):
        """Hilfsmethode zum verzögerten Schließen des Dialogs"""
        try:
            if self.dialogue:
                self.dialogue.close()
                self.dialogue = None
                self.dialogue_opened_at = 0
                self.last_item = None
        except Exception as e:
            LOG.error(f"_delayed_close failed: {e}")

    def is_last_item(self, item: MediaSegmentItem):
        try:
            if not self.last_item or not item:
                return False
            return self.last_item == item
        except Exception as e:
            LOG.error(f"is_last_item failed: {e}")
            return False

    def is_last_item_segment(self):
        try:
            player = xbmc.Player()
            if not player.isPlayingVideo() or not self.last_item:
                return False
            current_seconds = player.getTime()
            return (
                    self.last_item.get_start_seconds() - POSITION_TOLERANCE <= current_seconds <= self.last_item.get_end_seconds() + POSITION_TOLERANCE
            )
        except Exception as e:
            LOG.error(f"is_last_item_segment failed: {e}")
            return False

    def open_gui(self, item: MediaSegmentItem):
        try:
            # Aktuelle Zeit prüfen, um schnelle Wiederaufrufe zu vermeiden
            now = time.time()
            if now - self.dialogue_opened_at < 1.0 and self.dialogue:  # Mindestens 1 Sekunde zwischen Dialogöffnungen
                LOG.info(f"Skipping dialogue open - too soon after last open")
                return

            # Dialog soll immer erneut getriggert werden, wenn man wieder im Segment ist
            if self.is_last_item(item) and self.dialogue:
                LOG.info(
                    f"Skipping dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()} as it is the same as the last item and already open")
                return

            self.last_item = item
            LOG.info(f"Opening dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()}")
            self.close_gui()
            dialog = SkipSegmentDialogue('script-dialog.xml', addonPath, seek_time_seconds=item.get_end_seconds(),
                                         segment_type=item.get_segment_type_display())
            self.dialogue = dialog
            self.dialogue_opened_at = time.time()
            try:
                dialog.doModal()
            except Exception as e:
                LOG.error(f"doModal failed: {e}")
            del dialog
        except Exception as e:
            LOG.error(f"open_gui failed: {e}")


dialogue_handler = DialogueHandler()
