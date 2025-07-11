# -*- coding: utf-8 -*-
from __future__ import division, absolute_import, print_function, unicode_literals

#################################################################################################

import threading
import concurrent.futures
from datetime import date

import queue

import requests

from .helper import settings, stop, window, LazyLogger
from .jellyfin import Jellyfin
from .jellyfin import api
from .helper.exceptions import HTTPException

#################################################################################################

LOG = LazyLogger(__name__)

#################################################################################################

def get_jellyfinserver_url(handler):
    # {server} muss ersetzt werden! Hier Dummy für Kompatibilität – anpassen je nach tatsächlichem Anwendungsfall
    server_url = settings("server")
    if not server_url:
        LOG.error("Jellyfin server URL is not set!")
        return ""
    if handler.startswith("/"):
        handler = handler[1:]
        LOG.info("handler starts with /: %s", handler)
    return "{}/{}".format(server_url.rstrip("/"), handler)

def _http(action, url, request=None, server_id=None):
    if request is None:
        request = {}
    request.update({"url": url, "type": action})
    return Jellyfin(server_id).http.request(request)

def _get(handler, params=None, server_id=None):
    return _http("GET", get_jellyfinserver_url(handler), {"params": params}, server_id)

def _post(handler, json=None, params=None, server_id=None):
    return _http(
        "POST",
        get_jellyfinserver_url(handler),
        {"params": params, "json": json},
        server_id,
    )

def _delete(handler, params=None, server_id=None):
    return _http(
        "DELETE", get_jellyfinserver_url(handler), {"params": params}, server_id
    )

def validate_view(library_id, item_id):
    """This confirms a single item from the library matches the view it belongs to."""
    try:
        result = _get(
            "Users/{UserId}/Items",
            {"ParentId": library_id, "Recursive": True, "Ids": item_id},
        )
    except Exception as error:
        LOG.exception(error)
        return False
    return bool(result.get("Items"))

def get_single_item(parent_id, media):
    return _get(
        "Users/{UserId}/Items",
        {
            "ParentId": parent_id,
            "Recursive": True,
            "Limit": 1,
            "IncludeItemTypes": media,
        },
    )

def get_movies_by_boxset(boxset_id):
    for items in get_items(boxset_id, "Movie"):
        yield items

def get_episode_by_show(show_id):
    query = {
        "url": "Shows/%s/Episodes" % show_id,
        "params": {
            "EnableUserData": True,
            "EnableImages": True,
            "UserId": "{UserId}",
            "Fields": api.info(),
        },
    }
    for items in _get_items(query):
        yield items

def get_episode_by_season(show_id, season_id):
    query = {
        "url": "Shows/%s/Episodes" % show_id,
        "params": {
            "SeasonId": season_id,
            "EnableUserData": True,
            "EnableImages": True,
            "UserId": "{UserId}",
            "Fields": api.info(),
        },
    }
    for items in _get_items(query):
        yield items

def get_item_count(parent_id, item_type=None):
    url = "Users/{UserId}/Items"
    query_params = {
        "ParentId": parent_id,
        "IncludeItemTypes": item_type,
        "EnableTotalRecordCount": True,
        "LocationTypes": "FileSystem,Remote,Offline",
        "Recursive": True,
        "Limit": 1,
    }
    result = _get(url, query_params)
    return result.get("TotalRecordCount", 1)

def get_items(parent_id, item_type=None, basic=False, params=None):
    query = {
        "url": "Users/{UserId}/Items",
        "params": {
            "ParentId": parent_id,
            "IncludeItemTypes": item_type,
            "SortBy": "SortName",
            "SortOrder": "Ascending",
            "Fields": api.basic_info() if basic else api.info(),
            "CollapseBoxSetItems": False,
            "IsVirtualUnaired": False,
            "EnableTotalRecordCount": False,
            "LocationTypes": "FileSystem,Remote,Offline",
            "IsMissing": False,
            "Recursive": True,
        },
    }
    if params:
        query["params"].update(params)
    for items in _get_items(query):
        yield items

