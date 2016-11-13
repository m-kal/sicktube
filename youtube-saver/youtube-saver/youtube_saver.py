# youtube-dl dependencies
from __future__ import unicode_literals
import youtube_dl

# youtube-saver dependencies
import os
import ConfigParser

# Consts
INI_FILE_SETTINGS_FILENAME = 'settings.cfg'
INI_FILE_SETTINGS_SECTION  = 'ytsave-settings'
INI_FILE_SETTINGS_URLS_OPT = 'urls'

# Create Youtube-Saver settings
SAVER_SETTINGS = {
    'plex-drive':   'x',
    'output-template': youtube_dl.DEFAULT_OUTTMPL,
    'prefix-extractor-dir': False,
}

# Create Youtube-DL downloader settings
YOUTUBEDL_SETTINGS = {
    # set options critical to expected behavior
    'format':           'bestvideo+bestaudio',  # Caching assumes we want best quality to transcode later
    'skip_download':    True,                   # Skips downloading the video file but will download the .info.json file
    'simulate':         True,                   # Skips downloading the video and the .info.json file

    # overwrite any youtube-dl settings that may interfere with expected behavior
    'writeinfojson':    False,                  # Don't write out the info.json file
    'quiet':            True,                   # Don't spam the console with debug info
    'ffmpeg_location':  'c:/ffmpeg/bin'         # Location of FFMPEG
}

class YoutubeSaver:
    def __init__(self):
        sectionUrlDict = {}
        youtubeDl = None
        ytdlSettings = {}
        settings = {}
        runStats = { 'new': 0, 'old': 0 }

    @staticmethod
    def FromConfigFile(filename=INI_FILE_SETTINGS_FILENAME, settings=SAVER_SETTINGS, ytdlSettings=YOUTUBEDL_SETTINGS):
        if not os.path.exists(filename):
            print '{0} does not exist.'.format(filename)
            return None

        ytsv = YoutubeSaver()
        ytsv.SetSettings(settings)
        ytsv.SetYoutubeDlSettings(ytdlSettings)
        ytsv.ParseConfig(filename)

        return ytsv

    def SetSettings(self, settings):
        self.settings = settings

    def SetYoutubeDlSettings(self, ytdlSettings):
        self.ytdlSettings = ytdlSettings
        self.youtubeDl = youtube_dl.YoutubeDL(self.ytdlSettings)

    def ParseConfig(self, filename=INI_FILE_SETTINGS_FILENAME):
        self.sectionUrlDict = {}
        config = ConfigParser.SafeConfigParser(self.settings, allow_no_value=True)
        config.read(filename)
        for section in config.sections():
            if section == INI_FILE_SETTINGS_SECTION:
                continue

            if config.has_option(section, INI_FILE_SETTINGS_URLS_OPT):
                urlList = [s.strip() for s in config.get(section, INI_FILE_SETTINGS_URLS_OPT).splitlines()]
                self.sectionUrlDict[section] = urlList

        return self.sectionUrlDict

    def DetermineOutputDir(self, section):
        return '{0}:/{1}/{2}%(uploader)s/'.format(self.settings['plex-drive'], section, ('%(extractor_key)s/' if 'prefix-extractor-dir' in self.settings and self.settings['prefix-extractor-dir'] else ''))

    def GetFullOutputTemplate(self, section):
        return '{0}{1}'.format(self.DetermineOutputDir(section), self.settings['output-template'])

    def GetFullArchiveFilePath(self, section):
        return '{0}:/{1}/{2}'.format(self.settings['plex-drive'], section, 'archive.txt')

    def TouchArchiveFile(self, path):
        basedir = os.path.dirname(path)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        if not os.path.exists(path):
            with open(path, 'a'):
                os.utime(path, None)

    def ProcessUrls(self, section, urls, download=False):
        runSettings = self.ytdlSettings
        runSettings['outtmpl'] = self.GetFullOutputTemplate(section)
        runSettings['download_archive'] = self.GetFullArchiveFilePath(section)
        print runSettings['outtmpl']
        self.TouchArchiveFile(runSettings['download_archive'])
        if download:
            runSettings['skip_download'] = False
            runSettings['simulate'] = False
        self.SetYoutubeDlSettings(runSettings)
        for url in urls:
            self.ProcessUrl(url)

    def ProcessUrl(self, url):
        resDict = self.youtubeDl.extract_info(url=url, download=False)
        if 'entries' not in resDict:
            self.youtubeDl.process_info(resDict)
            self.printUresDict(self.youtubeDl.prepare_filename(resDict))
        else:
            for entry in resDict['entries']:
                self.youtubeDl.process_info(entry)
                self.printUresDict(self.youtubeDl.prepare_filename(entry))

    def printUresDict(self, saveName):
        exists = os.path.exists(saveName)
        if exists:
            self.runStats['old'] += 1
        else:
            self.runStats['new'] += 1

        print '[{0} | {1} v {2}] {3}'.format(exists, self.runStats['new'], self.runStats['old'], saveName)

    def DryRun(self):
        self.runStats = { 'new': 0, 'old': 0 }
        for section in self.sectionUrlDict:
            urls = self.sectionUrlDict[section]
            self.ProcessUrls(section, urls, download=False)

    def Download(self):
        self.runStats = { 'new': 0, 'old': 0 }
        for section in self.sectionUrlDict:
            urls = self.sectionUrlDict[section]
            self.ProcessUrls(section, urls, download=True)

    def DumpUrls(self):
        for section in self.sectionUrlDict:
            urls = self.sectionUrlDict[section]
            print '[{0}] = {1}'.format(section, urls)

YoutubeSaver.FromConfigFile().Download()
