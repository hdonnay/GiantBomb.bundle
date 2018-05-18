#!/bin/false
# This isn't a script

from urlparse import urlsplit, urlunsplit
from urllib import urlencode

TITLE    = 'Giant Bomb'
PREFIX   = '/video/giantbomb-uo'

# The images below are the default graphic for your channel and should be saved or located in you Resources folder
# The art and icon should be a certain size for channel submission. The graphics should be good quality and not be blurry
# or pixelated. Icons must be 512x512 PNG files and be named, icon-default.png. The art must be 1280x720 JPG files and be
# named, art-default.jpg. The art shows up in the background of the PMC Client, so you want to make sure image you choose 
# is not too busy or distracting.  I tested out a few in PMC to figure out which one looked best.

ART      = 'art-default.jpg'
ICON     = 'icon-default.png'

# Below you would set any other global variables you may want to use in your programming. I tend to automatically create 
# a base url for the website I am accessing to add to any urls that are returned with just the folder path and not the 
# whole url and an http for urls that are returned to the channel without these at the beginning

WebsiteURL = 'https://www.giantbomb.com'
API = WebsiteURL+'/api'
AppURL = WebsiteURL+'/app/plex'


def apiCall(resouce, args=None):
    '''Does API calls or throws an ApiEx.'''
    if args is None:
        args = {}
    args.update(Dict)
    j = JSON.ObjectFromURL(API+resource,
            values=args, headers={}, timeout=30)
    if 'error' not in j:
        log.Warning("wild api response: {}" % str(j))
    if j['error'] is not 'OK':
        Log.Debug("api error: {}" % j['error'])
        raise ApiEx("Giant Bomb Plugin Error", j['error'])
    return j

  
def filterVideos(f=None):
    '''
    Uses the string 'f' as a filter to /api/videos.

    Returns a list of EpisodeObjects.
    '''
    qs = {}
    if f is not None:
        qs['filter'] = f
    req = apiCall('/videos', qs)
    return [EpisodeObject(
                url = e['site_detail_url'],
                show=e['video_show']['title'],
                title=e['name'],
                summary=e['deck'],
                duration=e['length_seconds'] * 1000,
                originally_available_at=Datetime.ParseDate(e['publish_date']).date(),
                thumb=Resource.ContentsOfURLWithFallback(url=e['image']['medium_url']),
            ) for e in req.results]


def Start():
    '''
    This is all default.
    '''
    log.Debug("starting")
    ObjectContainer.title1 = TITLE
    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    EpisodeObject.thumb = R(ICON)
    EpisodeObject.art = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)


def ValidatePrefs():
    '''
    This does the authorization scheme described here:

    https://www.giantbomb.com/profile/wcarle/blog/how-to-authenticate-a-gb-app/114534/
    '''
    Dict.Reset()
    Dict['format'] = 'json'
    code = Prefs['regCode']
    if code == '':
        return MessageContainer("Registration code not provided")
    Log.Debug("attempting to use supplied regCode: {}", code)

    req = JSON.ObjectFromURL(AppURL+'/get-result', values={'regCode': code, 'format': 'json'}, headers={})
    if req['status'] != 'success':
        Log.Debug("get-result failed, got: "+str(req))
        return MessageContainer(req['error'])

    Dict['api_token'] = str(req['regToken'])
    Dict.Save()


@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():
    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(Latest), title='Latest', thumb=R(ICON)))
    oc.add(DirectoryObject(key=Callback(Shows), title='Shows', thumb=R(ICON)))
    oc.add(DirectoryObject(key=Callback(Categories), title='Categories', thumb=R(ICON)))
    # TOOO(hank): Add search.
    oc.add(PrefsObject(title='Preferences', thumb=R(ICON_PREFS)))
    return oc


@route(PREFIX+'/latest')
def Latest():
    '''
    Latest queries the video firehose.
    '''
    return ObjectContainer(title2='Latest', objects=filterVideos())


@route(PREFIX+'/shows')
def Shows():
    '''
    '''
    oc = ObjectContainer(title2='Shows')
    req = apiCall('/video_shows')
    # Check error
    for s in req.results:
        title = s['title']
        oc.add(DirectoryObject(
            key=Callback(key=Show(show_id=s['id'], title=title)),
            title=title,
            thumb=s['image']['medium_url'],
            summary=s['deck'],
            ))
    return oc


@route(PREFIX+'/categories')
def Categories():
    '''
    '''
    oc = ObjectContainer(title2='Categories')
    req = apiCall('/video_categories')
    # Check error
    for s in req.results:
        title = s['name']
        oc.add(DirectoryObject(
            key=Callback(key=Category(cat_id=s['id'], title=title)),
            title=title,
            thumb=s['image']['medium_url'],
            summary=s['deck'],
            ))
    return oc


@route(PREFIX+'/show/')
def Show(show_id, title):
    '''
    '''
    try:
        eps = filterVideos('video_show:'+show_id)
    except ApiEx as e:
        return e.oc()
    return ObjectContainer(title2=title, objects=eps)


@route(PREFIX+'/category/')
def Category(cat_id, title):
    '''
    '''
    try:
        eps = filterVideos('video_categories:'+cat_id)
    except ApiEx as e:
        return e.oc()
    return ObjectContainer(title2=title, objects=eps)


class ApiEx(Exception):
    def __init__(self, header, message):
        self.__header = header
        self.__message = message

    def oc(self):
        return ObjectContainer(
                header=self.__header,
                message=self.__message,
                )
