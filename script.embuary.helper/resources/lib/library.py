#!/usr/bin/python

import xbmc
import xbmcgui

from resources.lib.json_map import *
from resources.lib.helper import *

def add_items(li, json_query, type, searchstring=None):
    for item in json_query:
        if type == 'movie':
            handle_movies(li, item, searchstring)
        elif type == 'tvshow':
            handle_tvshows(li, item, searchstring)
        elif type == 'season':
            handle_seasons(li, item)
        elif type == 'episode':
            handle_episodes(li, item)
        elif type == 'genre':
            handle_genre(li, item)
        elif type == 'cast':
            handle_cast(li, item)

def handle_movies(li, item, searchstring=None):
    genre = item.get('genre', [])
    if not isinstance(genre, list):
        genre = [genre]
    studio = item.get('studio', [])
    if not isinstance(studio, list):
        studio = [studio]
    country = item.get('country', [])
    if not isinstance(country, list):
        country = [country]
    director = item.get('director', [])
    if not isinstance(director, list):
        director = [director]
    writer = item.get('writer', [])
    if not isinstance(writer, list):
        writer = [writer]

    li_item = xbmcgui.ListItem(label=item.get('title', ''), offscreen=True)
    info_tag = li_item.getVideoInfoTag()
    info_tag.setTitle(item.get('title', ''))
    info_tag.setOriginalTitle(item.get('originaltitle', ''))
    info_tag.setSortTitle(item.get('sorttitle', ''))
    info_tag.setYear(int(item.get('year', 0)))
    info_tag.setGenres(genre)
    info_tag.setStudios(studio)
    info_tag.setCountries(country)
    info_tag.setDirectors(director)
    info_tag.setWriters(writer)
    info_tag.setPlot(item.get('plot', ''))
    info_tag.setPlotOutline(item.get('plotoutline', ''))
    info_tag.setIMDBNumber(item.get('imdbnumber', ''))

    taglist = item.get('tag', [])
    if not isinstance(taglist, list):
        taglist = [taglist]
    info_tag.setTags(taglist)

    try:
        rating = float(item.get('rating', 0))
        votes = int(item.get('votes', 0))
        if rating > 10:
            rating /= 10
        info_tag.setRating(rating, votes)
    except Exception:
        pass

    try:
        userrating = int(float(item.get('userrating', 0)))
        info_tag.setUserRating(userrating)
    except Exception:
        pass

    info_tag.setLastPlayed(item.get('lastplayed', ''))
    info_tag.setMediaType('movie')
    info_tag.setTrailer(item.get('trailer', ''))
    info_tag.setDateAdded(item.get('dateadded', ''))
    info_tag.setPremiered(item.get('premiered', ''))
    info_tag.setPath(item.get('file', ''))
    info_tag.setPlaycount(item.get('playcount', 0))
    info_tag.setSet(item.get('set', ''))
    info_tag.setSetId(item.get('setid', ''))
    info_tag.setTop250(item.get('top250', 0))

    resume = item.get('resume', {})
    if 'position' in resume and 'total' in resume:
        info_tag.setResumePoint(resume.get('position', 0), resume.get('total', 0))

    li_item.setProperty('tagline', item.get('tagline', ''))
    li_item.setProperty('mpaa', item.get('mpaa', ''))

    # Cast als einfache Property (Kodi hat keine xbmc.Actor mehr)
    if 'cast' in item and isinstance(item['cast'], list):
        cast_names = [c.get('name', '').strip() for c in item['cast'] if c.get('name')]
        if cast_names:
            li_item.setProperty('cast', ', '.join(cast_names))
            # Zusätzlich andere Cast-Properties, falls gewünscht
            first_cast = cast_names[0]
            li_item.setProperty('cast.0', first_cast)

    # Ratings und andere Properties über Helper, wenn noch benötigt
    _set_ratings(li_item, item.get('ratings', {}))
    _set_unique_properties(li_item, genre, 'genre')
    _set_unique_properties(li_item, studio, 'studio')
    _set_unique_properties(li_item, country, 'country')
    _set_unique_properties(li_item, director, 'director')
    _set_unique_properties(li_item, writer, 'writer')

    art = item.get('art', {})
    if not art.get('icon'):
        art['icon'] = 'DefaultVideo.png'
    li_item.setArt(art)

    has_video = False
    streamdetails = item.get('streamdetails', {})
    if streamdetails:
        for key, streams in streamdetails.items():
            for stream in streams:
                if key == "video":
                    has_video = True
                    video_detail = xbmc.VideoStreamDetail()
                    video_detail.setLanguage(stream.get('language', ''))
                    video_detail.setCodec(stream.get('codec', ''))
                    video_detail.setWidth(stream.get('width', 0))
                    video_detail.setHeight(stream.get('height', 0))
                    video_detail.setDuration(stream.get('duration', 0))
                    video_detail.setStereoMode(stream.get('stereo_mode', ''))
                    video_detail.setAspect(stream.get('aspect', 0))
                    info_tag.addVideoStream(video_detail)
                elif key == "audio":
                    audio_detail = xbmc.AudioStreamDetail()
                    audio_detail.setLanguage(stream.get('language', ''))
                    audio_detail.setCodec(stream.get('codec', ''))
                    audio_detail.setChannels(stream.get('channels', 2))
                    info_tag.addAudioStream(audio_detail)
                elif key == "subtitle":
                    subtitle_detail = xbmc.SubtitleStreamDetail()
                    subtitle_detail.setLanguage(stream.get('language', ''))
                    info_tag.addSubtitleStream(subtitle_detail)
    if not has_video:
        video_detail = xbmc.VideoStreamDetail()
        video_detail.setDuration(item.get('runtime', 0))
        info_tag.addVideoStream(video_detail)

    if searchstring:
        li_item.setProperty('searchstring', searchstring)

    li.append((item.get('file', ''), li_item, False))


