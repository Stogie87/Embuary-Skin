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
    genre = item.get('genre', '')
    studio = item.get('studio', '')
    country = item.get('country', '')
    director = item.get('director', '')
    writer = item.get('writer', '')

    li_item = xbmcgui.ListItem(item['title'], offscreen=True)
    info_tag = li_item.getVideoInfoTag()
    info_tag.setTitle(item['title'])
    info_tag.setOriginalTitle(item['originaltitle'])
    info_tag.setSortTitle(item['sorttitle'])
    info_tag.setYear(item['year'])
    info_tag.setGenres([g for g in genre] if isinstance(genre, list) else [genre])
    info_tag.setStudios([s for s in studio] if isinstance(studio, list) else [studio])
    info_tag.setCountries([c for c in country] if isinstance(country, list) else [country])
    info_tag.setDirectors([d for d in director] if isinstance(director, list) else [director])
    info_tag.setWriters([w for w in writer] if isinstance(writer, list) else [writer])
    info_tag.setPlot(item['plot'])
    info_tag.setPlotOutline(item['plotoutline'])
    info_tag.setIMDBNumber(item['imdbnumber'])
    info_tag.setTags(item['tag'] if isinstance(item['tag'], list) else [item['tag']])
    info_tag.setRating(float(item['rating']), votes=int(item['votes']))
    info_tag.setUserRating(int(float(item['userrating'])))
    info_tag.setLastPlayed(item['lastplayed'])
    info_tag.setMediaType('movie')
    info_tag.setTrailer(item['trailer'])
    info_tag.setDateAdded(item['dateadded'])
    info_tag.setPremiered(item['premiered'])
    info_tag.setPath(item['file'])
    info_tag.setPlaycount(item['playcount'])
    info_tag.setSet(item['set'])
    info_tag.setSetId(item['setid'])
    info_tag.setTop250(item['top250'])
    info_tag.setResumePoint(item['resume']['position'], item['resume']['total'])
    li_item.setProperty('tagline', item.get('tagline', ''))
    li_item.setProperty('mpaa', item.get('mpaa', ''))

    if 'cast' in item and isinstance(item['cast'], list):
        cast_list = []
        for cast_member in item['cast']:
            name = cast_member.get('name', '').strip()
            if not name:
                continue
            actor = xbmc.Actor(name)
            actor.setRole(cast_member.get('role', ''))
            actor.setThumbnail(cast_member.get('thumbnail', ''))
            cast_list.append(actor)
        if cast_list:
            info_tag.setCast(cast_list)
            cast_actors = _get_cast(item['cast'])
            _set_unique_properties(li_item, cast_actors[0], 'cast')

    _set_ratings(li_item, item['ratings'])
    _set_unique_properties(li_item, genre, 'genre')
    _set_unique_properties(li_item, studio, 'studio')
    _set_unique_properties(li_item, country, 'country')
    _set_unique_properties(li_item, director, 'director')
    _set_unique_properties(li_item, writer, 'writer')
    li_item.setArt(item['art'])
    li_item.setArt({'icon': 'DefaultVideo.png'})

    hasVideo = False
    for key, value in (item['streamdetails'] or {}).items():
        for stream in value:
            if key == "video":
                hasVideo = True
                video_detail = xbmc.VideoStreamDetail()
                video_detail.setLanguage(stream.get('language', ''))
                video_detail.setCodec(stream.get('codec', ''))
                video_detail.setWidth(stream.get('width', 0))
                video_detail.setHeight(stream.get('height', 0))
                video_detail.setDuration(stream.get('duration', 0))
                video_detail.setStereoMode(stream.get('stereo_mode', ''))
                video_detail.setAspect(stream.get('aspect', 0))
                hdr_type = stream.get('hdrtype') or stream.get('hdrType') or stream.get('hdr_type') or ''
                if hdr_type:
                    try:
                        video_detail.setHDRType(hdr_type)
                    except AttributeError:
                        pass
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
    if not hasVideo:
        video_detail = xbmc.VideoStreamDetail()
        video_detail.setDuration(item['runtime'])
        info_tag.addVideoStream(video_detail)

    if searchstring:
        li_item.setProperty('searchstring', searchstring)

    li.append((item['file'], li_item, False))

