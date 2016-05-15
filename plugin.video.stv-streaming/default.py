# -*- encoding: utf-8 -*-
import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import json
import time
import datetime
import re
import resources.lib.savetv as savetv

# Settings
stvUsername = xbmcplugin.getSetting(int(sys.argv[1]),'stvUsername')
stvPassword = xbmcplugin.getSetting(int(sys.argv[1]),'stvPassword')
stvAdfree = xbmcplugin.getSetting(int(sys.argv[1]),'stvAdfree')
stvQualities = { 'Xvid SD': 1, 'H.264 Mobile': 4, 'H.264 SD': 5, 'H.264 HD': 6 }
stvQuality = stvQualities[xbmcplugin.getSetting(int(sys.argv[1]),'stvQuality')]
if time.localtime().tm_isdst:
	stvTzDelta = datetime.timedelta(hours=2)
else:
	stvTzDelta = datetime.timedelta(hours=1)

# Default initialization
#   base_url 	 = The base URL of your add-on, e.g. 'plugin://plugin.video.stv-streaming/'
#   addon_handle = The process handle for this add-on, as a numeric string 
#   args 	 = The query string passed to your add-on, e.g. '?foo=bar&baz=quux'
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:]) # '?foo=bar&foo=baz&quux=spam' ==> {'foo': ['bar', 'baz'], 'quux': ['spam']}

# Default method
#   Builds URLs like 'plugin://plugin.video.myaddon/?mode=folder&foldername=Folder+One'
def build_url(query):
	# Unicode in str umwandeln
	queryStr = {}
	for k, v in query.iteritems():
		queryStr[k] = unicode(v).encode('utf-8')
	return base_url + '?' + urllib.urlencode(queryStr)

# Build level 1 navigation (Nach Titel, Nach Datum, Nach Sender, Nach Genre)
def build_category(item, name):
	li = xbmcgui.ListItem(label=name, iconImage='DefaultTVShows.png')
	url = build_url({'stvToken': stvToken, 'mode': 'category', 'category': item})
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

# Build level 2 navigation (Nach Titeln)
def build_titlegroup(item):
	name = item['title']
	li = xbmcgui.ListItem(label=name, iconImage='DefaultTVShows.png')
	li.setArt({'thumb': item['imageUrl500'], 'fanart': item['imageUrl500']})
	li.setInfo('video', {'count': item['count']})
	url = build_url({'stvToken': stvToken, 'mode': 'group', 'groupName': name, 'groupBy': 'title'})
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

# Build level 2 navigation (Nach Datum)
def build_dategroup(item):
	name = item['title']
	li = xbmcgui.ListItem(label=name, iconImage='DefaultTVShows.png')
	url = build_url({'stvToken': stvToken, 'mode': 'group', 'groupName': item['key'], 'groupBy': 'date'})
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

# Build level 2 navigation (Nach Sender)
def build_tvStationGroup(item):
	name = item['name']
	li = xbmcgui.ListItem(label=name, iconImage='DefaultTVShows.png')
	li.setArt({'thumb': item['largeLogoUrl']})
	url = build_url({'stvToken': stvToken, 'mode': 'group', 'groupName': item['id'], 'groupBy': 'tvstation'})
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

# Build level 2 navigation (Nach Genre)
def build_tvGenreGroup(item):
	name = item['name']
        li = xbmcgui.ListItem(label=name, iconImage='DefaultTVShows.png')
        url = build_url({'stvToken': stvToken, 'mode': 'group', 'groupName': item['id'], 'groupBy': 'genre'})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

# Build level 3 navigation (Film-Liste)
def build_telecast(item):
	telecast = item['telecast']
	title = telecast['title']
	subTitle = telecast['subTitle']
	id = telecast['id']
	startDate = datetime.datetime(*map(int, re.split('[^\d]', telecast['startDate'])[:-1])) + stvTzDelta
	endDate = datetime.datetime(*map(int, re.split('[^\d]', telecast['endDate'])[:-1])) + stvTzDelta
	duration = endDate - startDate
	tvStation = telecast['tvStation']['name']
	info = {
		'genre': telecast['tvCategory']['name'],
		'title': title,
		'episode': telecast['episode'],
		'tagline': subTitle,
		'plot': telecast['description'],
		'duration': duration.seconds
		}
	if subTitle:
		label = subTitle
	else:
		label = title
	#BACKUP: label = label + ' (' + tvStation + ' ' + startDate.strftime('%d.%m.%Y %H:%M') + ')'

	li = xbmcgui.ListItem(label = label, iconImage = 'DefaultTVShows.png')
	li.setArt({'thumb': telecast['imageUrl100'], 'fanart': telecast['imageUrl500']})
	li.setInfo('video', info)
	#li.setProperty('IsPlayable', 'true')

	availableFormats = []
	recordFormats = item['formats']
	for recordFormat in recordFormats:
		formatId = recordFormat['recordFormat']['id']
		availableFormats.append(str(formatId))

	url = build_url({'stvToken': stvToken, 'mode': 'telecast', 'telecastId': id, 'label': label, 'recordFormats': ','.join(availableFormats) })
	xbmcplugin.addDirectoryItem(handle = addon_handle, url = url, listitem = li, isFolder=True)

