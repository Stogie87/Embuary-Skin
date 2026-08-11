# -*- coding: utf-8 -*-
# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)
import json
import urllib.request
import xbmcvfs

from helper import LazyLogger, window

LOG = LazyLogger(__name__)

from .media_segments import MediaSegmentResponse


class JellyfinHack:
    def __init__(self):
        self.jellyfin_itemid = None
        self._jellyfin_server = None
        self._jellyfin_apikey = None
        self.media_segments = None

    def _get_playing_itemid(self):
        """Return the Jellyfin item id of the item actually playing in Kodi."""
        try:
            item_id = window("jellyfin_playing_id")
            return str(item_id) if item_id else None
        except Exception as e:
            LOG.debug(f"Unable to read jellyfin_playing_id: {e}")
            return None

    def sync_itemid_from_player(self):
        """
        Prefer Jellyfin for Kodi's current-playback window property over websocket
        UserDataChanged events. UserDataChanged can contain unrelated library items.
        """
        playing_itemid = self._get_playing_itemid()
        if playing_itemid and playing_itemid != self.jellyfin_itemid:
            LOG.info(f"Using current Jellyfin playback item id: {playing_itemid}")
            self.jellyfin_itemid = playing_itemid
            self.media_segments = None
        return self.jellyfin_itemid

    def event_handler_jellyfin_userdatachanged(self, _, **kwargs):
        if kwargs.get("sender") != "plugin.video.jellyfin":
            return

        # Jellyfin for Kodi exposes the actual playing item id. Never let a
        # generic UserDataChanged event replace it with an unrelated item.
        playing_itemid = self._get_playing_itemid()
        if playing_itemid:
            if playing_itemid != self.jellyfin_itemid:
                self.jellyfin_itemid = playing_itemid
                self.media_segments = None
            return

        self.reset_itemid()

        try:
            payload = json.loads(kwargs["data"])[0]
            user_data = payload.get("UserDataList") or []
            if user_data:
                item_id = user_data[0].get("ItemId")
                self.jellyfin_itemid = str(item_id) if item_id else None
        except Exception as e:
            LOG.debug(f"Unable to resolve item id from UserDataChanged: {e}")
            self.jellyfin_itemid = None

    def setup_jellyfin_server(self):
        if not self._jellyfin_server:
            with open(xbmcvfs.translatePath("special://profile/addon_data/plugin.video.jellyfin/data.json"),
                      "rb") as f:
                jf_servers = json.load(f)
            self._jellyfin_apikey = jf_servers["Servers"][0]["AccessToken"]
            self._jellyfin_server = jf_servers["Servers"][0]["address"]

    def make_request(self, api_endpoint):
        url = f"{self._jellyfin_server}/{api_endpoint}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "Authorization": f"MediaBrowser Token={self._jellyfin_apikey}",
        })

        with urllib.request.urlopen(req, timeout=5) as response:
            return json.load(response)

    def has_itemid(self):
        self.sync_itemid_from_player()
        return self.jellyfin_itemid is not None

    def reset_itemid(self):
        self.jellyfin_itemid = None
        self.media_segments = None

    def get_media_segments(self):
        self.sync_itemid_from_player()
        if self.media_segments is None:
            self._fetch_media_segments()
        return self.media_segments

    def _fetch_media_segments(self):
        try:
            item_id = self.sync_itemid_from_player()
            if not item_id:
                LOG.info("No current Jellyfin playback item id")
                self.media_segments = None
                return None

            self.setup_jellyfin_server()
            api_endpoint = f"MediaSegments/{item_id}"
            ret = self.make_request(api_endpoint)

            media_segments_response = MediaSegmentResponse.from_json(
                ret,
                expected_item_id=item_id
            )

            if not media_segments_response.items:
                self.media_segments = None
                LOG.info(f"No supported media segments for current item {item_id}")
                return ret

            self.media_segments = media_segments_response
            LOG.info(f"MediaSegments: {media_segments_response}")
            return ret
        except Exception as e:
            self.media_segments = None
            LOG.warning(f"Fetching MediaSegments failed: {e}")
            return None

    def get_credits_time(self):
        ret = 0
        try:
            if self.jellyfin_itemid:
                self.setup_jellyfin_server()
                api_endpoint = f"Episode/{self.jellyfin_itemid}/IntroTimestamps/v1?mode=Credits"

                ret = self.make_request(api_endpoint)["IntroStart"]
        except Exception:
            pass
        finally:
            self.jellyfin_itemid = None
            return ret
