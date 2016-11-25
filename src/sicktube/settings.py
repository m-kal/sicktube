import json
import youtube_dl

def constant(f):
    def fset(self, value):
        raise TypeError

    def fget(self):
        return f()

    return property(fget, fset)


class Setting(object):
    @staticmethod
    def Filename(self=None):
        return 'settings-default.json'

    @staticmethod
    def ConvergedDefaults():
        defaults = {}
        jsonData = json.load(open(Setting.Filename()))
        for jsonKey, jsonValue in jsonData.iteritems():
            defaults[jsonKey] = jsonValue

        return defaults

    @staticmethod
    def Defaults():
        k = Setting.Keys()
        return {
            # System settings
            k.SYS_REPEAT_ENABLE: False,
            k.SYS_REPEAT_DELAY: 900,

            # Directory settings
            k.DIR_ROOT: 'x:/sicktube',
            k.DIR_VIDEO_AUTHOR: True,
            k.DIR_METADATA_CACHE_ENABLE: True,
            k.DIR_METADATA_NAME: '.metadata',
            ##'dir.archive.name': None,

            # File settings
            k.FILE_TEMPLATE_NAME: '%(title)s-%(id)s.%(ext)s',
            k.FILE_ARCHIVE_NAME: 'archive.log',
            k.FILE_ARCHIVE_GLOBAL: False,
            ##'file.metadata.cache.prefer': True,
            ##'file.metadata.cache.force-rebuild': False,

            # Email server configuratiton
            k.EMAIL_ENABLE: True,
            k.EMAIL_SERVER: 'localhost',
            k.EMAIL_PORT: 25
        }

    class Keys(object):
        @staticmethod
        def _keys():
            return [x for x, y in Setting.Keys.__dict__.items() if not x.startswith('_')]

        '''System Keys'''
        @constant
        def SYS_REPEAT_ENABLE(self=None):
            return 'sys.repeat.enable'

        @constant
        def SYS_REPEAT_DELAY(self=None):
            return 'sys.repeat.delay'

        '''Directory Keys'''
        @constant
        def DIR_ROOT(self=None):
            return 'dir.root'
        @constant
        def DIR_VIDEO_AUTHOR(self=None):
            return 'dir.video.author'
        @constant
        def DIR_METADATA_NAME(self=None):
            return 'dir.metadata.name'
        @constant
        def DIR_METADATA_CACHE_ENABLE(self=None):
            return 'dir.metadata.cache-enable'

        '''File Keys'''
        @constant
        def FILE_TEMPLATE_NAME(self=None):
            return 'file.template.name'
        @constant
        def FILE_ARCHIVE_NAME(self=None):
            return 'file.archive.name'
        @constant
        def FILE_ARCHIVE_GLOBAL(self=None):
            return 'file.archive.global'

        '''Email Keys'''
        @constant
        def EMAIL_ENABLE(self=None):
            return 'email.enable'
        @constant
        def EMAIL_SERVER(self=None):
            return 'email.server'
        @constant
        def EMAIL_PORT(self=None):
            return 'email.port'