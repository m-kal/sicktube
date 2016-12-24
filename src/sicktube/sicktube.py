# youtube-dl dependencies
from __future__ import unicode_literals
import youtube_dl

# sicktube dependencies
import sys
import os
import ConfigParser
import argparse
import json
import shutil
import time
import datetime
from pprint import pprint

import smtplib
from email.mime.text import MIMEText
import sicktube
import settings
from playlister import Playlister
from plexdb import PlexDB
'''
TODO:
* [x] Add missing youtube metadata
* [x] Add metadata test function
* [x] Add url-to-metadata static method to get metadata from `webpage_url`
* [x] Add config dump cli method
* [~] Video file rename changes may cause issue looking up `.info.json` files *// can make this a hard-no*
* [ ] Instantiate a video-saver at PlexAgent initialization/Start() *// needed for per-section settings*
* [x] Configure a` .metadata-cache` folder and setting?
* [x] Configure an archives file? *// maybe have [...]/.metadata-cache/archive.log*
* [x] Enable email
* [x] Ensure email gets config param and loads settings for email addrs and ports
* [x] Create a default prefs
* [x] Load a default prefs
* [ ] Import playlists into Plex, add a playlists.import configure var
'''

# Consts
INI_FILE_SETTINGS_FILENAME = 'settings.cfg'
INI_FILE_SETTINGS_SECTION  = '_global'
INI_FILE_SETTINGS_URLS_OPT = 'urls'
INI_SETTINGS_URLS_OPT = '_' + INI_FILE_SETTINGS_URLS_OPT

# Create Youtube-DL downloader settings
YOUTUBEDL_SETTINGS = {
    # set options critical to expected behavior
    'format':           'bestvideo+bestaudio',  # Caching assumes we want best quality to transcode later
    'skip_download':    True,                   # Skips downloading the video file but will download the .info.json file
    'simulate':         True,                   # Skips downloading the video and the .info.json file

    # overwrite any youtube-dl settings that may interfere with expected behavior
    'writeinfojson':    True,                   # Write out the info.json file for the metadata archive
    'quiet':            False,                  # Don't spam the console with debug info
    'ffmpeg_location':  'c:/ffmpeg/bin',        # Location of FFMPEG
    'ignoreerrors':     True
}

commands = {
    'config': 'Dumps/prints the configuration file',
    'email': 'Email yourself a test message to check if the email options are configured correctly',
    'metadata': 'Dumps/prints metadata for a url, useful for testing',
    'playlists': 'Dumps the playlists found in .metadata files',
    'run': 'Process urls from configuration files'
}
# program consts
PROG_NAME = 'Sicktube'

