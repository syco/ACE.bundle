from datetime import datetime, timedelta
import json
import re
import urllib

def Start():
  ObjectContainer.title1 = 'ACE'
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'
  HTTP.CacheTime = 0
  Log('Ace host: {}, Ace port: {}'.format(Prefs['ace_host'], Prefs['ace_port']))



@handler('/video/ace', 'ACE', thumb = 'logo.png', art = 'logo.png')
def MainMenu():
  oc = ObjectContainer(title2 = 'ACE')

  alink = "http://syco.netsons.org/scrapers/acestream/?action=&link="
  Log(alink)
  html = HTTP.Request(alink).content
  phpscrapers = json.loads(html)
  for phpscraper in phpscrapers:
    if phpscraper['action'] == "ace":
      oc.add(Show(
        url = 'http://{}:{}/ace/manifest.m3u8?id={}'.format(Prefs['ace_host'], Prefs['ace_port'], phpscraper['link']),
        title = phpscraper['title']
      ))
    else:
      oc.add(DirectoryObject(
        key = Callback(PHPScrapersList, title = phpscraper['title'], action = phpscraper['action'], link = phpscraper['link']),
        title = phpscraper['title']
      ))

  for tmp in Prefs['acestreamsearch_terms'].split(","):
    oc.add(DirectoryObject(
      key = Callback(PHPScrapersList, title = 'ASS '.format(tmp), action = 'acestreamsearch-search-0', link = tmp),
      title = 'ASS {}'.format(tmp)
    ))

  return oc



@route('/video/ace/phpscraperslist')
def PHPScrapersList(title, action, link):
  oc = ObjectContainer(title2 = title)

  alink = "http://syco.netsons.org/scrapers/acestream/?action={}&link={}".format(urllib.quote(action), urllib.quote(link))
  Log(alink)
  html = HTTP.Request(alink).content
  phpscrapers = json.loads(html)
  for phpscraper in phpscrapers:
    if phpscraper['action'] == "ace":
      oc.add(Show(
        url = 'http://{}:{}/ace/manifest.m3u8?id={}'.format(Prefs['ace_host'], Prefs['ace_port'], phpscraper['link']),
        title = phpscraper['title']
      ))
    else:
      oc.add(DirectoryObject(
        key = Callback(PHPScrapersList, title = phpscraper['title'], action = phpscraper['action'], link = phpscraper['link']),
        title = phpscraper['title']
      ))

  return oc



@route('/video/ace/show', include_container = bool)
def Show(url, title, include_container = False, **kwargs):
  vco = VideoClipObject(
    key = Callback(Show, url = url, title = title, include_container = True),
    rating_key = url,
    title = title,
    items = [
      MediaObject(
        protocol = Protocol.HLS,
        container = Container.MP4,
        video_codec = VideoCodec.H264,
        audio_codec = AudioCodec.AAC,
        audio_channels = 2,
        optimized_for_streaming = True,
        parts = [
          PartObject(
            key = HTTPLiveStreamURL(Callback(Play, url = url))
          )
        ],
      )
    ]
  )
  if include_container:
    return ObjectContainer(objects = [vco])
  else:
    return vco



@indirect
@route('/video/ace/play.m3u8')
def Play(url, **kwargs):
  Log(' --> Final stream url: %s' % (url))
  return IndirectResponse(VideoClipObject, key = url)
