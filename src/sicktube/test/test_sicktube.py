import unittest

import sys
import os.path
sys.path.append(os.path.abspath('..'))

from sicktube import Sicktube
import settings
import json

class SicktubeTestStatics(unittest.TestCase):
    def test_ResolveTemplateWithDict(self):
        # Basic substitution
        self.assertEquals(Sicktube.ResolveTemplateWithDict('%(title)s', {'title': 'Test Pass'}), 'Test Pass')
        # Average use case
        self.assertEquals(Sicktube.ResolveTemplateWithDict('%(title)s-%(id)s.%(ext)s', {'title': 'Test Pass', 'id': 1, 'ext': 'tst'}), 'Test Pass-1.tst')
        # Missing components
        self.assertEquals(Sicktube.ResolveTemplateWithDict('%(title)s-%(id)s.%(ext)s', {'id': 2, 'ext': 'tst'}), '-2.tst')
        self.assertEquals(Sicktube.ResolveTemplateWithDict('%(title)s-%(id)s.%(ext)s', {'ext': 'tst'}), '-.tst')
        self.assertEquals(Sicktube.ResolveTemplateWithDict('%(title)s-%(id)s.%(ext)s', {}), '')
        self.assertEquals(Sicktube.ResolveTemplateWithDict('%(title)s-%%-%(id)s.%(ext)s', {}), '')
        self.assertEquals(Sicktube.ResolveTemplateWithDict('%(title)s-%%-%(id)s.%(ext)s', {'ext': 'tst'}), '-%-.tst')
        self.assertEquals(Sicktube.ResolveTemplateWithDict('%(title)s-%%-%(id)s.%(ext)s', {'id': 2, 'ext': 'tst'}), '-%-2.tst')
        # Wrong missing substitutions
        # self.assertEquals(Sicktube.ResolveTemplateWithDict('%(title)s-%%-%(id)s.%(ext)s', {'txe': 'tst'}), '')

    def test_FromConfigFile(self):
        print "FromConfigFile"

    def test_GetSectionOptions(self):
        print "GetSectionOptions"

    def test_MetadataFromUrl(self):
        print "MetadataFromUrl"

class SicktubeTestSettings(unittest.TestCase):
    def test_Load(self):
        # Ensure we can enumerate the keys from the settings
        self.assertGreater(len(settings.Setting.Keys._keys()), 0, "Enumerating all keys returns non-zero list")

        # Assert loading settings-default.json works
        self.assertEqual(settings.Setting.Filename(), 'settings-default.json')

        # Ensure all settings-default.json keys are in default keys
        defaults =  settings.Setting.Defaults()
        defaultPrefsJson = json.load(open(settings.Setting.Filename()))
        for jsonKey, v in defaultPrefsJson.iteritems():
            self.assertTrue(jsonKey in defaults)

        # Check that loading a file and converging work
        converged = settings.Setting().ConvergedDefaults()
        for covKey, covVal in converged.iteritems():
            self.assertTrue(covKey in defaults)

        # Check that no defaults were dropped off
        for dKey, dVal in defaults.iteritems():
            self.assertTrue(dKey in converged)

        # And now ensure thre are no extra keys
        self.assertEqual(len(converged), len(defaults))