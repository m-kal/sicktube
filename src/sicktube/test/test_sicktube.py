import unittest
import sqlite3

import sys
import os.path
sys.path.append(os.path.abspath('..'))

from sicktube import Sicktube

class SicktubeTestStatics(unittest.TestCase):
    def test_ResolveTemplateWithDict(self):
        # Basic substitution
        self.assertEquals(Sicktube.ResolveTemplateWithDict('%(title)s', {'title': 'Test Pass'}), 'Test Pass')
        # Average use case
        self.assertEquals(Sicktube.ResolveTemplateWithDict('%(title)s-%(id)s.%(ext)s', {'title': 'Test Pass', 'id': 1, 'ext': 'tst'}), 'Test Pass-1.tst')
        # Missing components
        # self.assertEquals(Sicktube.ResolveTemplateWithDict('%(title)s-%(id)s.%(ext)s', {'id': 2, 'ext': 'tst'}), '-2.tst')

    def test_FromConfigFile(self):
        print "FromConfigFile"

    def test_GetSectionOptions(self):
        print "GetSectionOptions"

    def test_MetadataFromUrl(self):
        print "MetadataFromUrl"