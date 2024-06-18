#!/usr/bin/env python3

"""The munge_replacements() function works out how to combine records into a single document
   to make, for example, a sheet of labels.
"""

import sys, os, re
import unittest
import logging
from unittest.mock import Mock, patch # if needed

DATA_DIR = os.path.abspath(os.path.dirname(__file__))
VERBOSE = os.environ.get('VERBOSE', '0') != '0'

from make_the_pdfs import munge_replacements

class T(unittest.TestCase):

    def setUp(self):
        # See the errors in all their glory
        self.maxDiff = None

    def test_basic(self):
        """The most basic case. There is a single value.
           The reps should be unchanged.
        """
        fields =  dict( ns_fields = ["FOO"],
                        s_fields = [],
                        suffixes = [],
                        missing = [] )
        reps = [ {'FOO': 'x'} ]

        res = munge_replacements(reps, fields)

        self.assertEqual(res, reps)

    def test_suff_basic(self):
        """The most basic suffixed case. There is a single value.
           The reps should be slightly changed.
        """
        fields =  dict( ns_fields = [],
                        s_fields = ["FOO"],
                        suffixes = ["-0"],
                        missing = [] )
        reps = [ {'FOO': 'x'} ]

        res = munge_replacements(reps, fields)

        self.assertEqual(res, [{'FOO-0': 'x'}])

    def text_suff_2(self):
        """This is more like it
        """
        fields =  dict( ns_fields = [],
                        s_fields = ["FOO"],
                        suffixes = ["-0", "-1", "-2"],
                        missing = [] )
        reps = [ {'FOO': 'x'}, {'FOO': 'y'}, {'FOO': 'z'}, {'FOO': 'odd'} ]

        res = munge_replacements(reps, fields)

        self.assertEqual(res, [{'FOO-0': 'x', 'FOO-1': 'y', 'FOO-2': 'z'},
                               {'FOO-0': 'odd'}])

    def test_suff_all(self):
        """This has it all going on.
           I may want to have an option to disregard missing?
        """
        fields = dict( ns_fields = ["FOO", "MEEP"],
                       s_fields = ["BAR", "BAZ"],
                       suffixes = ["-1", "-2"],
                       missing = [] )

        reps = [ {'FOO': 'a', 'BAR': '0', 'BAZ': '_0', 'MEEP': 'meep1'},
                 {'FOO': 'a', 'BAR': '1', 'BAZ': '_1', 'MEEP': 'meep1'},
                 {'FOO': 'a', 'BAR': '0', 'BAZ': '_0', 'MEEP': 'meep2'},
                 {'FOO': 'a', 'BAR': '1', 'BAZ': '_1', 'MEEP': 'meep3'},

                 {'FOO': 'a', 'BAR': '2', 'BAZ': '_2', 'MEEP': 'meep1'},
                 {'FOO': 'a', 'BAR': '3', 'BAZ': '_3', 'MEEP': 'meep2'},
                 {'FOO': 'a', 'BAR': '4', 'BAZ': '_4', 'MEEP': 'meep1'},
                 {'FOO': 'a', 'BAR': '5', 'BAZ': '_5', 'MEEP': 'meep2'} ]

        # The munger should be able to come up with:
        desired = [ {'FOO': 'a', 'BAR-1': '0', 'BAZ-1': '_0',
                                 'BAR-2': '1', 'BAZ-2': '_1', 'MEEP': 'meep1'},
                    {'FOO': 'a', 'BAR-1': '2', 'BAZ-1': '_2',
                                 'BAR-2': '4', 'BAZ-2': '_4', 'MEEP': 'meep1'},
                    {'FOO': 'a', 'BAR-1': '0', 'BAZ-1': '_0',
                                 'BAR-2': '3', 'BAZ-2': '_3', 'MEEP': 'meep2'},
                    {'FOO': 'a', 'BAR-1': '5',
                                 'BAZ-1': '_5', 'MEEP': 'meep2'},
                    {'FOO': 'a', 'BAR-1': '1',
                                 'BAZ-1': '_1', 'MEEP': 'meep3'}, ]

        res = munge_replacements(reps, fields)
        self.assertEqual(res, desired)

if __name__ == '__main__':
    unittest.main()