def handle_tvshows(li, item, searchstring=None):
    genre = item.get('genre', [])
    if not isinstance(genre, list):
        genre = [genre]
    studio = item.get('studio', [])
    if not isinstance(studio, list):
        studio = [studio]

    dbid = item.get('tvshowid', '')
    season = item.get('season', 0)
    episode = item.get('episode', 0)
    watchedepisodes = item.get('watchedepisodes', 0)
    unwatchedepisodes = get_unwatched(episode, watchedepisodes)

    if not condition('Window.IsVisible(movieinformation)'):
        folder = True
        filepath = f'videodb://tvshows/titles/{dbid}/'
    else:
        folder = False
        filepath = f'plugin://script.embuary.helper/?action=folderjump&type=tvshow&dbid={dbid}'

    li_item = xbmcgui.ListItem(label=item.get('title', ''), offscreen=True)
    info_tag = li_item.getVideoInfoTag()
    info_tag.setTitle(item.get('title', ''))
    info_tag.setYear(int(item.get('year', 0)))
    info_tag.setSortTitle(item.get('sorttitle', ''))
    info_tag.setOriginalTitle(item.get('originaltitle', ''))
    info_tag.setGenres(genre)
    info_tag.setStudios(studio)
    info_tag.setPlot(item.get('plot', ''))
    try:
        rating = float(item.get('rating', 0))
        votes = int(item.get('votes', 0))
        if rating > 10:
            rating /= 10
        info_tag.setRating(rating, votes)
    except Exception:
        pass
    try:
        userrating = int(float(item.get('userrating', 0)))
        info_tag.setUserRating(userrating)
    except Exception:
        pass
    info_tag.setPremiered(item.get('premiered', ''))
    taglist = item.get('tag', [])
    if not isinstance(taglist, list):
        taglist = [taglist]
    info_tag.setTags(taglist)
    info_tag.setMediaType('tvshow')
    info_tag.setIMDBNumber(item.get('imdbnumber', ''))
    info_tag.setLastPlayed(item.get('lastplayed', ''))
    info_tag.setPath(filepath)
    info_tag.setDuration(item.get('runtime', 0))
    info_tag.setDateAdded(item.get('dateadded', ''))
    info_tag.setPlaycount(item.get('playcount', 0))
    info_tag.setSeason(season)
    info_tag.setEpisode(episode)

    li_item.setProperty('mpaa', item.get('mpaa', ''))

    if 'cast' in item and isinstance(item['cast'], list):
        cast_names = [c.get('name', '').strip() for c in item['cast'] if c.get('name')]
        if cast_names:
            li_item.setProperty('cast', ', '.join(cast_names))
            li_item.setProperty('cast.0', cast_names[0])

    _set_ratings(li_item, item.get('ratings', {}))
    _set_unique_properties(li_item, genre, 'genre')
    _set_unique_properties(li_item, studio, 'studio')

    li_item.setProperty('totalseasons', str(season))
    li_item.setProperty('totalepisodes', str(episode))
    li_item.setProperty('watchedepisodes', str(watchedepisodes))
    li_item.setProperty('unwatchedepisodes', str(unwatchedepisodes))
    li_item.setProperty('showtitle', item.get('title', ''))

    art = item.get('art', {})
    if not art.get('icon'):
        art['icon'] = 'DefaultVideo.png'
    li_item.setArt(art)

    if searchstring:
        li_item.setProperty('searchstring', searchstring)

    li.append((filepath, li_item, folder))