def get_artists(parent_id=None):
    query = {
        "url": "Artists",
        "params": {
            "UserId": "{UserId}",
            "ParentId": parent_id,
            "SortBy": "SortName",
            "SortOrder": "Ascending",
            "Fields": api.music_info(),
            "CollapseBoxSetItems": False,
            "IsVirtualUnaired": False,
            "EnableTotalRecordCount": False,
            "LocationTypes": "FileSystem,Remote,Offline",
            "IsMissing": False,
            "Recursive": True,
        },
    }
    for items in _get_items(query):
        yield items

@stop
def _get_items(query, server_id=None):
    """query = {'url': string, 'params': dict -- opt, include StartIndex to resume}"""
    items = {"Items": [], "TotalRecordCount": 0, "RestorePoint": {}}
    limit = min(int(settings("limitIndex") or 50), 50)
    dthreads = int(settings("limitThreads") or 3)
    url = query["url"]
    query.setdefault("params", {})
    params = query["params"]

    try:
        test_params = dict(params)
        test_params["Limit"] = 1
        test_params["EnableTotalRecordCount"] = True
        items["TotalRecordCount"] = _get(url, test_params, server_id=server_id).get("TotalRecordCount", 0)
    except Exception as error:
        LOG.exception(
            "Failed to retrieve the server response %s: %s params:%s",
            url,
            error,
            params,
        )
        return  # Fehler -> yield gar nichts

    params.setdefault("StartIndex", 0)

    def get_query_params(params, start, count):
        params_copy = dict(params)
        params_copy["StartIndex"] = start
        params_copy["Limit"] = count
        return params_copy

    query_params = [
        get_query_params(params, offset, limit)
        for offset in range(params["StartIndex"], items["TotalRecordCount"], limit)
    ]

    with concurrent.futures.ThreadPoolExecutor(dthreads) as p:
        jobs = {}
        thread_buffer = threading.Semaphore(dthreads)

        def get_wrapper(params):
            thread_buffer.acquire()
            try:
                return _get(url, params, server_id=server_id)
            finally:
                thread_buffer.release()

        for param in query_params:
            job = p.submit(get_wrapper, param)
            jobs[job] = param

        for job in concurrent.futures.as_completed(jobs):
            result = job.result() or {"Items": []}
            query["params"] = jobs[job]
            del jobs[job]
            # IndexError vermeiden
            if result.get("Items") and isinstance(result["Items"], list) and result["Items"]:
                first_item = result["Items"][0]
                if first_item.get("ProductionYear"):
                    try:
                        date(first_item["ProductionYear"], 1, 1)
                    except ValueError:
                        LOG.info("#216 mitigation triggered. Setting ProductionYear to None")
                        first_item["ProductionYear"] = None
            items["Items"].extend(result.get("Items", []))
            items["RestorePoint"] = query
            yield items
            del items["Items"][:]

class GetItemWorker(threading.Thread):
    def __init__(self, server, queue, output):
        super(GetItemWorker, self).__init__()
        self.server = server
        self.queue = queue
        self.output = output
        self.is_done = False

    def run(self):
        with requests.Session() as s:
            while True:
                try:
                    item_ids = self.queue.get(timeout=1)
                except queue.Empty:
                    self.is_done = True
                    LOG.info("--<[ q:download/%s ]", id(self))
                    return
                request = {
                    "type": "GET",
                    "handler": "Users/{UserId}/Items",
                    "params": {
                        "Ids": ",".join(str(x) for x in item_ids),
                        "Fields": api.info(),
                    },
                }
                try:
                    result = self.server.http.request(request, s)
                    for item in result.get("Items", []):
                        if item["Type"] in self.output:
                            self.output[item["Type"]].put(item)
                except HTTPException as error:
                    LOG.error("--[ http status: %s ]", error.status)
                    if error.status == "ServerUnreachable":
                        self.is_done = True
                        break
                except Exception as error:
                    LOG.exception(error)
                self.queue.task_done()
                if window("jellyfin_should_stop.bool"):
                    break
