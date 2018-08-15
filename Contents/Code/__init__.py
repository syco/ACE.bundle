import urllib

def Start():
  ObjectContainer.title1 = 'ACE'
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'
  HTTP.CacheTime = 0
  HTTP.Timeout = 60

@handler('/video/ace', 'ACE', thumb = 'logo.png', art = 'logo.png')
def MainMenu():
  Log('ZX_COMMAND_START_ACESTREAMENGINE')
  oc = ObjectContainer(title2 = 'ACE')
  json = JSON.ObjectFromURL('http://syco.netsons.org/scrapers/acestream/index.php?action=getProviders')
  for item in json:
    jTitle = item['title'].decode('utf-8')
    jAction = item['action'].decode('utf-8')
    oc.add(
      DirectoryObject(
        key = Callback(ListProvider, title = jTitle, action = jAction),
        title = jTitle
      )
    )
  return oc


@route('/video/ace/listprovider')
def ListProvider(title, action):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(ListProvider, title = title, action = action),
      title = 'Refresh'
    )
  )
  json = JSON.ObjectFromURL('http://syco.netsons.org/scrapers/acestream/index.php?action=' + action)
  for item in json:
    jTitle = item['title'].decode('utf-8')
    jAction = item['action'].decode('utf-8')
    jUrl = item['url'].decode('utf-8')
    oc.add(
      DirectoryObject(
        key = Callback(ListProviderStreams, title = jTitle, action = jAction, url = jUrl),
        title = jTitle
      )
    )
  return oc

@route('/video/ace/listproviderstreams')
def ListProviderStreams(title, action, url):
  oc = ObjectContainer(title2 = title)
  oc.add(
    DirectoryObject(
      key = Callback(ListProviderStreams, title = title, action = action, url = url),
      title = 'Refresh'
    )
  )
  json = JSON.ObjectFromURL('http://syco.netsons.org/scrapers/acestream/index.php?action=' + action + '&url=' + urllib.quote_plus(url))
  for item in json:
    jTitle = item['title'].decode('utf-8')
    jAce = item['ace'].decode('utf-8')
    oc.add(
      Show(
        ace = 'http://10.0.0.250:6878/ace/manifest.m3u8?id=' + jAce,
        title = jTitle
      )
    )
  return oc


@route('/video/ace/show', include_container = bool)
def Show(ace, title, include_container = False, **args):
  vco = VideoClipObject(
    key = Callback(Show, ace = ace, title = title, include_container = True),
    rating_key = ace,
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
            key = HTTPLiveStreamURL(Callback(Play, ace = ace))
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
def Play(ace, **args):
  Log(' --> Final stream ace: %s' % (ace))
  return IndirectResponse(VideoClipObject, key = ace)