class Sicktube:
    """
    Management and execution for browsing the internet
    in a similar manner to existing browsing history
    """
    SETTING_KEYS = settings.Setting.Keys()
    youtubeDl = None
    ytdlSettings = {}
    settings = {}
    runStats = { 'new': 0, 'old': 0 }
    # program consts
    PROG_NAME = 'Sicktube'

    def __init__(self):
        self.settings = settings.Setting().ConvergedDefaults()
        self.settings['consoletitle'] = True

    # Static methods
    @staticmethod
    def FromConfigFile(filename=INI_FILE_SETTINGS_FILENAME, ytdlSettings=YOUTUBEDL_SETTINGS):
        if not os.path.exists(filename):
            print('{0} does not exist.'.format(filename))
            return None

        ytsv = Sicktube()
        ytsv.SetSettings(ytsv.ParseConfigFile(filename))
        ytsv.SetYoutubeDlSettings(ytdlSettings) # TODO: fix

        return ytsv

    def GetSettingSectionOptions(self, section=None):
        return self.GetSectionOptions(self.settings, section)

    @staticmethod
    def GetSectionOptions(optionsDict, section=None):
        sectionOptions = {}
        # Default to global section if no section specified
        if section is None:
            section = INI_FILE_SETTINGS_SECTION

        if section not in optionsDict:
            return sectionOptions

        # Merge global if needed
        if INI_FILE_SETTINGS_SECTION in optionsDict:
            sectionOptions = optionsDict[INI_FILE_SETTINGS_SECTION].copy()

        # Now merge the section options
        for sectionOption in optionsDict[section]:
            sectionOptions[sectionOption] = optionsDict[section][sectionOption]

        # Return merged result
        return sectionOptions

    @staticmethod
    def MetadataFromUrl(url):
        # Force needed settings
        metadataYtdlOpts = YOUTUBEDL_SETTINGS.copy()
        metadataYtdlOpts.update({
            'quite': True,
            'writeinfojson': False,
            'consoletitle': True
        })
        # This changes the metadata formats returned in a best-effort to find any video
        # regardless of the video format. This is to increase the chance a video can be
        # found and thus retrieve its metadata.
        metadataYtdlOpts['format'] = 'best'

        # Construct the ytdl object and get the metadata
        try:
            ytdl = youtube_dl.YoutubeDL(metadataYtdlOpts)
            metadataDict = ytdl.extract_info(url, download=False)
            # Return the youtube-dl instance we used to obtain the data, since this is a static method
            return (metadataDict, ytdl)
        except:
            return None

    @staticmethod
    def ResolveTemplateWithDict(template, dictionary):
        # Todo: make efficient
        workDict = dictionary.copy()
        keyCount = len(workDict.keys())
        attempts = 0
        templateFailures = 0
        while True:
            # Try to resolve the template
            try:
                attempts += 1
                candidate = template % workDict
                # Return an empty string if we failed to match anything
                # Note: This section is suspect because of dubious logic.
                # Note: There should be a way to substitute for string templates
                # Note: and detect if nothing was matched, but that hasn't been found yet,
                # Note: so in the interest of time, leave this for now until it causes an issue,
                # Note: then add to unit tests and refactor this code to do it properly.
                if (templateFailures > keyCount and templateFailures < attempts and (attempts > (keyCount + templateFailures))):
                    return ''
                else:
                    return candidate
            except KeyError, e:
                # On failures use a empty string placeholder
                workDict[e.message] = ''
                templateFailures += 1

    # Object methods
    def SetSettings(self, settings):
        self.settings = settings.copy()

    def SetYoutubeDlSettings(self, ytdlSettings):
        self.ytdlSettings = ytdlSettings.copy()
        self.youtubeDl = youtube_dl.YoutubeDL(self.ytdlSettings)

    def ParseConfigFile(self, filename=INI_FILE_SETTINGS_FILENAME):
        '''Parses a configuration file and returns a merged set of options on a per-section basis'''

        # The dictionary structure is { INI_FILE_SETTINGS_SECTION: [], '<section>': [] }
        globalOptions = settings.Setting.ConvergedDefaults()
        globalOptions.update(YOUTUBEDL_SETTINGS)

        # Use a RawConfigParser to disable option name interpolation
        # so as not to conflict with templating strings for Youtube-DL
        config = ConfigParser.RawConfigParser(globalOptions, allow_no_value=True)
        config.read(filename)

        # hacky for now
        int_keys = [
            self.SETTING_KEYS.SYS_REPEAT_DELAY,
            self.SETTING_KEYS.EMAIL_PORT
        ]
        boolean_keys = [
            self.SETTING_KEYS.SYS_REPEAT_ENABLE,
            self.SETTING_KEYS.DIR_VIDEO_AUTHOR,
            self.SETTING_KEYS.DIR_METADATA_CACHE_ENABLE,
            self.SETTING_KEYS.FILE_ARCHIVE_GLOBAL,
            self.SETTING_KEYS.EMAIL_ENABLE,
            self.SETTING_KEYS.PLAYLISTS_IMPORT
        ]

        # Process the global options from the config
        overWriteGlobalOpts = {}
        if config.has_section(INI_FILE_SETTINGS_SECTION):
            for section in config.sections():
                if section == INI_FILE_SETTINGS_SECTION:
                    for option in config.options(section):
                        # Force the correct type of data
                        overWriteGlobalOpts[option] = config.get(section, option)
                        # Force the correct type of data
                        if option in int_keys:
                            overWriteGlobalOpts[option] = int(overWriteGlobalOpts[option])
                        elif option in boolean_keys:
                            overWriteGlobalOpts[option] = bool(overWriteGlobalOpts[option])

        for key in overWriteGlobalOpts:
            globalOptions[key] = overWriteGlobalOpts[key]

        # Now piggy-back off ConfigParser allowing defaults,
        # so pass the global options as defaults for each section.
        config = ConfigParser.RawConfigParser(globalOptions, allow_no_value=True)
        config.read(filename)
        parsedOptions = { INI_FILE_SETTINGS_SECTION: globalOptions }

        for section in config.sections():
            # Do not generation per-section config options for the global optitons,
            # Instead update the global options, which was already done
            if section == INI_FILE_SETTINGS_SECTION:
                continue

            sectionOptions = { INI_SETTINGS_URLS_OPT: [] }
            for option in config.options(section):
                optionVal = config.get(section, option)
                # Force the correct type of data
                if option in int_keys:
                    optionVal = int(optionVal)
                elif option in boolean_keys:
                    optionVal = bool(optionVal)

                if option == INI_FILE_SETTINGS_URLS_OPT:
                    urlList = [s.strip() for s in optionVal.splitlines() if not s.startswith('#') and not s.startswith(';')]
                    sectionOptions[INI_SETTINGS_URLS_OPT] = urlList
                else:
                    sectionOptions[option] = optionVal
            parsedOptions[section] = sectionOptions

        return parsedOptions

    def DetermineOutputDir(self, section):
        settings = self.GetSettingSectionOptions(section)
        if settings[self.SETTING_KEYS.DIR_VIDEO_AUTHOR]:
            return '{0}/{1}/%(uploader)s/'.format(settings[self.SETTING_KEYS.DIR_ROOT], section)
        return '{0}/{1}/'.format(settings[self.SETTING_KEYS.DIR_ROOT], section)

    def GetFullOutputTemplate(self, section):
        settings = self.GetSettingSectionOptions(section)
        return '{0}{1}'.format(self.DetermineOutputDir(section), settings[self.SETTING_KEYS.FILE_TEMPLATE_NAME])

    def GetFullArchiveFilePath(self, section):
        settings = self.GetSettingSectionOptions(section)

        fullPath = settings[self.SETTING_KEYS.DIR_ROOT]
        if not settings[self.SETTING_KEYS.FILE_ARCHIVE_GLOBAL]:
            fullPath = '{0}/{1}'.format(fullPath, section)
        return '{0}/{1}'.format(fullPath, settings[self.SETTING_KEYS.FILE_ARCHIVE_NAME])

    @staticmethod
    def TouchArchiveFile(path):
        """
        Updates the modification time of the archive.log file, and creates path if none exists yet.

        :param path: Path of destination archive.log file
        :return: None
        """
        basedir = os.path.dirname(path)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        if not os.path.exists(path):
            with open(path, 'a'):
                os.utime(path, None)

    def ProcessUrls(self, section, urls, download=False):
        runSettings = self.GetSettingSectionOptions(section)
        runSettings.update({
            'outtmpl': self.GetFullOutputTemplate(section),
            'download_archive': self.GetFullArchiveFilePath(section),
            'consoletitle': True
        })
        if runSettings['dir.metadata.cache-enable']:
            runSettings['writeinfojson'] = True

        if len(urls):
            # Ensure archive file is present, but only if there are URLs to download
            Sicktube.TouchArchiveFile(runSettings['download_archive'])

        if download:
            runSettings['skip_download'] = False
            runSettings['simulate'] = False

        self.SetYoutubeDlSettings(runSettings)
        for url in urls:
            self.ProcessUrl(url, section)

    def ProcessUrl(self, url, section):
        resDict = self.youtubeDl.extract_info(url=url, download=False)
        if not resDict:
            print("Cannot extract info from URL: {0}".format(url))
            return
        if 'entries' not in resDict:
            self.youtubeDl.process_info(resDict)
            self.printUresDict(self.youtubeDl.prepare_filename(resDict))
            self.CleanupPostProcessUrl(resDict, section)
        else:
            for entry in [e for e in resDict['entries'] if e is not None]:
                self.youtubeDl.process_info(entry)
                self.printUresDict(self.youtubeDl.prepare_filename(entry))
                self.CleanupPostProcessUrl(entry, section)

    def CleanupPostProcessUrl(self, resDict, section):
        # Move any metadata files if needed to subdirs
        settings = self.GetSettingSectionOptions(section)
        # If there is a metadata dir to move .info.json files to, do that now
        if settings[self.SETTING_KEYS.DIR_METADATA_NAME] is None or not len(settings[self.SETTING_KEYS.DIR_METADATA_NAME]):
            return

        # Get the base path and append metadata dir name
        if ('_filename' in resDict) and (len(resDict['_filename'])):
            fileFullPath = resDict['_filename']
        else:
            # If there is no _filename but there is an id, then it's likely the download was skipped
            # and the original metadata was returned, so we can attempt to use a resolved filename in the current dir
            # BUG && TODO
            # File was probably already downloaded and we're getting the extracted info
            # from a alive query for the URL, so in the future we can,
            #
            # 1. [bad] intelligently guess browser area and guess the filename with resolved filename
            # 2. [ok] only do a clean-up per section and walk dirs for 'dir.metadata.name' and '.info.json'
            #
            # Regardless, the root cause is that the ie_info dict (info.json) is written before the manual
            # modifications to the dict get updated with MKV extension and filename updating. Updating the info.json
            # means Sicktube will rely on modified info.jsons rather than
            print("BUG && TODO")
            outputDir = self.ResolveTemplateWithDict(self.DetermineOutputDir(section), resDict)
            bestGuessFilename = self.ResolveTemplateWithDict(settings[self.SETTING_KEYS.FILE_TEMPLATE_NAME], resDict)
            fileFullPath = os.path.join(outputDir, bestGuessFilename)

        # Determine file dir, then the metadata dir
        fileDir = os.path.dirname(fileFullPath)
        fileName = os.path.basename(fileFullPath)
        infoJsonFile = os.path.splitext(fileName)[0] + '.info.json'

        # Determine source and destination .info.json files
        src = os.path.join(fileDir, infoJsonFile)
        metadataDir = os.path.join(fileDir, settings[self.SETTING_KEYS.DIR_METADATA_NAME])
        dst = os.path.join(metadataDir, infoJsonFile)

        # Can't move a metadata file that doesn't exist
        if not os.path.exists(src):
            if os.path.exists(dst):
                # Nothing to do, file already moved appropriately
                return
            print("Can't find {0}".format(src))
            return

        if not os.path.exists(metadataDir):
            print('Creating metadatadir: {0}'.format(metadataDir))
            try:
                os.makedirs(metadataDir)
            except OSError, err:
                print("OSError")
                pprint(err)
                pass

        # Metadata dir exists and the info json file is known, attempt Move
        # print 'Moving info.json: [{0}]{1} -> [{2}]{3}'.format(os.path.exists(src), src, os.path.exists(dst), dst)
        shutil.move(src, dst)

    def printUresDict(self, saveName):
        # May need to change ext in info json, or rather add _ext
        exists = os.path.exists(saveName)
        existsBackup = os.path.exists(saveName.replace('.mkv', '.mp4'))
        if exists or existsBackup:
            self.runStats['old'] += 1
        else:
            self.runStats['new'] += 1

        print('[{0} | {1} v {2}] {3}'.format(exists, self.runStats['new'], self.runStats['old'], saveName.encode('ascii', 'ignore')))

    def DryRun(self):
        self.runStats = { 'new': 0, 'old': 0 }
        for section in self.settings:
            settings = self.GetSettingSectionOptions(section)
            if (section is INI_FILE_SETTINGS_SECTION) or (INI_SETTINGS_URLS_OPT not in settings):
                continue
            urls = settings[INI_SETTINGS_URLS_OPT]
            self.ProcessUrls(section, urls, download=False)

    def Download(self, whitelistedSections=[]):
        self.runStats = { 'new': 0, 'old': 0 }
        for section in self.settings:
            # print self.settings[section]
            settings = self.GetSettingSectionOptions(section)
            # print settings
            if (section is INI_FILE_SETTINGS_SECTION) or (INI_SETTINGS_URLS_OPT not in settings):
                continue

            if (len(whitelistedSections)) and (section.strip().lower() not in whitelistedSections):
                continue

            urls = settings[INI_SETTINGS_URLS_OPT]
            self.ProcessUrls(section, urls, download=True)

    def DumpUrls(self):
        for section in self.settings:
            settings = self.GetSettingSectionOptions(section)
            if (section is INI_FILE_SETTINGS_SECTION) or (INI_SETTINGS_URLS_OPT not in settings):
                continue
            urls = settings[INI_SETTINGS_URLS_OPT]
            print('[{0}] = {1}'.format(section, urls))

    def find_metadata_files(self):
        # Recurse through each directory looking for .metadata dirs
        # For each dir.root in the config
        metadata_dirs = []
        section_playlists = {}
        dir_root = self.settings[INI_FILE_SETTINGS_SECTION][self.SETTING_KEYS.DIR_ROOT]
        for section in self.settings:
            settings = self.GetSettingSectionOptions(section)
            if (section is INI_FILE_SETTINGS_SECTION) or (INI_SETTINGS_URLS_OPT not in settings):
                continue

            if not settings[self.SETTING_KEYS.DIR_METADATA_CACHE_ENABLE]:
                continue

            if not settings[self.SETTING_KEYS.PLAYLISTS_IMPORT]:
                continue

            # Ensure this section is marked for playlist import
            section_playlists[section] = True

            dir_root = settings[self.SETTING_KEYS.DIR_ROOT]
            metadata_dir_name = settings[self.SETTING_KEYS.DIR_METADATA_NAME]
            # Look for a metadata dir starting from the dir root
            for root, dirs, files in os.walk(dir_root):
                for dir in dirs:
                    metadata_dir_path = os.path.join(root, dir, metadata_dir_name)
                    if os.path.exists(metadata_dir_path):
                        metadata_dirs.append(metadata_dir_path)

        # Uniquify the existing metadata dirs and sort them alphabetically
        unique_dirs = list(set(metadata_dirs))
        unique_dirs.sort()

        metadata_files = []
        for metadata_dir in unique_dirs:
            # Process each .info.json file
            for root, dirs, files in os.walk(metadata_dir):
                # Only process sections that are marked
                playlist_section = None
                for section in self.settings:
                    section_path = os.path.join(dir_root, section)
                    if metadata_dir.startswith(section_path):
                        playlist_section = section

                if playlist_section not in section_playlists:
                    continue

                for file in files:
                    if file.endswith(".info.json"):
                        file_path = os.path.join(root, file)
                        metadata_files.append(file_path)

        return metadata_files

    def process_metadata_files(self, files=[], callback=None):
        pass


