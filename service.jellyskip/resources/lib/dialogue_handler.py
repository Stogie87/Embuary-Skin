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
MIN_DIALOGUE_VISIBLE = 2  # Mindestanzeigezeit in Sekunden fuer Dialog
POSITION_TOLERANCE = 1.5  # Toleranzzeitfenster fuer Segmenterkennung
SEGMENT_SETTING_IDS = {
    "intro": "skip_intro",
    "outro": "skip_outro",
    "recap": "skip_recap",
    "preview": "skip_preview",
    "commercial": "skip_commercial",
}
SUPPORTED_SEGMENT_TYPES = set(SEGMENT_SETTING_IDS)


def get_settings():
    addon = xbmcaddon.Addon()
    enabled = addon.getSettingBool("enabled")
    segment_settings = {
        segment_type: addon.getSettingBool(setting_id)
        for segment_type, setting_id in SEGMENT_SETTING_IDS.items()
    }
    return enabled, segment_settings


def get_enabled_segment_types():
    enabled, segment_settings = get_settings()
    if not enabled:
        return set()
    return {
        segment_type
        for segment_type, is_enabled in segment_settings.items()
        if is_enabled
    }


def is_segment_enabled(item: MediaSegmentItem):
    if not item:
        return False

    segment_type = item.get_segment_type_display().lower()
    if segment_type not in SUPPORTED_SEGMENT_TYPES:
        return False

    enabled, segment_settings = get_settings()
    return enabled and segment_settings.get(segment_type, False)


class DialogueHandler:

    def __init__(self):  # Python-Standard-Namenskonvention
        self.dialogue = None
        self.scheduled_thread = None
        self.last_item = None
        self.dialogue_opened_at = 0

    def schedule_skip_gui(self, item: MediaSegmentItem, current_seconds):
        try:
            enabled, segment_settings = get_settings()
            if not enabled:
                LOG.info("schedule_skip_gui: Plugin deaktiviert - kein Dialog.")
                self.close_gui()
                return

            if not item:
                LOG.warn("schedule_skip_gui: No item provided.")
                return

            seg_type = item.get_segment_type_display().lower()
            if seg_type not in SUPPORTED_SEGMENT_TYPES:
                LOG.info(f"schedule_skip_gui: Ignoring unsupported segment type {seg_type}")
                self.close_gui()
                return

            if not segment_settings.get(seg_type, False):
                LOG.info(f"schedule_skip_gui: {seg_type} skip disabled - no dialogue.")
                return

            self.cancel_scheduled()

            # Pruefe ob wir gerade ausserhalb des Segments sind und resette das Flag,
            # damit ein erneuter Eintritt den Dialog wieder anzeigt.
            if self.last_item and not self.is_last_item_segment() and self.dialogue:
                LOG.info(
                    f"Closing dialogue for {self.last_item.get_segment_type_display()} at "
                    f"{self.last_item.get_start_seconds()} as it is not currently playing"
                )
                self.close_gui()

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
                        f"Scheduled dialogue for {item.get_segment_type_display()} at "
                        f"{item.get_start_seconds()} in {seconds_till_start} seconds"
                    )
                except Exception as e:
                    LOG.error(f"Failed to schedule threaded dialogue: {e}")
        except Exception as e:
            LOG.error(f"schedule_skip_gui failed: {e}")

    def on_gui_scheduled(self, item: MediaSegmentItem):
        try:
            if not is_segment_enabled(item):
                segment_name = item.get_segment_type_display() if item else "unknown"
                LOG.info(f"on_gui_scheduled: {segment_name} skip disabled or unsupported - no dialogue.")
                return

            player = xbmc.Player()
            if not player.isPlayingVideo():
                LOG.info("on_gui_scheduled: Video nicht mehr aktiv")
                return

            current_seconds = player.getTime()
            LOG.info(
                f"Opening scheduled dialogue for {item.get_segment_type_display()} at "
                f"{item.get_start_seconds()} as within segment"
            )
            if item.get_start_seconds() - POSITION_TOLERANCE <= current_seconds <= item.get_end_seconds() + POSITION_TOLERANCE:
                self.open_gui(item)
                return
            LOG.info(
                f"Skipping dialogue for {item.get_segment_type_display()} at "
                f"{item.get_start_seconds()} as not within segment ({current_seconds})"
            )
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
                    utils.run_threaded(
                        self._delayed_close,
                        delay=time_to_wait,
                        kwargs={}
                    )
                    return
                self.dialogue.close()
                self.dialogue = None
                self.dialogue_opened_at = 0
                self.last_item = None
        except Exception as e:
            LOG.error(f"close_gui failed: {e}")

    def _delayed_close(self):
        """Hilfsmethode zum verzoegerten Schliessen des Dialogs"""
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
                self.last_item.get_start_seconds() - POSITION_TOLERANCE
                <= current_seconds
                <= self.last_item.get_end_seconds() + POSITION_TOLERANCE
            )
        except Exception as e:
            LOG.error(f"is_last_item_segment failed: {e}")
            return False

    def open_gui(self, item: MediaSegmentItem):
        try:
            if not is_segment_enabled(item):
                LOG.info("open_gui: Ignoring disabled or unsupported media segment")
                return

            now = time.time()
            if now - self.dialogue_opened_at < 1.0 and self.dialogue:
                LOG.info("Skipping dialogue open - too soon after last open")
                return

            if self.is_last_item(item) and self.dialogue:
                LOG.info(
                    f"Skipping dialogue for {item.get_segment_type_display()} at "
                    f"{item.get_start_seconds()} as it is the same as the last item and already open"
                )
                return

            self.last_item = item
            LOG.info(f"Opening dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()}")
            self.close_gui()
            dialog = SkipSegmentDialogue(
                'script-dialog.xml',
                addonPath,
                seek_time_seconds=item.get_end_seconds(),
                segment_type=item.get_segment_type_display()
            )
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