def handle_tvshows(li, item, searchstring=None):
    genre = item.get('genre', '')
    studio = item.get('studio', '')
    dbid = item['tvshowid']
    season = item['season']
    episode = item['episode']
    watchedepisodes = item['watchedepisodes']
    unwatchedepisodes = get_unwatched(episode, watchedepisodes)

    if not condition('Window.IsVisible(movieinformation)'):
        folder = True
        item['file'] = 'videodb://tvshows/titles/%s/' % dbid
    else:
        folder = False
        item['file'] = 'plugin://script.embuary.helper/?action=folderjump&type=tvshow&dbid=%s' % dbid

    li_item = xbmcgui.ListItem(item['title'], offscreen=True)
    info_tag = li_item.getVideoInfoTag()
    info_tag.setTitle(item['title'])
    info_tag.setYear(item['year'])
    info_tag.setSortTitle(item['sorttitle'])
    info_tag.setOriginalTitle(item['originaltitle'])
    info_tag.setGenres([g for g in genre] if isinstance(genre, list) else [genre])
    info_tag.setStudios([s for s in studio] if isinstance(studio, list) else [studio])
    info_tag.setPlot(item['plot'])
    info_tag.setRating(float(item['rating']), votes=int(item['votes']))
    info_tag.setUserRating(int(float(item['userrating'])))
    info_tag.setPremiered(item['premiered'])
    info_tag.setTags(item['tag'] if isinstance(item['tag'], list) else [item['tag']])
    info_tag.setMediaType('tvshow')
    info_tag.setIMDBNumber(item['imdbnumber'])
    info_tag.setLastPlayed(item['lastplayed'])
    info_tag.setPath(item['file'])
    info_tag.setDuration(item['runtime'])
    info_tag.setDateAdded(item['dateadded'])
    info_tag.setPlaycount(item['playcount'])
    info_tag.setSeason(season)
    info_tag.setEpisode(episode)
    li_item.setProperty('mpaa', item.get('mpaa', ''))

    if 'cast' in item and isinstance(item['cast'], list):
        cast_list = []
        for cast_member in item['cast']:
            name = cast_member.get('name', '').strip()
            if not name:
                continue
            actor = xbmc.Actor(name)
            actor.setRole(cast_member.get('role', ''))
            actor.setThumbnail(cast_member.get('thumbnail', ''))
            cast_list.append(actor)
        if cast_list:
            info_tag.setCast(cast_list)
            cast_actors = _get_cast(item['cast'])
            _set_unique_properties(li_item, cast_actors[0], 'cast')

    _set_ratings(li_item, item['ratings'])
    _set_unique_properties(li_item, genre, 'genre')
    _set_unique_properties(li_item, studio, 'studio')
    li_item.setProperty('totalseasons', str(season))
    li_item.setProperty('totalepisodes', str(episode))
    li_item.setProperty('watchedepisodes', str(watchedepisodes))
    li_item.setProperty('unwatchedepisodes', str(unwatchedepisodes))
    li_item.setProperty('showtitle', item['title'])
    li_item.setArt(item['art'])
    li_item.setArt({'icon': 'DefaultVideo.png'})

    if searchstring:
        li_item.setProperty('searchstring', searchstring)

    li.append((item['file'], li_item, folder))

def handle_seasons(li, item):
    tvshowdbid = item['tvshowid']
    season = item['season']
    episode = item['episode']
    watchedepisodes = item['watchedepisodes']
    unwatchedepisodes = get_unwatched(episode, watchedepisodes)

    if season == 0:
        title = '%s' % (xbmc.getLocalizedString(20381))
        special = 'true'
    else:
        title = '%s %s' % (xbmc.getLocalizedString(20373), season)
        special = 'false'

    if not condition('Window.IsVisible(movieinformation)'):
        folder = True
        file = 'videodb://tvshows/titles/%s/%s/' % (tvshowdbid, season)
    else:
        folder = False
        file = 'plugin://script.embuary.helper/?action=folderjump&type=season&dbid=%s&season=%s' % (tvshowdbid, season)

    li_item = xbmcgui.ListItem(title, offscreen=True)
    info_tag = li_item.getVideoInfoTag()
    info_tag.setTitle(title)
    info_tag.setSeason(season)
    info_tag.setEpisode(episode)
    info_tag.setPlaycount(item['playcount'])
    info_tag.setMediaType('season')
    info_tag.setDbId(item['seasonid'])
    li_item.setProperty('showtitle', item['showtitle'])
    li_item.setArt(item['art'])
    li_item.setArt({'icon': 'DefaultVideo.png', 'fanart': item['art'].get('tvshow.fanart', '')})
    li_item.setProperty('watchedepisodes', str(watchedepisodes))
    li_item.setProperty('unwatchedepisodes', str(unwatchedepisodes))
    li_item.setProperty('isspecial', special)
    li_item.setProperty('season_label', item.get('label', ''))
    li_item.setProperty('mpaa', item.get('mpaa', ''))
    li.append((file, li_item, folder))

