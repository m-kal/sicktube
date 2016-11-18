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
  Utils.Log(msg, level=1, source="YoutubeSaver Agent")
  #print msg

def Start():
  pass
  
class PlexPersonalMediaAgentMovies(Agent.Movies):
  name = 'YoutubeSaverAgent'
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
    #metadata.title = media.title

    # Get the filename and the mod time.
    filename = unicodize(media.items[0].parts[0].file)
    mod_time = os.path.getmtime(filename)
    
    date = datetime.date.fromtimestamp(mod_time)
    
    ## Fill in the little we can get from a file.
    try: title = os.path.splitext(os.path.basename(filename))[0]
    except: title = media.title
    ## Is there a .info.json file indicating we've used our scanner?
    (file, ext) = os.path.splitext(filename)
    infoJsonFile = file + '.info.json'
    if os.path.exists(infoJsonFile):
        downloadInfo = json.load(io.open(infoJsonFile))
        metadata.rating = 3.0
        # Summary
        if 'description' in downloadInfo:
            metadata.summary = "{0}".format(downloadInfo['description'])

        if not len(metadata.summary):
            metadata.summary = "Imported from Plex.YoutubeSaverAgent"
        # Title
        if 'title' in downloadInfo:
            metadata.title = "{0}".format(downloadInfo['title'])
        # Website/Movie ID
        #if 'id' in downloadInfo:
        #    metadata.guid = "{0}".format(downloadInfo['id'])
        # Year
        #if 'upload_date' in downloadInfo:
        #    dateObj = datetime.strptime(downloadInfo['upload_date'], '%Y%m%d')
            #metadata.originally_available_at = dateObj
            #metadata.year = datetime.strptime(downloadInfo['upload_date']).year

      
    #metadata.title = 'AgentUrI ' + title
    #metadata.year = date.year
    metadata.originally_available_at = Datetime.ParseDate(str(date)).date()