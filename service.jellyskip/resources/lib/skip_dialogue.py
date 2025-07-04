import xbmcgui
import xbmc
import helper.utils as utils
from helper import LazyLogger

OK_BUTTON = 2101
ACTION_PREVIOUS_MENU = 10
ACTION_BACK = 92
MIN_REMAINING_SECONDS = 5
LOG = LazyLogger(__name__)

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
                        self.close()
                    else:
                        self.player.seekTime(self.seek_time_seconds)
                except Exception as e:
                    LOG.error(f"Seek failed: {e}")
            self.close()
        except Exception as e:
            LOG.error(f"onClick failed: {e}")
