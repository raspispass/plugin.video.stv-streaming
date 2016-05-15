import sys
import urllib
import urllib2
import urlparse
import json
import time
import datetime

def stvGetToken(username, password):
	url = 'https://auth.save.tv/token'
	id = '07f805dc51224ed783cc68bf7284a191'
	secret = '96625a899fee42bbbdc9809f4503675ff53b6fe24cb541228092ad4993858005'
	credentialValues = {'grant_type' : 'password',
						'client_id' : id,
						'client_secret' : secret,
						'username' : username,
						'password' : password }
	credentialData = urllib.urlencode(credentialValues)
	req = urllib2.Request(url, credentialData, {"Content-type": "application/x-www-form-urlencoded"})
	
	try:
		resp = urllib2.urlopen(req)
	except urllib2.HTTPError as e:
		if e.code == 400:
			jsResponse = json.loads(resp.read())
			# Passwort falsch: {"error":"invalid_request","error_description":"Login failed. Username = thomasfl, error code id = 49"}
			# User falsch: {"error":"invalid_request","error_description":"Login failed. Username = joe, error code id = 49"}
			# Secret falsch: {"error":"invalid_client","error_description":"Invalid client secret."}
			# Id falsch: {"error":"invalid_client","error_description":"No client with the provided id registered."}
			# alles falsch: {"error":"invalid_request","error_description":"Either client_id or client_secret not provided."}
			if jsResponse['error'] == 'invalid_client':
				stvError = 'Ganz schlechte Nachricht: API Key vom Save.TV Server abgelehnt'
			elif jsResponse['error'] == 'invalid_request':
				stvError = 'Username oder Passwort nicht akzeptiert'
			else:
				stvError = jsResponse['error_decription']
		else:
			stvError = 'Login mit unbekanntem Fehler gescheitert'
		stvToken = None
		stvTokenExpiry = None

	except urllib2.URLError as e:
		stvError = 'Save.TV Server nicht erreichbar'
		stvToken = None
		stvTokenExpiry = None

	else:
		stvError = None
		jsResponse = json.loads(resp.read())
		stvToken = jsResponse['access_token']
		stvTokenExpiry = time.time() + jsResponse['expires_in']

	return(stvError, stvToken, stvTokenExpiry)


def stvGetGroupsByKeyCount(stvToken, groupKey):
	# https://api.save.tv:443/v3/records/groups/title?limit=1&nopagingheader=true&recordstates=3
	
	baseUrl = 'https://api.save.tv:443/v3/records/groups/'
	query = { 
		'limit': 1, 
		'nopagingheader': True, 
		'recordstates': 3 
		}
	url = baseUrl + groupKey + '?' + urllib.urlencode(query)

	req = urllib2.Request(url, headers={"Authorization": "Bearer " + stvToken})
	resp = urllib2.urlopen(req)
	response = json.loads(resp.read())

	paging = response['paging']
	return(paging['totalCount'])


def stvGetGroupsByKey(stvToken, groupKey, filterDate, filterTvStation, filterGenre, startIndex):
	
	baseUrl = 'https://api.save.tv:443/v3/records/groups/'
	query = { 
		'fields': 'count,imageurl100,imageurl500,title', 
		'limit': 20, 
		'nopagingheader': True, 
		'offset': startIndex, 
		'recordstates': 3
		}
	if groupKey == 'date':
		query['sort'] = '-startdate'
	if filterTvStation != 0:
		query['tvstations'] = filterTvStation
	if filterDate != '': 
		query['minstartdate'] = filterDate
		query['maxstartdate'] = filterDate + datetime.timedelta(days=1)
	if filterGenre != '':
                query['tvcategories'] = filterGenre
	url = baseUrl + groupKey + '?' + urllib.urlencode(query)

	req = urllib2.Request(url, headers={"Authorization": "Bearer " + stvToken})
	resp = urllib2.urlopen(req)
	response = json.loads(resp.read())

	paging = response['paging']
	if paging['offset'] + paging['limit'] < paging['totalCount']:
		moreTitles = True
	else:
		moreTitles = False
	
	nextOffset = paging['offset'] + paging['limit']
	
	return(response['items'], moreTitles, nextOffset, paging['totalCount'])


