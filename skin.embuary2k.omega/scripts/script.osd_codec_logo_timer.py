import xbmc
import xbmcgui

# Deine Optionen
options = [
    '1 Sekunde',
    '2 Sekunden',
    '3 Sekunden',
    '4 Sekunden',
    '5 Sekunden (Standard)',
    '6 Sekunden',
    '7 Sekunden',
    '8 Sekunden',
    '9 Sekunden',
    '10 Sekunden',
    '11 Sekunden',
    '12 Sekunden',
    '13 Sekunden',
    '14 Sekunden',
    '15 Sekunden'
]

# Settings-Keys passend zum Skin
settings = [
    'osd.useOneSecondCodecLogos',
    'osd.useTwoSecondsCodecLogos',
    'osd.useThreeSecondsCodecLogos',
    'osd.useFourSecondsCodecLogos',
    'osd.useFiveSecondsCodecLogos',
    'osd.useSixSecondsCodecLogos',
    'osd.useSevenSecondsCodecLogos',
    'osd.useEightSecondsCodecLogos',
    'osd.useNineSecondsCodecLogos',
    'osd.useTenSecondsCodecLogos',
    'osd.useElevenSecondsCodecLogos',
    'osd.useTwelveSecondsCodecLogos',
    'osd.useThirteenSecondsCodecLogos',
    'osd.useFourteenSecondsCodecLogos',
    'osd.useFifteenSecondsCodecLogos'
]

dialog = xbmcgui.Dialog()
idx = dialog.select("Codec-Logos Anzeigedauer wählen", options)
if idx >= 0:
    # Zuerst alle zurücksetzen
    for s in settings:
        xbmc.executebuiltin(f"Skin.Reset({s})")
    # Dann das gewählte setzen
    xbmc.executebuiltin(f"Skin.SetBool({settings[idx]})")
