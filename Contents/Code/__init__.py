from datetime import datetime, timedelta
import json
import re

def Start():
  ObjectContainer.title1 = 'ACE'
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'
  HTTP.CacheTime = 0
  Log('Ace host: {}, Ace port: {}'.format(Prefs['ace_host'], Prefs['ace_port']))

@handler('/video/ace', 'ACE', thumb = 'logo.png', art = 'logo.png')
def MainMenu():
  oc = ObjectContainer(title2 = 'ACE')
  oc.add(
    DirectoryObject(
      key = Callback(ArenavisionList, title = 'Arenavision'),
      title = 'Arenavision'
    )
  )
  oc.add(
    DirectoryObject(
      key = Callback(RedditList, title = 'Reddit/Soccerstreams'),
      title = 'Reddit/Soccerstreams'
    )
  )
  return oc


@route('/video/ace/arenavisionlist')
def ArenavisionList(title):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(ArenavisionList, title = title),
      title = 'Refresh'
    )
  )
  today = '{:%d/%m/%Y}'.format(datetime.utcnow())
  tomorrow = '{:%d/%m/%Y}'.format(datetime.utcnow() + timedelta(days=1))
  html = HTML.ElementFromURL('http://arenavision.in/guide', '', {'Cookie': 'beget=begetok; expires=' + ('{:%a, %d %b %Y %H:%M:%S GMT}'.format(datetime.utcnow() + timedelta(seconds=19360000))) + '; path=/'})
  for item in html.xpath('//tr[count(./td)>=6]'):
    av_date = item.xpath('./td[1]/text()')[0].decode('utf-8')
    if today != av_date and tomorrow !=av_date:
      continue
    av_time = item.xpath('./td[2]/text()')[0].decode('utf-8')
    av_sport = item.xpath('./td[3]/text()')[0].decode('utf-8')
    av_tournament = item.xpath('./td[4]/text()')[0].decode('utf-8')
    av_match = item.xpath('./td[5]/text()')[0].decode('utf-8')
    av_langs = ''
    urls = []
    for t1 in item.xpath('./td[6]/text()'):
      tokens = t1.split(' ')
      av_langs = av_langs + ' ' + tokens[1]
      for c in tokens[0].split('-'):
        c = c.strip()
        if c[0] == 'W':
          urls.append(tokens[1] + '!' + (html.xpath('//a[text()="World Cup ' + c[1:] + '"]')[0]).get('href'))
        else:
          urls.append(tokens[1] + '!' + (html.xpath('//a[text()="ArenaVision ' + c + '"]')[0]).get('href'))
    title = av_date + ' ' + av_time + ' | ' + av_sport + ' | ' + av_tournament + ' | ' + av_match + ' |' + av_langs
    oc.add(
      DirectoryObject(
        key = Callback(ArenavisionSubList, title = title, url = '|'.join(urls)),
        title = title
      )
    )
  return oc

@route('/video/ace/arenavisionsublist')
def ArenavisionSubList(title, url):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(ArenavisionSubList, title = title, url = url),
      title = 'Refresh'
    )
  )
  pattern = re.compile(r'acestream:\/\/([0-z]{40})', re.IGNORECASE)
  for r in url.split('|'):
    t = r.split('!')
    html = HTTP.Request(t[1]).content
    for m in re.finditer(pattern, html):
      Log(m.group(1))
      oc.add(
        Show(
          url = 'http://{}:{}/ace/manifest.m3u8?id={}'.format(Prefs['ace_host'], Prefs['ace_port'], m.group(1)),
          title = t[0]
        )
      )
  return oc


@route('/video/ace/redditlist')
def RedditList(title):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(RedditList, title = title),
      title = 'Refresh'
    )
  )
  html = HTML.ElementFromURL('https://www.reddit.com/r/soccerstreams/')
  for item in html.xpath('//a[.//*[contains(translate(text(), "ABCDEFGHJIKLMNOPQRSTUVWXYZ", "abcdefghjiklmnopqrstuvwxyz"), " vs")]]'):
    title = (item.xpath('./h2/text()')[0]).decode('utf-8')
    href = item.get('href');
    oc.add(
      DirectoryObject(
        key = Callback(RedditSubList, title = title, url = href),
        title = title
      )
    )
  return oc

@route('/video/ace/redditsublist')
def RedditSubList(title, url):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(RedditSubList, title = title, url = url),
      title = 'Refresh'
    )
  )
  html = HTTP.Request('https://www.reddit.com{}'.format(url)).content
  pattern = re.compile(r'((?:\[[^\[\]]+\]\s+)*)acestream:\/\/([0-z]{40})((?:\s+\[[^\[\]]+\])*)', re.IGNORECASE)
  lang_0 = []
  lang_1 = []
  for m in re.finditer(pattern, html):
    aceid = m.group(2)
    acedesc = m.group(1) + m.group(3) + '   [ ' + aceid + ' ]'
    url = 'http://{}:{}/ace/manifest.m3u8?id={}'.format(Prefs['ace_host'], Prefs['ace_port'], aceid),
    if re.search('\[(ar|croatian|es|esp|ger|german|kazakh|pl|portugal|pt|ru|spanish|ukrainian)\]', acedesc, re.IGNORECASE) == None:
      lang_1.append(
        Show(
          url = url,
          title = acedesc.decode('utf-8')
        )
      )
    else:
      lang_0.append(
        Show(
          url = url,
          title = acedesc.decode('utf-8')
        )
      )
    for e in lang_0:
      oc.add(e)
    for e in lang_1:
      oc.add(e)
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
