import sys

import xbmc, xbmcaddon

from helper import LazyLogger
from helper import window

# # Replace 'plugin.video.example' with the ID of the other plugin
# other_plugin_id = 'plugin.video.jellyfin'
# other_plugin = xbmcaddon.Addon(id=other_plugin_id)
# other_plugin_path = other_plugin.getAddonInfo('path')
#
# # Add the other plugin's path to the Python path
# sys.path.append(xbmc.translatePath(other_plugin_path))
#
# # Now you can import modules from the other plugin

LOG = LazyLogger(__name__)


class JellySkipPlayer(xbmc.Player):


    def __init__(self, monitor):
        xbmc.Player.__init__(self)
        self.jellyskip_monitor = monitor

    def onPlayBackStarted(self):
        LOG.info("Playback started")
        # self.monitor.start_tracking()




    def get_playing_file(self):
        try:
            return self.getPlayingFile()
        except Exception as error:
            LOG.exception(error)