#!/usr/bin/env python3

"""See about making the args_to_replacements() function work for labels (multiple placeholders)
   and multi-replace (multiple columns).
"""

import sys, os, re
import unittest
import logging
from unittest.mock import Mock, patch # if needed

DATA_DIR = os.path.abspath(os.path.dirname(__file__))
VERBOSE = os.environ.get('VERBOSE', '0') != '0'

from make_the_pdfs import args_to_replacements

class T(unittest.TestCase):

    def test_basic(self):

        a = args_to_replacements("FOO=a", "BAR=b", "FOO=c")
        self.assertEqual(a, [ {'FOO': 'a', 'BAR': 'b'},
                              {'FOO': 'c', 'BAR': 'b'} ])

    def test_file(self):

        a = args_to_replacements("FOO=a", "BAR=@alist.tsv", base_dir=DATA_DIR)

        self.assertEqual(a, [ {'FOO': 'a', 'BAR': 'Peter'},
                              {'FOO': 'a', 'BAR': 'Lois'},
                              {'FOO': 'a', 'BAR': 'Meg'},
                              {'FOO': 'a', 'BAR': 'Chris'}, ])

    def test_file_2_cols(self):
        # Here the blist.tsv has two lines and two columns. The function should spot that it's
        # reading the alist.tsv file twice and should add the new item to the replacements
        # without expanding the replacements list.

        a = args_to_replacements("FOO=a", "BAR=@alist.tsv", "BAZ=@blist.tsv", "ADDR=@alist.tsv",
                                 base_dir = DATA_DIR)

        expected =  [ {'FOO': 'a', 'BAR': 'Peter', 'BAZ': 'a', 'ADDR': 'peter68@example.org'},
                      {'FOO': 'a', 'BAR': 'Lois',  'BAZ': 'a', 'ADDR': 'lois@example.org'},
                      {'FOO': 'a', 'BAR': 'Meg',   'BAZ': 'a', 'ADDR': 'mg@example.org'},
                      {'FOO': 'a', 'BAR': 'Chris', 'BAZ': 'a', 'ADDR': 'cg@example.org'},
                      {'FOO': 'a', 'BAR': 'Peter', 'BAZ': 'c', 'ADDR': 'peter68@example.org'},
                      {'FOO': 'a', 'BAR': 'Lois',  'BAZ': 'c', 'ADDR': 'lois@example.org'},
                      {'FOO': 'a', 'BAR': 'Meg',   'BAZ': 'c', 'ADDR': 'mg@example.org'},
                      {'FOO': 'a', 'BAR': 'Chris', 'BAZ': 'c', 'ADDR': 'cg@example.org'}, ]

        self.assertEqual(a, expected)

if __name__ == '__main__':
    unittest.main()
