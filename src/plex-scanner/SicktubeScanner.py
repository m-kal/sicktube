#!/usr/bin/env python
from datetime import datetime
import re, os, os.path
import sys
import json

# Manually import Plex libraries
sys.path.append("M:/Plex/Resources/Plug-ins-ee6e505/Scanners.bundle/Contents/Resources/Common")
import Media, VideoFiles, Stack, Utils

__author__ = "MKal"
__copyright__ = "Copyright 2016"
__credits__ = ["MKal"]

__license__ = "GPLv3"
__version__ = "1.0"
__maintainer__ = "MKal"
__email__ = ""

def LogMsg(msg):
  print msg
  #Utils.Log(msg, level=1, source="Sicktube Scanner")

def unicodize(s):
  filename = s
  if os.path.supports_unicode_filenames:
    try: filename = unicode(s.decode('utf-8'))
    except: pass
  return filename


# Look for episodes.
def Scan(path, files, mediaList, subdirs):
  # Scan for video files.
  VideoFiles.Scan(path, files, mediaList, subdirs)
  LogMsg("SicktubeScanner.VideoFiles.Scan({0}, {1}, {2}, {3})".format(path, files, mediaList, subdirs))

  for mediaFile in files:
    (file, ext) = os.path.splitext(mediaFile)
    if ext == 'json':
        continue
    infoJsonFile = file + '.info.json'
    LogMsg("{0} | {1} | {2} | {3}".format(os.path.basename(mediaFile), mediaFile, infoJsonFile, os.path.exists(infoJsonFile)))

    # Create the movie
    (name, ext)  = os.path.splitext(os.path.basename(mediaFile))
    # Is there a .info.json file indicating we've used our scanner?
    if not os.path.exists(infoJsonFile):
        movie = Media.Movie(name)
        movie.parts.append(mediaFile)
    else:
        downloadInfo = json.load(open(infoJsonFile))
        movie = Media.Movie("{0}".format(downloadInfo['title']))
        #movie = Media.Movie(os.path.basename(mediaFile))
        movie.parts.append(mediaFile)
        # Source URL
        if 'webpage_url' in downloadInfo:
            movie.source = "{0}".format(downloadInfo['webpage_url'])
        # Website/Movie ID
        if 'id' in downloadInfo:
            movie.guid = "{0}".format(downloadInfo['id'])
        # Year
        if 'upload_date' in downloadInfo:
            dateObj = datetime.strptime(downloadInfo['upload_date'], '%Y%m%d')
            movie.year = "{0}".format(dateObj.year)
    mediaList.append(movie)
  # Stack the results.
  Stack.Scan(path, files, mediaList, subdirs)


if __name__ == '__main__':
    path = sys.argv[1]
    files = [os.path.join(path, file) for file in os.listdir(path)]
    media = []
    Scan(path[1:], files, media, [])
