# -*- coding: utf-8 -*-

import json
import re
import xbmc
import xbmcgui


HOME = xbmcgui.Window(10000)
PROP_PREFIX = "EmbuaryHDRFallback"


def _set_prop(name, value):
    HOME.setProperty(name, "" if value is None else str(value))


def _get_prop(name):
    return HOME.getProperty(name).strip()


def _clear_result():
    for key in (
        "HdrType",
        "Source",
        "MatchedTitle",
        "MatchedYear",
        "MatchedMovieID",
        "VideoCodec",
        "VideoResolution",
        "Debug",
    ):
        _set_prop(f"{PROP_PREFIX}.{key}", "")


def _jsonrpc(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {},
    }
    try:
        raw = xbmc.executeJSONRPC(json.dumps(payload))
        return json.loads(raw or "{}")
    except Exception as exc:
        _set_prop(f"{PROP_PREFIX}.Debug", f"JSONRPC error: {exc}")
        return {}


def _norm(value):
    value = value or ""
    value = value.lower()
    value = value.replace("&", "and")
    value = re.sub(r"[\[\]\(\)\{\}:;,.!?'\"´`]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _strip_trailing_roman(title):
    # Beispiel: "Black Panther I" -> "Black Panther"
    return re.sub(r"\s+(i|ii|iii|iv|v|vi|vii|viii|ix|x)$", "", title or "", flags=re.I).strip()


def _candidate_titles(title, label):
    candidates = []

    for value in (title, label):
        value = (value or "").strip()
        if not value:
            continue

        candidates.append(value)

        stripped = _strip_trailing_roman(value)
        if stripped and stripped != value:
            candidates.append(stripped)

        if " - " in value and not re.search(r"episode\s+[ivxlcdm]+", value, re.I):
            candidates.append(value.split(" - ", 1)[0].strip())

    result = []
    seen = set()
    for item in candidates:
        key = _norm(item)
        if key and key not in seen:
            seen.add(key)
            result.append(item)

    return result


def _extract_hdr_from_streamdetails(movie):
    streamdetails = movie.get("streamdetails") or {}
    videos = streamdetails.get("video") or []

    if not isinstance(videos, list):
        return "", "", ""

    for video in videos:
        if not isinstance(video, dict):
            continue

        hdr = (
            video.get("hdrtype")
            or video.get("hdrType")
            or video.get("hdr_type")
            or ""
        )

        codec = video.get("codec") or ""
        width = video.get("width") or ""
        height = video.get("height") or ""

        hdr = str(hdr).strip().lower()
        codec = str(codec).strip().lower()

        if hdr in ("dolbyvision", "dolby vision", "dovi", "dv"):
            hdr = "dolbyvision"
        elif hdr in ("hdr10plus", "hdr10+", "hdr10_plus", "hdr10 plus"):
            hdr = "hdr10plus"
        elif hdr == "hdr10":
            hdr = "hdr10"
        elif hdr == "hdr":
            hdr = "hdr"
        elif hdr == "hlg":
            hdr = "hlg"
        elif hdr == "sdr":
            hdr = "sdr"

        resolution = ""
        try:
            w = int(width)
            h = int(height)
            if w >= 3800 or h >= 2000:
                resolution = "4K"
            elif h >= 1000:
                resolution = "1080"
            elif h >= 700:
                resolution = "720"
        except Exception:
            resolution = ""

        if hdr:
            return hdr, codec, resolution

    return "", "", ""


def _get_movies_by_title_contains(query):
    params = {
        "properties": [
            "title",
            "originaltitle",
            "sorttitle",
            "year",
            "streamdetails",
        ],
        "limits": {
            "start": 0,
            "end": 50,
        },
        "filter": {
            "field": "title",
            "operator": "contains",
            "value": query,
        },
    }

    data = _jsonrpc("VideoLibrary.GetMovies", params)
    result = data.get("result") or {}
    return result.get("movies") or []


def _score_movie(movie, wanted_titles, wanted_year):
    title = movie.get("title") or ""
    original = movie.get("originaltitle") or ""
    sorttitle = movie.get("sorttitle") or ""
    movie_year = str(movie.get("year") or "")

    movie_names = [_norm(title), _norm(original), _norm(sorttitle)]
    wanted_norms = [_norm(t) for t in wanted_titles if t]

    score = 0

    for wanted in wanted_norms:
        if not wanted:
            continue

        for name in movie_names:
            if not name:
                continue

            if name == wanted:
                score = max(score, 100)
            elif wanted in name or name in wanted:
                score = max(score, 80)

    if wanted_year and movie_year and str(wanted_year) == movie_year:
        score += 20

    hdr, _, _ = _extract_hdr_from_streamdetails(movie)
    if hdr:
        score += 10

    return score


def _lookup():
    _clear_result()

    title = _get_prop("ListItemTitle")
    label = _get_prop("ListItemLabel")
    year = _get_prop("ListItemYear")
    dbtype = _get_prop("ListItemDBType")
    direct_hdr = _get_prop("ListItemHdrType")

    _set_prop(
        f"{PROP_PREFIX}.Debug",
        f"start title={title} label={label} year={year} dbtype={dbtype} hdr={direct_hdr}",
    )

    if direct_hdr:
        _set_prop(f"{PROP_PREFIX}.HdrType", direct_hdr.lower())
        _set_prop(f"{PROP_PREFIX}.Source", "direct-listitem")
        _set_prop(f"{PROP_PREFIX}.Debug", "direct ListItem.HdrType exists")
        return

    if dbtype and dbtype.lower() != "movie":
        _set_prop(f"{PROP_PREFIX}.Debug", f"skip dbtype={dbtype}")
        return

    candidates = _candidate_titles(title, label)
    if not candidates:
        _set_prop(f"{PROP_PREFIX}.Debug", "no title candidates")
        return

    all_movies = []
    seen_ids = set()

    for candidate in candidates:
        query = _strip_trailing_roman(candidate) or candidate

        words = query.split()
        if len(words) > 3:
            query = " ".join(words[:3])

        for movie in _get_movies_by_title_contains(query):
            movieid = movie.get("movieid")
            if movieid in seen_ids:
                continue
            seen_ids.add(movieid)
            all_movies.append(movie)

    if not all_movies:
        _set_prop(f"{PROP_PREFIX}.Debug", "no movies returned from VideoLibrary.GetMovies")
        return

    best = None
    best_score = -1

    for movie in all_movies:
        score = _score_movie(movie, candidates, year)
        if score > best_score:
            best = movie
            best_score = score

    if not best:
        _set_prop(f"{PROP_PREFIX}.Debug", "no best match")
        return

    hdr, codec, resolution = _extract_hdr_from_streamdetails(best)

    _set_prop(f"{PROP_PREFIX}.MatchedTitle", best.get("title") or "")
    _set_prop(f"{PROP_PREFIX}.MatchedYear", best.get("year") or "")
    _set_prop(f"{PROP_PREFIX}.MatchedMovieID", best.get("movieid") or "")
    _set_prop(f"{PROP_PREFIX}.VideoCodec", codec)
    _set_prop(f"{PROP_PREFIX}.VideoResolution", resolution)

    if hdr:
        _set_prop(f"{PROP_PREFIX}.HdrType", hdr)
        _set_prop(f"{PROP_PREFIX}.Source", "movie-db-jsonrpc")
        _set_prop(f"{PROP_PREFIX}.Debug", f"matched score={best_score} hdr={hdr} title={best.get('title')}")
    else:
        _set_prop(f"{PROP_PREFIX}.Debug", f"matched but no hdrtype score={best_score} title={best.get('title')}")


if __name__ == "__main__":
    _lookup()