def handle_episodes(li, item):
    director = item.get('director', '')
    writer = item.get('writer', '')

    if item['episode'] < 10:
        label = '0%s. %s' % (item['episode'], item['title'])
    else:
        label = '%s. %s' % (item['episode'], item['title'])

    if item['season'] == '0':
        label = 'S' + label
    else:
        label = '%sx%s' % (item['season'], label)

    li_item = xbmcgui.ListItem(label, offscreen=True)
    info_tag = li_item.getVideoInfoTag()
    info_tag.setTitle(item['title'])
    info_tag.setEpisode(item['episode'])
    info_tag.setSeason(item['season'])
    info_tag.setPremiered(item['firstaired'])
    info_tag.setDbId(item['episodeid'])
    info_tag.setPlot(item['plot'])
    info_tag.setOriginalTitle(item['originaltitle'])
    info_tag.setLastPlayed(item['lastplayed'])
    info_tag.setRating(float(item.get('rating', 0)), votes=int(item.get('votes', 0)))
    info_tag.setUserRating(int(float(item['userrating'])))
    info_tag.setPlaycount(item['playcount'])
    info_tag.setDirectors([d for d in director] if isinstance(director, list) else [director])
    info_tag.setWriters([w for w in writer] if isinstance(writer, list) else [writer])
    info_tag.setPath(item['file'])
    info_tag.setDateAdded(item['dateadded'])
    info_tag.setMediaType('episode')
    info_tag.setResumePoint(item['resume']['position'], item['resume']['total'])
    li_item.setProperty('showtitle', item['showtitle'])
    li_item.setProperty('mpaa', item.get('mpaa', ''))

    if 'cast' in item and isinstance(item['cast'], list):
        cast_list = []
        for cast_member in item['cast']:
            name = cast_member.get('name', '').strip()
            if not name:
                continue
            actor = xbmc.Actor(name)
            actor.setRole(cast_member.get('role', ''))
            actor.setThumbnail(cast_member.get('thumbnail', ''))
            cast_list.append(actor)
        if cast_list:
            info_tag.setCast(cast_list)
            cast_actors = _get_cast(item['cast'])
            _set_unique_properties(li_item, cast_actors[0], 'cast')

    _set_ratings(li_item, item['ratings'])
    _set_unique_properties(li_item, director, 'director')
    _set_unique_properties(li_item, writer, 'writer')
    li_item.setProperty('season_label', item.get('season_label', ''))

    li_item.setArt({'icon': 'DefaultTVShows.png',
                    'fanart': item['art'].get('tvshow.fanart', ''),
                    'poster': item['art'].get('tvshow.poster', ''),
                    'banner': item['art'].get('tvshow.banner', ''),
                    'clearlogo': item['art'].get('tvshow.clearlogo') or item['art'].get('tvshow.logo') or '',
                    'landscape': item['art'].get('tvshow.landscape', ''),
                    'clearart': item['art'].get('tvshow.clearart', '')})
    li_item.setArt(item['art'])

    hasVideo = False
    for key, value in (item['streamdetails'] or {}).items():
        for stream in value:
            if key == "video":
                hasVideo = True
                video_detail = xbmc.VideoStreamDetail()
                video_detail.setLanguage(stream.get('language', ''))
                video_detail.setCodec(stream.get('codec', ''))
                video_detail.setWidth(stream.get('width', 0))
                video_detail.setHeight(stream.get('height', 0))
                video_detail.setDuration(stream.get('duration', 0))
                video_detail.setStereoMode(stream.get('stereo_mode', ''))
                video_detail.setAspect(stream.get('aspect', 0))
                hdr_type = stream.get('hdrtype') or stream.get('hdrType') or stream.get('hdr_type') or ''
                if hdr_type:
                    try:
                        video_detail.setHDRType(hdr_type)
                    except AttributeError:
                        pass
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
    if not hasVideo:
        video_detail = xbmc.VideoStreamDetail()
        video_detail.setDuration(item['runtime'])
        info_tag.addVideoStream(video_detail)

    if item['season'] == '0':
        li_item.setProperty('IsSpecial', 'true')

    li.append((item['file'], li_item, False))

def handle_cast(li, item):
    li_item = xbmcgui.ListItem(item['name'], offscreen=True)
    li_item.setLabel(item['name'])
    li_item.setLabel2(item['role'])
    li_item.setProperty('role', item['role'])
    li_item.setArt({'icon': 'DefaultActor.png', 'thumb': item.get('thumbnail', '')})
    li.append(('', li_item, False))

def handle_genre(li, item):
    li_item = xbmcgui.ListItem(item['label'], offscreen=True)
    info_tag = li_item.getVideoInfoTag()
    info_tag.setTitle(item['label'])
    info_tag.setDbId(item['genreid'])
    info_tag.setPath(item['url'])
    info_tag.setMediaType('genre')
    li_item.setArt(item['art'])
    li_item.setArt({'icon': 'DefaultGenre.png'})
    li.append((item['url'], li_item, True))

def get_unwatched(episode, watchedepisodes):
    if episode > watchedepisodes:
        return episode - watchedepisodes
    else:
        return 0

def _get_cast(castData):
    listcast = []
    listcastandrole = []
    for castmember in castData:
        listcast.append(castmember['name'])
        listcastandrole.append((castmember['name'], castmember['role']))
    return [listcast, listcastandrole]

def _set_unique_properties(li_item, item, prop):
    try:
        i = 0
        for value in item:
            li_item.setProperty('%s.%s' % (prop, i), value)
            i += 1
    except Exception:
        pass
    return li_item

def _set_ratings(li_item, item):
    info_tag = li_item.getVideoInfoTag()
    for key in item:
        try:
            rating = item[key]['rating']
            votes = item[key]['votes'] or 0
            if rating > 100:
                raise Exception
            elif rating > 10:
                rating = rating / 10
            # key entspricht dem Rating-Typ, z. B. 'imdb', 'tmdb', 'user' etc.
            # Kodi Omega erwartet das 3. Argument für den Rating-Typ.
            info_tag.setRating(float(rating), int(votes), key)
        except Exception:
            pass
    return li_item
