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
  oc.add(
    DirectoryObject(
      key = Callback(PHPScrapersList, title = 'PHP Scrapers', action = 'list', link = ''),
      title = 'PHP Scrapers'
    )
  )
  if (Prefs['show_arenavision']):
    oc.add(
      DirectoryObject(
        key = Callback(ArenavisionList0, title = 'Arenavision'),
        title = 'Arenavision'
      )
    )
  if (Prefs['show_platinsport']):
    oc.add(
      DirectoryObject(
        key = Callback(PlatinsportList0, title = 'Platinsport'),
        title = 'Platinsport'
      )
    )
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
      oc.add(
        DirectoryObject(
          key = Callback(PHPScrapersList, title = phpscraper['title'], action = phpscraper['action'], link = phpscraper['link']),
          title = phpscraper['title']
        )
      )

  return oc


@route('/video/ace/arenavisionlist0')
def ArenavisionList0(title):
  oc = ObjectContainer(title2 = title)
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
        key = Callback(ArenavisionList1, title = title, url = '|'.join(urls)),
        title = title
      )
    )
  return oc

@route('/video/ace/arenavisionlist1')
def ArenavisionList1(title, url):
  oc = ObjectContainer(title2 = title)
  pattern = re.compile(r'acestream:\/\/([0-z]{40})', re.IGNORECASE)
  for r in url.split('|'):
    t = r.split('!')
    html = HTTP.Request(t[1], '', {'Cookie': 'beget=begetok; expires=' + ('{:%a, %d %b %Y %H:%M:%S GMT}'.format(datetime.utcnow() + timedelta(seconds=19360000))) + '; path=/'}).content
    for m in re.finditer(pattern, html):
      aurl = 'http://{}:{}/ace/manifest.m3u8?id={}'.format(Prefs['ace_host'], Prefs['ace_port'], m.group(1))
      Log(aurl)
      oc.add(Show(
        url = aurl,
        title = t[0]
      ))
  return oc



@route('/video/ace/platinsportlist0')
def PlatinsportList0(title):
  oc = ObjectContainer(title2 = title)
  html = HTML.ElementFromURL('http://www.platinsport.com/')
  for item in html.xpath('//article[@class="item-list"]'):
    date = (item.xpath('./h2[@class="post-box-title"]/a/text()')[0])[0:10]
    for row in item.xpath('.//tr'):
      title = "{} {}".format(date, row.xpath('.//td[2]/strong/text()')[0]).decode('UTF-8')
      url = (row.xpath('.//td[3]/a')[0]).get('href').decode('UTF-8')
      oc.add(
        DirectoryObject(
          key = Callback(PlatinsportList1, title = title, url = url[20:]),
          title = title
        )
      )
  return oc

@route('/video/ace/platinsportlist1')
def PlatinsportList1(title, url):
  oc = ObjectContainer(title2 = title.decode('UTF-8'))
  pattern = re.compile(r'acestream:\/\/([0-z]{40})', re.IGNORECASE)
  html = HTTP.Request(url).content
  for m in re.finditer(pattern, html):
    aurl = 'http://{}:{}/ace/manifest.m3u8?id={}'.format(Prefs['ace_host'], Prefs['ace_port'], m.group(1))
    Log(aurl)
    oc.add(Show(
      url = aurl.decode('UTF-8'),
      title = title.decode('UTF-8')
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
