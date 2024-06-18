#!/usr/bin/env python3

"""Template/boilerplate for writing new test classes"""

# Note this will get discovered and run as a no-op test. This is fine.

import sys, os, re
import unittest
import logging
from unittest.mock import Mock, patch # if needed

DATA_DIR = os.path.abspath(os.path.dirname(__file__))
VERBOSE = os.environ.get('VERBOSE', '0') != '0'

from make_the_pdfs import ODTTemplate, TXTTemplate

class T(unittest.TestCase):

    def test_txt_basic(self):
        l1 = TXTTemplate(os.path.join(DATA_DIR, "t_basic.csv"))

        # l1.get_fields(name_list)
        # returns the non-suffix fields and the suffix fields and the suffixes.

        # usual empty case
        self.assertEqual(l1.get_fields([]),
                         dict( ns_fields = [],
                               s_fields = [],
                               suffixes = [],
                               missing = [] ) )

        self.assertEqual(l1.get_fields("FOO BAR BAZ".split()),
                         dict( ns_fields = ["FOO", "BAR", "BAZ"],
                               s_fields = [],
                               suffixes = [],
                               missing = [] ) )

        # This should work for a subset of fields
        self.assertEqual(l1.get_fields("BAR".split()),
                         dict( ns_fields = ["BAR"],
                               s_fields = [],
                               suffixes = [],
                               missing = [] ) )

        # And if a field is not in the template at all this just gets reported as a
        # ns_field. But we'll also note that it's missing.
        self.assertEqual(l1.get_fields("BAR NOPE NYET".split()),
                         dict( ns_fields = ["BAR", "NOPE", "NYET"],
                               s_fields = [],
                               suffixes = [],
                               missing  = ["NOPE", "NYET"]) )

if __name__ == '__main__':
    unittest.main()
