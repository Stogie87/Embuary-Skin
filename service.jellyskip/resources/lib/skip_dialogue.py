import xbmcgui, xbmc

import helper.utils as utils
from helper import LazyLogger

OK_BUTTON = 2101

ACTION_PREVIOUS_MENU = 10
ACTION_BACK = 92
INSTRUCTION_LABEL = 203
AUTHCODE_LABEL = 204
WARNING_LABEL = 205
CENTER_Y = 6
CENTER_X = 2

MIN_REMAINING_SECONDS = 5
LOG = LazyLogger(__name__)

class SkipSegmentDialogue(xbmcgui.WindowXMLDialog):

    def __init__(self, xmlFile, resourcePath, seek_time_seconds, segment_type):
        self.seek_time_seconds = seek_time_seconds
        self.segment_type = segment_type
        self.player = xbmc.Player()

    def onInit(self):
        language = xbmc.getLanguage(xbmc.ISO_639_1)

        # Übersetzungen für "Skip" bzw. "Überspringe"
        skip_translations = {
            "de": "Überspringe",
            "fr": "Passer",
            "es": "Saltar",
            "it": "Salta",
            "nl": "Overslaan",
            "pt": "Pular",
            "pl": "Pomiń",
            "sv": "Hoppa över",
            "ru": "Пропустить",
            "tr": "Atla",
            "en": "Skip"  # fallback und Standard
        }

        # Optional: Segmentübersetzungen (Intro, Werbung etc.)
        segment_translations = {
            "intro": {
                "de": "Intro",
                "fr": "l’intro",
                "es": "la introducción",
                "it": "l’introduzione",
                "en": "Intro"
            },
            "ads": {
                "de": "Werbung",
                "fr": "la pub",
                "es": "los anuncios",
                "en": "Ads"
            }
        }

        prefix = skip_translations.get(language, "Skip")
        segment_key = self.segment_type.lower()

        # Segment übersetzen, wenn bekannt
        translated_segment = segment_translations.get(segment_key, {}).get(language, self.segment_type)

        skip_label = f"{prefix} {translated_segment}"
        skip_button = self.getControl(OK_BUTTON)
        skip_button.setLabel(skip_label)

        self.schedule_close_action()

    def get_seconds_till_segment_end(self):
        return self.seek_time_seconds - self.player.getTime()

    def schedule_close_action(self):
        seconds_till_segment_end = self.get_seconds_till_segment_end()

        if seconds_till_segment_end > 0:
            utils.run_threaded(self.on_automatic_close, delay=seconds_till_segment_end, kwargs={})

    def on_automatic_close(self):
        self.close()
        LOG.info("JellySkip: Auto closing dialogue")
        sender = "service.jellyskip"
        xbmc.executebuiltin("NotifyAll(%s, %s, %s)" % (sender, "Jellyskip.DialogueClosed", {}))

    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU or action == ACTION_BACK:
            self.close()

    def onControl(self, control):
        pass

    def onFocus(self, control):
        pass

    def onClick(self, control):
        if not self.player.isPlaying():
            self.close()
            return

        if control == OK_BUTTON:
            remaining_seconds = self.player.getTotalTime() - self.seek_time_seconds

            if remaining_seconds < MIN_REMAINING_SECONDS:
                self.player.seekTime(self.player.getTotalTime() - MIN_REMAINING_SECONDS)
                self.close()
            else:
                self.player.seekTime(self.seek_time_seconds)

        self.close()
