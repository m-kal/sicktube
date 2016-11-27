# youtube-dl dependencies
#from __future__ import unicode_literals
#import youtube_dl
import json
import re, os, io
import sys

# Manually import Plex libraries
sys.path.append("M:/Plex/Resources/Plug-ins-ee6e505/Scanners.bundle/Contents/Resources/Common")
import Media, VideoFiles, Stack, Utils
import datetime, time

# Only use unicode if it's supported, which it is on Windows and OS X,
# but not Linux. This allows things to work with non-ASCII characters
# without having to go through a bunch of work to ensure the Linux
# filesystem is UTF-8 "clean".
#
def unicodize(s):
  filename = s
  if os.path.supports_unicode_filenames:
    try: filename = unicode(s.decode('utf-8'))
    except: pass
  return filename

def LogMsg(msg):
  Utils.Log(msg, level=1, source="Sicktube Agent")

def Start():
  pass

class SicktubeAgentMovies(Agent.Movies):
  name = 'Sicktube Agent'
  languages = Locale.Language.All()
  primary_provider = True
  accepts_from = ['com.plexapp.agents.localmedia']

  def search(self, results, media, lang):
    LogMsg("search: {0} {1}".format(media.name, media.id))
    # Compute the GUID based on the media hash.
    part = media.items[0].parts[0]

    # Get the modification time to use as the year.
    filename = unicodize(part.file)
    mod_time = os.path.getmtime(filename)

    results.Append(MetadataSearchResult(id=part.hash, name=media.name, year=time.localtime(mod_time)[0], lang=lang, score=100))

  def update(self, metadata, media, lang, force=False):
    LogMsg("update: {0} {1} {2} {3}".format(metadata, media, lang, force))

    # Get the filename and the mod time.
    filename = unicodize(media.items[0].parts[0].file)
    mod_time = os.path.getmtime(filename)

    date = datetime.date.fromtimestamp(mod_time)

    ## Fill in the little we can get from a file.
    try: title = os.path.splitext(os.path.basename(filename))[0]
    except: title = media.title
    ## Is there a .info.json file indicating we've used our scanner?

    fDir = os.path.split(filename)[0]
    fName = os.path.basename(filename)
    (baseFileName, ext) = os.path.splitext(fName)
    metadataDir = os.path.join(fDir, '.metadata')
    LogMsg("metadataDir: {0}".format(metadataDir))

    if os.path.exists(metadataDir):
        fDir = metadataDir

    infoJsonFile = os.path.join(fDir, baseFileName + '.info.json')

    metadata.title = "{0}".format(title)
    if os.path.exists(infoJsonFile):
        downloadInfo = json.load(io.open(infoJsonFile))
        # Ratings are based out of 10 but usually average_rating is out of 5
        if 'average_rating' in downloadInfo:
            metadata.rating = 2*float(downloadInfo['average_rating'])
        else:
            metadata.rating = 5.0
        # Summary
        if 'description' in downloadInfo:
            metadata.summary = "{0}".format(downloadInfo['description'])

        if not len(metadata.summary):
            metadata.summary = "Imported from Plex.Sicktube"
        # Title
        if 'title' in downloadInfo:
            metadata.title = "{0}".format(downloadInfo['title'])

        # Studio is the uploader
        if 'uploader' in downloadInfo:
            metadata.studio = downloadInfo['uploader'].strip()

        # Genres
        if 'categories' in downloadInfo:
            # Genres from categories
            metadata.genres.clear()
            for cat in downloadInfo['categories']:
                metadata.genres.add(cat.strip())

        # Taglines
        if 'playlist_title' in downloadInfo:
            metadata.tagline = downloadInfo['playlist_title'].strip()

        # Genres from folder detection
        if 'uploader' in downloadInfo:
            videoOutputDir = os.path.split(filename)[0]
            if os.path.basename(videoOutputDir).lower() == downloadInfo['uploader'].strip().lower():
                section = os.path.basename(os.path.abspath(videoOutputDir + "/../"))
                pass
            else:
                section = os.path.basename(videoOutputDir)
            metadata.genres.add(section)

    metadata.originally_available_at = Datetime.ParseDate(str(date)).date()
