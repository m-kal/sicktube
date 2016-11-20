# youtube-dl dependencies
from __future__ import unicode_literals
import youtube_dl

# sicktube dependencies
import sys
import os
import ConfigParser
import argparse
import json
from pprint import pprint

import smtplib
from email.mime.text import MIMEText

'''
TODO:
* [ ] Add missing youtube metadata
* [x] Add metadata test function
* [x] Add url-to-metadata static method to get metadata from `webpage_url`
* [x] Add config dump cli method
* [ ] Video file rename changes may cause issue looking up `.info.json` files *// can make this a hard-no*
* [ ] Instantiate a video-saver at PlexAgent initialization/Start() *// needed for per-section settings*
* [ ] Configure a` .metadata-cache` folder and setting?
* [ ] Configurare an archives file? *// maybe have [...]/.metadata-cache/archive.log*
* [x] Enable email
* [x] Ensure email gets config param and loads settings for email addrs and ports
'''

# Consts
INI_FILE_SETTINGS_FILENAME = 'settings.cfg'
INI_FILE_SETTINGS_SECTION  = '_global'
INI_FILE_SETTINGS_URLS_OPT = 'urls'

# Create Sicktube settings
SAVER_SETTINGS = {
    # Directory settings
    'dir.root': 'x:/sicktube',
    'dir.extractor.prefix': False,
    'dir.extractor.postfix': False,
    ##'dir.metadata.name': '.metadata',
    ##'dir.archive.name': None,

    # File settings
    'file.template.name': youtube_dl.DEFAULT_OUTTMPL,
    ##'file.archive.name': 'archive.log',
    ##'file.archive.global': True,
    ##'file.metadata.cache.prefer': True,
    ##'file.metadata.cache.force-rebuild': False,

    # Email server configuratiton
    'email.enable': False,
    'email.server': 'localhost',
    'email.port': 25
}

# Create Youtube-DL downloader settings
YOUTUBEDL_SETTINGS = {
    # set options critical to expected behavior
    'format':           'bestvideo+bestaudio',  # Caching assumes we want best quality to transcode later
    'skip_download':    True,                   # Skips downloading the video file but will download the .info.json file
    'simulate':         True,                   # Skips downloading the video and the .info.json file

    # overwrite any youtube-dl settings that may interfere with expected behavior
    'writeinfojson':    True,                   # Don't write out the info.json file
    'quiet':            False,                  # Don't spam the console with debug info
    'ffmpeg_location':  'c:/ffmpeg/bin',        # Location of FFMPEG
    'ignoreerrors':     True
}