def handle_seasons(li, item):
    tvshowdbid = item.get('tvshowid', '')
    season = item.get('season', 0)
    episode = item.get('episode', 0)
    watchedepisodes = item.get('watchedepisodes', 0)
    unwatchedepisodes = get_unwatched(episode, watchedepisodes)

    if season == 0:
        title = xbmc.getLocalizedString(20381)  # Specials
        special = 'true'
    else:
        title = f"{xbmc.getLocalizedString(20373)} {season}"  # Season
        special = 'false'

    if not condition('Window.IsVisible(movieinformation)'):
        folder = True
        filepath = f'videodb://tvshows/titles/{tvshowdbid}/{season}/'
    else:
        folder = False
        filepath = f'plugin://script.embuary.helper/?action=folderjump&type=season&dbid={tvshowdbid}&season={season}'

    li_item = xbmcgui.ListItem(label=title, offscreen=True)
    info_tag = li_item.getVideoInfoTag()
    info_tag.setTitle(title)
    info_tag.setSeason(season)
    info_tag.setEpisode(episode)
    info_tag.setPlaycount(item.get('playcount', 0))
    info_tag.setMediaType('season')
    info_tag.setDbId(item.get('seasonid', ''))

    li_item.setProperty('showtitle', item.get('showtitle', ''))

    art = item.get('art', {})
    if not art.get('icon'):
        art['icon'] = 'DefaultVideo.png'
    if 'tvshow.fanart' not in art:
        art['fanart'] = ''
    li_item.setArt(art)

    li_item.setProperty('watchedepisodes', str(watchedepisodes))
    li_item.setProperty('unwatchedepisodes', str(unwatchedepisodes))
    li_item.setProperty('isspecial', special)
    li_item.setProperty('season_label', item.get('label', ''))
    li_item.setProperty('mpaa', item.get('mpaa', ''))

    li.append((filepath, li_item, folder))


def handle_episodes(li, item):
    director = item.get('director', [])
    if not isinstance(director, list):
        director = [director]
    writer = item.get('writer', [])
    if not isinstance(writer, list):
        writer = [writer]

    episode_num = int(item.get('episode', 0))
    season_num = item.get('season', '0')

    if episode_num < 10:
        label = f"0{episode_num}. {item.get('title', '')}"
    else:
        label = f"{episode_num}. {item.get('title', '')}"

    if season_num == '0':
        label = 'S' + label
    else:
        label = f"{season_num}x{label}"

    li_item = xbmcgui.ListItem(label=label, offscreen=True)
    info_tag = li_item.getVideoInfoTag()

    info_tag.setTitle(item.get('title', ''))
    info_tag.setEpisode(episode_num)
    info_tag.setSeason(season_num)
    info_tag.setPremiered(item.get('firstaired', ''))
    info_tag.setDbId(item.get('episodeid', ''))
    info_tag.setPlot(item.get('plot', ''))
    info_tag.setOriginalTitle(item.get('originaltitle', ''))
    info_tag.setLastPlayed(item.get('lastplayed', ''))

    try:
        rating = float(item.get('rating', 0))
        votes = int(item.get('votes', 0))
        if rating > 10:
            rating /= 10
        info_tag.setRating(rating, votes)
    except Exception:
        pass
    try:
        userrating = int(float(item.get('userrating', 0)))
        info_tag.setUserRating(userrating)
    except Exception:
        pass

    info_tag.setPlaycount(item.get('playcount', 0))
    info_tag.setDirectors(director)
    info_tag.setWriters(writer)
    info_tag.setPath(item.get('file', ''))
    info_tag.setDateAdded(item.get('dateadded', ''))
    info_tag.setMediaType('episode')

    resume = item.get('resume', {})
    if 'position' in resume and 'total' in resume:
        info_tag.setResumePoint(resume.get('position', 0), resume.get('total', 0))

    li_item.setProperty('showtitle', item.get('showtitle', ''))
    li_item.setProperty('mpaa', item.get('mpaa', ''))
    li_item.setProperty('season_label', item.get('season_label', ''))

    art = item.get('art', {})
    # Set Art mit Defaults falls nicht vorhanden
    li_item.setArt({
        'icon': 'DefaultTVShows.png',
        'fanart': art.get('tvshow.fanart', ''),
        'poster': art.get('tvshow.poster', ''),
        'banner': art.get('tvshow.banner', ''),
        'clearlogo': art.get('tvshow.clearlogo') or art.get('tvshow.logo') or '',
        'landscape': art.get('tvshow.landscape', ''),
        'clearart': art.get('tvshow.clearart', '')
    })

    has_video = False
    streamdetails = item.get('streamdetails', {})
    if streamdetails:
        for key, streams in streamdetails.items():
            for stream in streams:
                if key == "video":
                    has_video = True
                    video_detail = xbmc.VideoStreamDetail()
                    video_detail.setLanguage(stream.get('language', ''))
                    video_detail.setCodec(stream.get('codec', ''))
                    video_detail.setWidth(stream.get('width', 0))
                    video_detail.setHeight(stream.get('height', 0))
                    video_detail.setDuration(stream.get('duration', 0))
                    video_detail.setStereoMode(stream.get('stereo_mode', ''))
                    video_detail.setAspect(stream.get('aspect', 0))
                    info_tag.addVideoStream(video_detail)
                elif key == "audio":
                    audio_detail = xbmc.AudioStreamDetail()
                    audio_detail.setLanguage(stream.get('language', ''))
                    audio_detail.setCodec(stream.get('codec', ''))
                    audio_detail.setChannels(stream.get('channels', 2))
                    info_tag.addAudioStream(audio_detail)
                elif key == "subtitle":
                    subtitle_detail = xbmc.SubtitleStreamDetail()
                    subtitle_detail.setLanguage(stream.get('language', ''))
                    info_tag.addSubtitleStream(subtitle_detail)
    if not has_video:
        video_detail = xbmc.VideoStreamDetail()
        video_detail.setDuration(item.get('runtime', 0))
        info_tag.addVideoStream(video_detail)

    if season_num == '0':
        li_item.setProperty('IsSpecial', 'true')

    if 'cast' in item and isinstance(item['cast'], list):
        cast_names = [c.get('name', '').strip() for c in item['cast'] if c.get('name')]
        if cast_names:
            li_item.setProperty('cast', ', '.join(cast_names))
            li_item.setProperty('cast.0', cast_names[0])

    _set_ratings(li_item, item.get('ratings', {}))
    _set_unique_properties(li_item, director, 'director')
    _set_unique_properties(li_item, writer, 'writer')

    li.append((item.get('file', ''), li_item, False))