mode = args.get('mode', None)

# Main (first execution)
if mode is None:
	stvError, stvToken, stvTokenExpy = savetv.stvGetToken(stvUsername, stvPassword)
	if stvError:
		xbmcgui.Dialog().ok('Save.TV Streaming Plugin', 'Fehler beim Login:', stvError)
	else:
		build_category('title', 'Nach Titel der Sendung')
		build_category('date', 'Nach Datum')
		build_category('tvstation', 'Nach Sender')
		build_category('genre', 'Nach Genre')
		xbmcplugin.endOfDirectory(addon_handle)

# Level 1 navigation (Nach Titel, Nach Datum, Nach Sender, Nach Genre)
elif mode[0] == 'category':
	stvToken = args['stvToken'][0]
	category = args['category'][0]
	# In case of initial start there is no page offset set
	if args.get('hasMorePagesOffset', None) is None:
		hasMorePagesOffset = 0
	else:
		hasMorePagesOffset = args['hasMorePagesOffset'][0]
	if category == 'title':
		# stvGetGroupsByKey(stvToken, groupKey, filterDate, filterTvStation, filterGenre, startIndex)
		titles, hasMore, nextOffset, totalCount = savetv.stvGetGroupsByKey(stvToken, 'title', '', 0, '', hasMorePagesOffset)
		for title in titles:
			build_titlegroup(title)
		# Add hasMore Listitem
		if hasMore:
			nextPage = str(int((nextOffset) / 20)+1)
			totalPages = str(int(totalCount / 20))
                	li = xbmcgui.ListItem(label= "Nächste Seite (" + nextPage + " / " + totalPages + ")", iconImage='DefaultTVShows.png')
			url = build_url({'stvToken': stvToken, 'mode': 'category', 'category': 'title', 'hasMorePagesOffset': nextOffset})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

	elif category == 'date':
		dates, hasMore, nextOffset, totalCount = savetv.stvGetGroupsByKey(stvToken, 'date', '', 0, '', hasMorePagesOffset)
		for date in dates:
			build_dategroup(date)
                # Add hasMore Listitem
                if hasMore:
                        nextPage = str(int((nextOffset) / 20)+1)
                        totalPages = str(int(totalCount / 20))
                        li = xbmcgui.ListItem(label= "Nächste Seite (" + nextPage + " / " + totalPages + ")", iconImage='DefaultTVShows.png')
                        url = build_url({'stvToken': stvToken, 'mode': 'category', 'category': 'date', 'hasMorePagesOffset': nextOffset})
                        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

	elif category == 'tvstation':
		tvStations = savetv.stvGetTvStations(stvToken)
		for tvStation in tvStations:
			build_tvStationGroup(tvStation)	
	elif category == 'genre':
		genres = savetv.stvGetGenres(stvToken)
                for genre in genres:
                        build_tvGenreGroup(genre)


	xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'group':
	stvToken = args['stvToken'][0]
	filter = args['groupName'][0]
	groupBy = args['groupBy'][0]
        # In case of initial start there is no page offset set
        if args.get('hasMorePagesOffset', None) is None:
                hasMorePagesOffset = 0
        else:
                hasMorePagesOffset = args['hasMorePagesOffset'][0]
	filterTitle = ''
	filterDate = ''
	filterTvStation = 0
	filterGenre = ''
	if groupBy == 'title': 
		filterTitle = filter
	elif groupBy == 'date':
		filterDate = datetime.datetime(*map(int, filter.split('-'))) - stvTzDelta
	elif groupBy == 'tvstation':
		filterTvStation = filter
	elif groupBy == 'genre':
		filterGenre = filter
	telecasts, hasMore, nextOffset, totalCount = savetv.stvGetTelecastsByFilter(stvToken, filterTitle, filterDate, filterTvStation, filterGenre, hasMorePagesOffset)

	xbmcplugin.setContent(addon_handle, 'movies')
	for telecast in telecasts:
		build_telecast(telecast)

        # Add hasMore Listitem
        if hasMore:
                nextPage = str(int((nextOffset) / 20)+1)
                totalPages = str(int(totalCount / 20))
                li = xbmcgui.ListItem(label= "Nächste Seite (" + nextPage + " / " + totalPages + ")", iconImage='DefaultTVShows.png')
                url = build_url({'stvToken': stvToken, 'mode': 'group', 'groupName': filter, 'groupBy': groupBy, 'hasMorePagesOffset': nextOffset})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

	xbmc.executebuiltin("Container.SetViewMode(504)")
	xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'telecast':
	stvToken = args['stvToken'][0]
	telecastId = args['telecastId'][0]
	label = args['label'][0]
	recordFormats = map(int, args['recordFormats'][0].split(','))

	if stvQuality in recordFormats:
		quality = stvQuality
	else:
		quality = max(recordFormats)
	streamingUrl, estimatedFileSize = savetv.stvGetDownload(stvToken, telecastId, quality, stvAdfree)
	# Create a playable item with a path to play.
	play_item = xbmcgui.ListItem(label=label, path=streamingUrl)
	# Pass the item to the Kodi player.
	print('play here')
	#xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
	xbmc.Player().play(streamingUrl, play_item)
