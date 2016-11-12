# youtube-dl dependencies
from __future__ import unicode_literals
import youtube_dl

# youtube-saver dependencies
import os

# temp config data
plexDir = 'x:/plex/'

youtubeDir = plexDir + 'youtube/'
print youtubeDir

def GetResDictValue(resDict, key):
    res = resDict

# Create Youtube-DL downloader settings
youtubeDlSettings = {
    # set options critical to expected behavior
    'skip_download': 'true',
    'format': 'best',
    #'merge_output_format': 'mkv',

    # overwrite any youtube-dl settings that may interfere with expected behavior
    'writeinfojson': 'false',
    'simulate': 'true',
    'quiet': 'true'
}

# Define URLs to use
urls = [
]

def printUresDict(uresDict):
    print uresDict[u'uploader']

    uploader = uresDict[u'uploader'].encode('ascii', 'ignore')
    creator = uploader.replace(' ', '');
    creatorDir = youtubeDir + creator + '/'

    print uploader

    title   = uresDict[u'title'].encode('ascii', 'ignore')
    id      = uresDict[u'id'].encode('ascii', 'ignore')
    ext     = uresDict[u'ext'].encode('ascii', 'ignore')

    ext = 'mkv'
    fname   = creatorDir + title + '-' + id + '.' + ext
    print fname

    print creatorDir
    print os.path.exists(creatorDir)
    print os.path.exists(fname)

def processUrl(ydl, url):
    uresDict = ydl.extract_info(url=url, download='False');

    if uresDict.has_key(u'entries') is False:
        printUresDict(uresDict)
    else:
        for entry in uresDict[u'entries']:
            ydl.process_info(entry)
            printUresDict(entry)

def ProcessUrls(ydlSettings, urls):
    with youtube_dl.YoutubeDL(ydlSettings) as ydl:
        for url in urls:
            processUrl(ydl, url);

# Main func
ProcessUrls(youtubeDlSettings, urls)