def handle_cast(li, item):
    li_item = xbmcgui.ListItem(label=item.get('name', ''), offscreen=True)
    li_item.setLabel(item.get('name', ''))
    li_item.setLabel2(item.get('role', ''))
    li_item.setProperty('role', item.get('role', ''))
    li_item.setArt({'icon': 'DefaultActor.png', 'thumb': item.get('thumbnail', '')})
    li.append(('', li_item, False))


def handle_genre(li, item):
    li_item = xbmcgui.ListItem(label=item.get('label', ''), offscreen=True)
    info_tag = li_item.getVideoInfoTag()
    info_tag.setTitle(item.get('label', ''))
    info_tag.setDbId(item.get('genreid', ''))
    info_tag.setPath(item.get('url', ''))
    info_tag.setMediaType('genre')
    art = item.get('art', {})
    if not art.get('icon'):
        art['icon'] = 'DefaultGenre.png'
    li_item.setArt(art)
    li.append((item.get('url', ''), li_item, True))


def get_unwatched(episode, watchedepisodes):
    try:
        episode = int(episode)
        watchedepisodes = int(watchedepisodes)
        return max(episode - watchedepisodes, 0)
    except Exception:
        return 0


def _get_cast(castData):
    listcast = []
    listcastandrole = []
    for castmember in castData:
        listcast.append(castmember.get('name', ''))
        listcastandrole.append((castmember.get('name', ''), castmember.get('role', '')))
    return [listcast, listcastandrole]


def _set_unique_properties(li_item, item, prop):
    try:
        i = 0
        for value in item:
            li_item.setProperty(f'{prop}.{i}', str(value))
            i += 1
    except Exception:
        pass
    return li_item


def _set_ratings(li_item, ratings):
    if not isinstance(ratings, dict):
        return li_item
    for key in ratings:
        try:
            rating = ratings[key].get('rating', 0)
            votes = ratings[key].get('votes', 0) or 0
            rating = float(rating)
            votes = int(votes)
            if rating > 100:
                continue
            if rating > 10:
                rating /= 10
            # setRating auf ListItem existiert nicht mehr -> als Property speichern
            li_item.setProperty(f'rating.{key}.value', str(rating))
            li_item.setProperty(f'rating.{key}.votes', str(votes))
        except Exception:
            pass
    return li_item
