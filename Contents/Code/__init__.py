import re

def Start():
  ObjectContainer.title1 = 'ACE'
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'
  HTTP.CacheTime = 0

@handler('/video/ace', 'ACE', thumb = 'logo.png', art = 'logo.png')
def MainMenu():
  oc = ObjectContainer(title2 = 'ACE')
  html = HTML.ElementFromURL('https://www.reddit.com/r/soccerstreams/')
  for item in html.xpath('//a[.//*[contains(translate(text(), "ABCDEFGHJIKLMNOPQRSTUVWXYZ", "abcdefghjiklmnopqrstuvwxyz"), " vs")]]'):
    title = item.xpath('./h2/text()')[0]
    href = item.get('href');
    oc.add(
      DirectoryObject(
        key = Callback(List, title = title, url = href),
        title = title
      )
    )
  return oc

@route('/video/ace/list')
def List(title, url):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(List, title = title, url = url),
      title = 'Refresh'
    )
  )
  html = HTTP.Request('https://www.reddit.com{}'.format(url)).content
  pattern = re.compile(r'((?:\[[^\[\]]+\]\s+)*)acestream:\/\/([0-z]{40})((?:\s+\[[^\[\]]+\])*)', re.IGNORECASE)
  for m in re.finditer(pattern, html):
    aceid = m.group(2)
    acedesc = m.group(1) + m.group(3) + '   [ ' + aceid + ' ]'
    if re.search('\[(ar|croatian|es|esp|ger|german|kazakh|pl|portugal|pt|ru|spanish|ukrainian)\]', acedesc, re.IGNORECASE) == None:
      #url = 'http://127.0.0.1:6878/ace/getstream?id={}'.format(aceid),
      url = 'http://127.0.0.1:6878/ace/manifest.m3u8?id={}'.format(aceid),
      oc.add(
        Show(
          url = url,
          title = acedesc
        )
      )
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
