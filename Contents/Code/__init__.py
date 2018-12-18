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
  if (Prefs['show_arenavision']):
    oc.add(
      DirectoryObject(
        key = Callback(ArenavisionList, title = 'Arenavision'),
        title = 'Arenavision'
      )
    )
  if (Prefs['show_reddit_boxing']):
    oc.add(
      DirectoryObject(
        key = Callback(RedditNFLList, title = 'Reddit/Boxing'),
        title = 'Reddit/Boxing'
      )
    )
  if (Prefs['show_reddit_nba']):
    oc.add(
      DirectoryObject(
        key = Callback(RedditNBAList, title = 'Reddit/NBA'),
        title = 'Reddit/NBA'
      )
    )
  if (Prefs['show_reddit_nfl']):
    oc.add(
      DirectoryObject(
        key = Callback(RedditNFLList, title = 'Reddit/NFL'),
        title = 'Reddit/NFL'
      )
    )
  if (Prefs['show_reddit_mma']):
    oc.add(
      DirectoryObject(
        key = Callback(RedditMMAList, title = 'Reddit/MMA'),
        title = 'Reddit/MMA'
      )
    )
  if (Prefs['show_reddit_motorsports']):
    oc.add(
      DirectoryObject(
        key = Callback(RedditMotorSportsList, title = 'Reddit/MotorSports'),
        title = 'Reddit/MotorSports'
      )
    )
  if (Prefs['show_reddit_soccer']):
    oc.add(
      DirectoryObject(
        key = Callback(RedditSoccerList, title = 'Reddit/Soccer'),
        title = 'Reddit/Soccer'
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
    av_date = item.xpath('./td[1]/text()')[0].decode('UTF-8')
    if today != av_date and tomorrow !=av_date:
      continue
    av_time = item.xpath('./td[2]/text()')[0].decode('UTF-8')
    av_sport = item.xpath('./td[3]/text()')[0].decode('UTF-8')
    av_tournament = item.xpath('./td[4]/text()')[0].decode('UTF-8')
    av_match = item.xpath('./td[5]/text()')[0].decode('UTF-8')
    av_langs = ''
    urls = []
    for t1 in item.xpath('./td[6]/text()'):
      tokens = t1.split(' ')
      av_langs = av_langs + ' ' + tokens[1]
      for c in tokens[0].split('-'):
        c = c.strip()
        if c[0] == 'W':
          urls.append(tokens[1] + ' ' + c + '!' + (html.xpath('//a[text()="World Cup ' + c[1:] + '"]')[0]).get('href'))
        else:
          urls.append(tokens[1] + ' ' + c + '!' + (html.xpath('//a[text()="ArenaVision ' + c + '"]')[0]).get('href'))
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
    html = HTTP.Request(t[1], '', {'Cookie': 'beget=begetok; expires=' + ('{:%a, %d %b %Y %H:%M:%S GMT}'.format(datetime.utcnow() + timedelta(seconds=19360000))) + '; path=/'}).content
    for m in re.finditer(pattern, html):
      aurl = 'http://{}:{}/ace/manifest.m3u8?id={}'.format(Prefs['ace_host'], Prefs['ace_port'], m.group(1))
      Log(aurl)
      oc.add(
        Show(
          url = aurl,
          title = t[0]
        )
      )
  return oc


def getRedditLinks(oc, url, selector):
  plus = ""
  while True:
    html = HTTP.Request(url + plus).content
    js = json.loads(html)
    for t3 in js["data"]["children"]:
      title = t3["data"]["title"]
      if title.lower().find(selector) != -1:
        title2 = "{}, by {}".format(title, t3["data"]["author"]).decode('UTF-8')
        url2 = t3["data"]["url"].decode('UTF-8')
        oc.add(
          DirectoryObject(
            key = Callback(RedditSubList, title = title2, url = url2),
            title = title2
          )
        )
    after = js["data"]["after"]
    if after is None:
      break
    else:
      plus = "?after=" + after


def findAllData(js, ks):
  arr = []
  if isinstance(js, dict):
    for k in js:
      if k == ks and "body" in js[k]:
        arr.append(js[k])
      arr.extend(findAllData(js[k], ks))
  elif isinstance(js, list):
    for sjs in js:
      arr.extend(findAllData(sjs, ks))
  return arr

@route('/video/ace/redditsublist')
def RedditSubList(title, url):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(RedditSubList, title = title, url = url),
      title = 'Refresh'
    )
  )
  pattern = re.compile(r'((?:\[[^\[\]]+\]\s+)*)acestream:\/\/([0-z]{40})((?:\s+\[[^\[\]]+\])*)', re.IGNORECASE)
  lang_0 = []
  lang_1 = []
  plus = ""
  while True:
    html = HTTP.Request(url[:-1] + ".json" + plus).content
    js = json.loads(html)
    arr = findAllData(js, "data")
    for t3 in arr:
      for m in re.finditer(pattern, t3["body"]):
        aceid = m.group(2)
        acedesc = "{}{} [{}] by {}".format(m.group(1), m.group(3), aceid, t3["author"])
        aurl = 'http://{}:{}/ace/manifest.m3u8?id={}'.format(Prefs['ace_host'], Prefs['ace_port'], aceid)
        Log(aurl)
        if re.search('\[(ar|croatian|es|esp|ger|german|kazakh|pl|portugal|pt|ru|spanish|ukrainian)\]', acedesc, re.IGNORECASE) == None:
          lang_1.append(
            Show(
              url = aurl,
              title = acedesc.decode('UTF-8')
            )
          )
        else:
          lang_0.append(
            Show(
              url = aurl,
              title = acedesc.decode('UTF-8')
            )
          )
    after = js[0]["data"]["after"]
    if after is None:
      break
    else:
      plus = "?after=" + after
  for e in lang_0:
    oc.add(e)
  for e in lang_1:
    oc.add(e)
  return oc


@route('/video/ace/redditboxinglist')
def RedditBoxingList(title):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(RedditBoxingList, title = title),
      title = 'Refresh'
    )
  )
  getRedditLinks(oc, 'https://www.reddit.com/r/boxingstreams.json', ' vs')
  return oc

@route('/video/ace/redditnbalist')
def RedditNBAList(title):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(RedditNBAList, title = title),
      title = 'Refresh'
    )
  )
  getRedditLinks(oc, 'https://www.reddit.com/r/nbastreams.json', ' @')
  return oc

@route('/video/ace/redditnfllist')
def RedditNFLList(title):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(RedditNFLList, title = title),
      title = 'Refresh'
    )
  )
  getRedditLinks(oc, 'https://www.reddit.com/r/nflstreams.json', ' @')
  return oc

@route('/video/ace/redditmmalist')
def RedditMMAList(title):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(RedditMMAList, title = title),
      title = 'Refresh'
    )
  )
  getRedditLinks(oc, 'https://www.reddit.com/r/MMAStreams.json', ' vs')
  return oc

@route('/video/ace/redditmotorsportslist')
def RedditMotorSportsList(title):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(RedditMotorSportsList, title = title),
      title = 'Refresh'
    )
  )
  getRedditLinks(oc, 'https://www.reddit.com/r/motorsportsstreams.json', ' utc')
  return oc

@route('/video/ace/redditsoccerlist')
def RedditSoccerList(title):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(RedditSoccerList, title = title),
      title = 'Refresh'
    )
  )
  getRedditLinks(oc, 'https://www.reddit.com/r/soccerstreams.json', ' vs')
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