class Sicktube:
    """
    Management and execution for browsing the internet
    in a similar manner to existing browsing history
    """
    sectionUrlDict = {}
    youtubeDl = None
    ytdlSettings = {}
    settings = {}
    runStats = { 'new': 0, 'old': 0 }
    commands = {
        'config': 'Dumps/prints the configuration file',
        'email': 'Email yourself a test message to check if the email options are configured correctly',
        'metadata': 'Dumps/prints metadata for a url, useful for testing'
    }
    # program consts
    PROG_NAME = 'Sicktube'

    def __init__(self):

        """
        Do argument setup / description, and execute subcommand
        """
        cmdStr = ''
        for cmd, desc in sorted(self.commands.items()):
            cmdStr += '  %s%s\n' % (cmd.ljust(10, ' '), desc)

        parser = argparse.ArgumentParser(prog = self.PROG_NAME, description = '', usage = '''%(prog)s <command> [<args>]

The most commonly used %(prog)s commands are:

''' + cmdStr)

        parser.add_argument('command', help = 'Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])
        if (not hasattr(self, args.command)) or (args.command not in self.commands.keys()):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        # use CLI command == function name, use it
        getattr( self, args.command )( )

    # First-Order CLI commands
    def config(self):
        parser = argparse.ArgumentParser( description = self.commands['config'],
                                          formatter_class = argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument( '--config', action = 'store', help = 'Location of the settings configuration file' )
        args = parser.parse_args( sys.argv[ 2: ] )

        # Parse the correct file
        if args.config is not None:
            configs = self.ParseConfig(filename=args.config)
        else:
            configs = self.ParseConfig()

        # Pretty print each config
        for k in configs:
            print '\nSection Config For: {0}\n'.format(k)
            pprint(self.GetSectionOptions(configs, k))

    def email(self):
        parser = argparse.ArgumentParser( description = self.commands['email'],
                                          formatter_class = argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument( '--config', action = 'store', help = 'Location of the settings configuration file' )
        parser.add_argument( '--from-addr', action = 'store', help = 'Test sender\'s email address', default='admin@localhost' )
        parser.add_argument( '--to-addr', action = 'store', help = 'Test recipient\'s email address', default='admin@localhost' )
        parser.add_argument( '--msg', action = 'store', help = 'Test email message', default='This is a test message sent for {0}'.format(self.PROG_NAME) )
        parser.add_argument( '--subject', action = 'store', help = 'Test email message subject', default='[{0}] Test configuration email'.format(self.PROG_NAME) )
        args = parser.parse_args( sys.argv[ 2: ] )

        # Parse the correct file
        if args.config is not None:
            configs = self.ParseConfig(filename=args.config)
        else:
            configs = self.ParseConfig()

        msg = MIMEText(args.msg)
        msg['Subject'] = args.subject
        s = smtplib.SMTP(configs[INI_FILE_SETTINGS_SECTION]['email.server'], configs[INI_FILE_SETTINGS_SECTION]['email.port'])
        msg['From'] = args.from_addr
        msg['To'] = args.to_addr
        s.sendmail(msg['From'], msg['To'], msg.as_string())
        s.quit()
        print 'Email message sent from `{0}` to `{1}` with a subject of `{2}`'.format(args.from_addr, args.to_addr, args.subject)
        print 'Email Feature Status: {0}'.format('Enabled' if configs[INI_FILE_SETTINGS_SECTION]['email.enable'] else 'Disabled')

    def metadata(self):
        parser = argparse.ArgumentParser( description = self.commands['metadata'],
                                          formatter_class = argparse.ArgumentDefaultsHelpFormatter )
        parser.add_argument( 'url', action = 'store', help = 'URL to extract metadata for' )
        parser.add_argument( '--save-as', action = 'store', help = 'Save the metadata to a file rather than printing to stdout' )
        parser.add_argument( '--config', action = 'store', help = 'Location of the settings configuration file' )
        args = parser.parse_args( sys.argv[ 2: ] )

        (metadataDict, ytld) = self.MetadataFromUrl(args.url)
        if args.save_as is None:
            # Print to screen because no save file was set
            pprint(metadataDict)
        else:
            absPath = os.path.abspath(args.save_as)
            if not os.path.exists(absPath):
                print '{0} doesnt exist yet'.format(absPath)

            # Dump the dict to file through the json lib rather than a print-style dump
            f = open(absPath, 'w')
            json.dump(metadataDict, f)
            f.close()
            # Use the youtubeDL() instance from MetadataFromUrl to obtain any extra information
            print '{0} written with {1} bytes of data for video `{2}`'.format(args.save_as, os.path.getsize(absPath), ytld._make_archive_id(metadataDict))

    # Static methods
    @staticmethod
    def FromConfigFile(filename=INI_FILE_SETTINGS_FILENAME, settings=SAVER_SETTINGS, ytdlSettings=YOUTUBEDL_SETTINGS):
        if not os.path.exists(filename):
            print '{0} does not exist.'.format(filename)
            return None

        ytsv = Sicktube()
        ytsv.SetSettings(settings)
        ytsv.SetYoutubeDlSettings(ytdlSettings)
        ytsv.sectionUrlDict = ytsv.ParseConfig(filename)

        return ytsv

    @staticmethod
    def GetSectionOptions(optionsDict, section):
        sectionOptions = {}
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
        metadataYtdlOpts['quiet'] = True
        metadataYtdlOpts['writeinfojson'] = False
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


    # Object methods
    def SetSettings(self, settings):
        self.settings = settings

    def SetYoutubeDlSettings(self, ytdlSettings):
        self.ytdlSettings = ytdlSettings
        self.youtubeDl = youtube_dl.YoutubeDL(self.ytdlSettings)

    def ParseConfig(self, filename=INI_FILE_SETTINGS_FILENAME):
        '''Parses a configuration file and returns a merged set of options on a per-section basis'''

        # The dictionary structure is { INI_FILE_SETTINGS_SECTION: [], '<section>': [] }
        globalOptions = SAVER_SETTINGS.copy()
        globalOptions.update(YOUTUBEDL_SETTINGS)

        sectionUrlDict = {}
        configOptions = {}
        # Use a RawConfigParser to disable option name interpolation
        # so as not to conflict with templateing strings for Youtube-DL
        config = ConfigParser.RawConfigParser(self.settings, allow_no_value=True)
        config.read(filename)

        overWriteGlobalOpts = {}
        if config.has_section(INI_FILE_SETTINGS_SECTION):
            for section in config.sections():
                if section == INI_FILE_SETTINGS_SECTION:
                    for option in config.options(section):
                        overWriteGlobalOpts[option] = config.get(section, option)

        for key in overWriteGlobalOpts:
            globalOptions[key] = overWriteGlobalOpts[key]

        parsedOptions = { INI_FILE_SETTINGS_SECTION: globalOptions }

        for section in config.sections():
            # Do not generation per-section config options for the global optitons,
            # Instead update the global options, which was already done
            if section == INI_FILE_SETTINGS_SECTION:
                continue

            urlOptionKey = '_{0}'.format(INI_FILE_SETTINGS_URLS_OPT)
            sectionOptions = { urlOptionKey: [] }
            for option in config.options(section):
                optionVal = config.get(section, option)
                if option == INI_FILE_SETTINGS_URLS_OPT:
                    urlList = [s.strip() for s in optionVal.splitlines()]
                    sectionOptions[urlOptionKey] = urlList
                else:
                    sectionOptions[option] = optionVal
            parsedOptions[section] = sectionOptions

        return parsedOptions

    def DetermineOutputDir(self, section):
        prefixDir = ('%(extractor_key)s/' if 'dir.extractor.prefix' in self.settings and self.settings['dir.extractor.prefix'] else '')
        postfixDir = ('/%(extractor_key)s' if 'dir.extractor.postfix' in self.settings and self.settings['dir.extractor.postfix'] else '')
        if section == 'Misc':
            return '{0}/{1}{2}{3}/'.format(self.settings['dir.root'], prefixDir, section, postfixDir)
        return '{0}/{1}{2}{3}/%(uploader)s/'.format(self.settings['dir.root'], prefixDir, section, postfixDir)

    def GetFullOutputTemplate(self, section):
        return '{0}{1}'.format(self.DetermineOutputDir(section), self.settings['file.template.name'])

    def GetFullArchiveFilePath(self, section):
        return '{0}/{1}'.format(self.settings['dir.root'], 'archive.txt')

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

# main()
if __name__ == '__main__':
    ytsv = Sicktube()