# First-Order CLI commands
def run(st):
    parser = argparse.ArgumentParser(description=commands['run'], formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--repeat', action='store_true', help='Location of the settings configuration file')
    parser.add_argument('--delay', action='store', help='Delay (in seconds) between repeating configuration processing/downloading')
    parser.add_argument('--dry', action='store_true', help='Dry run, do not download anything')
    parser.add_argument('--config', action='store', help='Location of the settings configuration file')
    parser.add_argument('--sections', nargs='+', action='store', help='List of sections to process')
    args = parser.parse_args(sys.argv[2:])


    whitelistedSections = []
    if args.sections is not None:
        for section in args.sections:
            whitelistedSections.append(section.strip().lower())

    while True:
        # Parse the correct file
        if args.config is not None:
            configs = st.ParseConfigFile(filename=args.config)
        else:
            configs = st.ParseConfigFile()

        if args.repeat:
            configs[INI_FILE_SETTINGS_SECTION][Sicktube.SETTING_KEYS.SYS_REPEAT_ENABLE] = args.repeat
            if args.delay is not None:
                configs[INI_FILE_SETTINGS_SECTION][Sicktube.SETTING_KEYS.SYS_REPEAT_DELAY] = float(args.delay)

        # Set everything up
        st.SetSettings(configs)
        st.SetYoutubeDlSettings(YOUTUBEDL_SETTINGS)

        # Do the processing and downloads
        st.Download(whitelistedSections)

        # If repeat is not enabled, end now
        if not st.GetSettingSectionOptions()[Sicktube.SETTING_KEYS.SYS_REPEAT_ENABLE]:
            return

        # Repeat not enabled, so wait for the appropriate duration
        repeatDelay = st.GetSettingSectionOptions()[Sicktube.SETTING_KEYS.SYS_REPEAT_DELAY]
        print("Waiting {0} seconds before next iteration".format(repeatDelay))
        time.sleep(repeatDelay)

def config(st):
    parser = argparse.ArgumentParser(description=commands['config'], formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--config', action='store', help='Location of the settings configuration file')
    parser.add_argument('--raw', action='store_true', help='Dump the parsed config file in an unstructured manner')
    parser.add_argument('--sections', nargs='+', action='store', help='List of sections to process')
    args = parser.parse_args(sys.argv[2:])

    # Parse the correct file
    if args.config is not None:
        configs = st.ParseConfigFile(filename=args.config)
    else:
        configs = st.ParseConfigFile()

    st.SetSettings(configs)

    # Pretty print each config
    if args.raw:
        for k in configs:
            print('\nSection Config For: {0}\n'.format(k))
            pprint(st.GetSectionOptions(configs, k))
        return

    whitelistedSections = []
    if args.sections is not None:
        for section in args.sections:
            whitelistedSections.append(section.strip().lower())

    now = datetime.datetime.now()
    for section in configs:
        if (len(whitelistedSections)) and (section.strip().lower() not in whitelistedSections):
            continue
        print("\n[{0}]\n".format(section) + "{")
        sectOpt = st.GetSectionOptions(configs, section)
        globOpt = st.GetSectionOptions(configs)
        keys=list(sectOpt.keys())
        keys.sort()
        for k in keys:
            value = sectOpt[k]
            modified = (k in globOpt and globOpt[k] == sectOpt[k])
            if k == settings.Setting.Keys().FILE_ARCHIVE_NAME:
                archive_path = st.GetFullArchiveFilePath(section)
                if os.path.exists(archive_path):
                    mod_time = os.path.getmtime(archive_path)
                    dtm = datetime.datetime.fromtimestamp(mod_time)
                    print(now - dtm)

            if modified:
                print("  {0: <30} : {1}".format(k, value))
            else:
                print("  {0: <30}*: {1}".format(k, value))
        print("}")

def email(st):
    parser = argparse.ArgumentParser(description=commands['email'], formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--config', action='store', help='Location of the settings configuration file')
    parser.add_argument('--from-addr', action='store', help='Test sender\'s email address', default='admin@localhost')
    parser.add_argument('--to-addr', action='store', help='Test recipient\'s email address', default='admin@localhost')
    parser.add_argument('--msg', action='store', help='Test email message', default='This is a test message sent for {0}'.format(st.PROG_NAME))
    parser.add_argument('--subject', action='store', help='Test email message subject', default='[{0}] Test configuration email'.format(st.PROG_NAME))
    args = parser.parse_args(sys.argv[2:])

    # Parse the correct file
    if args.config is not None:
        configs = st.ParseConfigFile(filename=args.config)
    else:
        configs = st.ParseConfigFile()

    msg = MIMEText(args.msg)
    msg['Subject'] = args.subject
    s = smtplib.SMTP(configs[INI_FILE_SETTINGS_SECTION][Sicktube.SETTING_KEYS.EMAIL_SERVER],
                     configs[INI_FILE_SETTINGS_SECTION][Sicktube.SETTING_KEYS.EMAIL_PORT])
    msg['From'] = args.from_addr
    msg['To'] = args.to_addr
    s.sendmail(msg['From'], msg['To'], msg.as_string())
    s.quit()
    print('Email message sent from `{0}` to `{1}` with a subject of `{2}`'.format(args.from_addr, args.to_addr,
                                                                                  args.subject))
    print('Email Feature Status: {0}'.format(
        'Enabled' if configs[INI_FILE_SETTINGS_SECTION][Sicktube.SETTING_KEYS.EMAIL_ENABLE] else 'Disabled'))

def metadata(st):
    parser = argparse.ArgumentParser(description=commands['metadata'], formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('url', action='store', help='URL to extract metadata for')
    parser.add_argument('--save-as', action='store', help='Save the metadata to a file rather than printing to stdout')
    parser.add_argument('--config', action='store', help='Location of the settings configuration file')
    args = parser.parse_args(sys.argv[2:])

    (metadataDict, ytld) = st.MetadataFromUrl(args.url)
    if args.save_as is None:
        # Print to screen because no save file was set
        pprint(metadataDict)
    else:
        absPath = os.path.abspath(args.save_as)
        if not os.path.exists(absPath):
            print('{0} doesnt exist yet'.format(absPath))

        # Dump the dict to file through the json lib rather than a print-style dump
        f = open(absPath, 'w')
        json.dump(metadataDict, f)
        f.close()
        # Use the youtubeDL() instance from MetadataFromUrl to obtain any extra information
        print('{0} written with {1} bytes of data for video `{2}`'.format(args.save_as,
                                                                          os.path.getsize(absPath),
                                                                          ytld._make_archive_id(metadataDict)))

def playlists(st):
    parser = argparse.ArgumentParser(description=commands['playlists'], formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--config', action='store', help='Location of the settings configuration file')
    args = parser.parse_args(sys.argv[2:])

    # Parse the correct file
    if args.config is not None:
        configs = st.ParseConfigFile(filename=args.config)
    else:
        configs = st.ParseConfigFile()

    st.SetSettings(configs)

    dbdir = "\Plex Media Server\Plug-in Support\Databases"
    #plister = Playlister()
    #plister.test(dbdir)
    plex = PlexDB(dbdir)
    if not plex.connect():
        print("Unsuccessful connection to database, exiting...")
        exit(1)

    plexdb_playlists = plex.get_playlists()

    # Recurse through each directory looking for .metadata dirs
    # For each dir.root in the config
    metadata_files = st.find_metadata_files()
    playlists = {}
    plmgr = Playlister(dbdir)
    metadatas = plmgr.file_paths_to_metadata(metadata_files)
    for metadata in metadatas:
        if 'playlist_title' in metadata:
            file_path = metadata['_file_path']
            # Increment playlist counts, eg: playlists[name] += 1
            pt = metadata['playlist_title']

            # Skip default playlists
            if pt.startswith(u'Uploads from '):
                continue

            if pt in playlists:
                playlists[pt]['count'] = 1 + playlists[pt]['count']
                playlists[pt]['file_paths'].append(file_path)
            else:
                playlists[pt] = {'count': 1, 'file_paths': [file_path]}

    # Print each playlist with its item count
    # pprint(playlists)
    metadata_titles = []

    for title, dict in playlists.items():
        metadata_titles.append(title)
        # print("Processing playlist: %s" % title)
        # playlist_id = plex.get_playlist_id_by_title(title)
        plmgr.create_plexdb_playlist(title, dict['file_paths'])
        # print("")

# main()
if __name__ == '__main__':
    """
    Do argument setup / description, and execute subcommand
    """
    cmdStr = ''
    for cmd, desc in sorted(commands.items()):
        cmdStr += '  %s%s\n' % (cmd.ljust(10, ' '), desc)

    parser = argparse.ArgumentParser(prog=PROG_NAME, description='', usage='''%(prog)s <command> [<args>]

The most commonly used %(prog)s commands are:

''' + cmdStr)

    parser.add_argument('command', help='Subcommand to run')
    args = parser.parse_args(sys.argv[1:2])
    if (args.command not in commands.keys()):
        print('Unrecognized command')
        parser.print_help()
        exit(1)
    # use CLI command == function name, use it
    st = sicktube.Sicktube()
    if 'run' == args.command:
        run(st)
    elif 'config' == args.command:
        config(st)
    elif 'email' == args.command:
        email(st)
    elif 'metadata' == args.command:
        metadata(st)
    elif 'playlists' == args.command:
        playlists(st)
