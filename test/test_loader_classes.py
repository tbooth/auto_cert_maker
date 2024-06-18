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
        l1 = TXTTemplate(os.path.join(DATA_DIR, "t_basic.txt"))

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

    def test_txt_indexed(self):
        l2 = TXTTemplate(os.path.join(DATA_DIR, "t_suffixed.txt"))

        # FOO is not suffixed
        self.assertEqual(l2.get_fields("FOO".split()),
                         dict( ns_fields = ["FOO"],
                               s_fields = [],
                               suffixes = [],
                               missing = [] ) )

        # BAR is suffixed
        self.assertEqual(l2.get_fields("BAR".split()),
                         dict( ns_fields = [],
                               s_fields = ["BAR"],
                               suffixes = ["-1", "-2"],
                               missing = [] ) )

        # Get everything
        self.assertEqual(l2.get_fields("FOO BAR BAZ MEEP NYET".split()),
                         dict( ns_fields = ["FOO", "MEEP", "NYET"],
                               s_fields = ["BAR", "BAZ"],
                               suffixes = ["-1", "-2"],
                               missing = ["NYET"] ) )

    def test_odf_indexed(self):
        """As above but with the .odt file
        """
        odtt = ODTTemplate(os.path.join(DATA_DIR, "t_suffixed.odt"))

        # FOO is not suffixed
        self.assertEqual(odtt.get_fields("FOO".split()),
                         dict( ns_fields = ["FOO"],
                               s_fields = [],
                               suffixes = [],
                               missing = [] ) )

        # BAR is suffixed
        self.assertEqual(odtt.get_fields("BAR".split()),
                         dict( ns_fields = [],
                               s_fields = ["BAR"],
                               suffixes = ["-1", "-2"],
                               missing = [] ) )

        # Get everything
        self.assertEqual(odtt.get_fields("FOO BAR BAZ MEEP NYET".split()),
                         dict( ns_fields = ["FOO", "MEEP", "NYET"],
                               s_fields = ["BAR", "BAZ"],
                               suffixes = ["-1", "-2"],
                               missing = ["NYET"] ) )


if __name__ == '__main__':
    unittest.main()