telecastFields = 'telecastid,telecast.title,telecast.subtitle,telecast.tvcategory.name,telecast.startdate,telecast.enddate,telecast.tvstation.name,telecast.subject,telecast.episode,telecast.description,telecast.imageurl100,telecast.imageurl500,adfreeavailable,formats.recordformat.id,formats.recordformat.name'

def stvGetTelecastsByFilter(stvToken, filterTitle, filterDate, filterTvStation, filterGenre, startIndex):
	baseUrl = 'https://api.save.tv:443/v3/records'
	query = { 
		'exacttitle': filterTitle,
		'fields': telecastFields, 
		'limit': 20, 
		'nopagingheader': True, 
		'offset': startIndex, 
		'recordstates': 3
		}
	if filterTvStation != 0:
		query['tvstations'] = filterTvStation
	if filterDate != '': 
		query['minstartdate'] = filterDate
		query['maxstartdate'] = filterDate + datetime.timedelta(days=1)
	if filterGenre != '':
		query['tvcategories'] = filterGenre
		query['sort'] = '-startdate'
	url = baseUrl + '?' + urllib.urlencode(query)

	req = urllib2.Request(url, headers={"Authorization": "Bearer " + stvToken})
	resp = urllib2.urlopen(req)
	response = json.loads(resp.read())

	paging = response['paging']
	if paging['offset'] + paging['limit'] < paging['totalCount']:
		moreTitles = True
	else:
		moreTitles = False
	
	nextOffset = paging['offset'] + paging['limit']

        return(response['items'], moreTitles, nextOffset, paging['totalCount'])


def stvGetTelecastsByTitle(stvToken, title, startIndex):
	baseUrl = 'https://api.save.tv:443/v3/records'
	query = { 
		'exacttitle': title,
		'fields': telecastFields, 
		'limit': 20, 
		'nopagingheader': True, 
		'offset': startIndex, 
		'recordstates': 3 
		}
	url = baseUrl + '?' + urllib.urlencode(query)

	req = urllib2.Request(url, headers={"Authorization": "Bearer " + stvToken})
	resp = urllib2.urlopen(req)
	response = json.loads(resp.read())

	paging = response['paging']
	if paging['offset'] + paging['limit'] < paging['totalCount']:
		moreTitles = True
	else:
		moreTitles = False

        nextOffset = paging['offset'] + paging['limit']

        return(response['items'], moreTitles, nextOffset)


def stvGetTvStations(stvToken):
	#https://api.save.tv:443/v3/tvstations?fields=id%2C%20largelogourl%2C%20name&isrecordable=true

	baseUrl = 'https://api.save.tv:443/v3/tvstations'
	query = {
		'fields': 'id,largelogourl,name',
		'isrecordable': True 
	}
	url = baseUrl + '?' + urllib.urlencode(query)

	req = urllib2.Request(url, headers={"Authorization": "Bearer " + stvToken})
	resp = urllib2.urlopen(req)
	response = json.loads(resp.read())

	return(response)
	

def stvGetGenres(stvToken):
        baseUrl = 'https://api.save.tv:443/v3/tvcategories'
        query = {
                'fields': 'id,name'
        }
        url = baseUrl + '?' + urllib.urlencode(query)

        req = urllib2.Request(url, headers={"Authorization": "Bearer " + stvToken})
        resp = urllib2.urlopen(req)
        response = json.loads(resp.read())

        return(response)



def stvGetDownload(stvToken, telecastId, recordFormat, adFree):
	# https://api.save.tv:443/v3/records/11857786/downloads/6?adfree=true

	baseUrl = 'https://api.save.tv:443/v3/records'
	query = { 'adfree': adFree }
	url = baseUrl + '/' + str(telecastId) + '/downloads/' + str(recordFormat) + '?' + urllib.urlencode(query)

	req = urllib2.Request(url, headers={"Authorization": "Bearer " + stvToken})
	resp = urllib2.urlopen(req)
	response = json.loads(resp.read())

	return(response['streamingUrl'], response['estimatedFileSize'])

