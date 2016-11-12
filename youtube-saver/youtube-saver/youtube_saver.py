# youtube-dl dependencies
from __future__ import unicode_literals
import youtube_dl

# youtube-saver dependencies
import os

# Create Youtube-Saver settings
youtubeSaverSettings = {
    'plex-drive':   'x',
    'plex-dir':     'youtube/'
}

def GetResDictValue(resDict, key):
    res = resDict

# Create Youtube-DL downloader settings
youtubeDlSettings = {
    # set options critical to expected behavior
    'skip_download': 'true',
    'format': 'best',

    # overwrite any youtube-dl settings that may interfere with expected behavior
    'writeinfojson': 'false',
    'simulate': 'true',
    'quiet': 'true'
}

# Define URLs to use
urls = [
]

existsCount = 0;
newCount = 0

def formatFolderName(str):
    return str.title().replace(' ','')

def printUresDict(uresDict, saveDir, saveName):
    global existsCount
    global newCount

    uploader    = uresDict['uploader'].encode('ascii', 'ignore')
    creator     = formatFolderName(uploader)
    creatorDir  = saveDir + creator + '/'
    fname       = creatorDir + saveName
    fname       = os.path.abspath(fname)
    creatorDir  = os.path.abspath(creatorDir)

    exists = os.path.exists(fname)
    if exists:
        existsCount += 1
    else:
        newCount += 1

    print '{0} [ {1} ]'.format(exists, fname)

def processUrl(ydl, url, dlDir):
    uresDict = ydl.extract_info(url=url, download=False);
    if uresDict.has_key('entries') is False:
        ydl.process_info(uresDict)
        uresDict['ext'] = 'mkv'
        printUresDict(uresDict, dlDir, ydl.prepare_filename(uresDict))
    else:
        for entry in uresDict['entries']:
            ydl.process_info(entry)
            entry['ext'] = 'mkv'
            printUresDict(entry, dlDir, ydl.prepare_filename(entry))

def ProcessUrls(ydlSaverSettings, ydlSettings, urls):
    with youtube_dl.YoutubeDL(ydlSettings) as ydl:
        dlDir = ydlSaverSettings['plex-drive'] + ':' + '/' + formatFolderName(ydlSaverSettings['plex-dir']) + '/'
        for url in urls:
            processUrl(ydl, url, dlDir);

# Main func
ProcessUrls(youtubeSaverSettings, youtubeDlSettings, urls)
print "New vs Exists = {0} vs {1}".format(newCount, existsCount)