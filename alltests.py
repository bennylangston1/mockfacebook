#!/usr/bin/python
"""Runs all unit tests in *_test.py files in the current directory.
"""

__author__ = ['Ryan Barrett <mockfacebook@ryanb.org>']

import glob
import imp
import logging
import os
import sys
import unittest


def main():
  # don't show logging messages
  logging.disable(logging.CRITICAL + 1)

  for filename in glob.glob('*_test.py'):
    name = os.path.splitext(filename)[0]

    # these are wishlisted right now.
    if name in ('server_test', 'graph_on_fql_test'):
      continue
    elif name in sys.modules:
      # this is important. imp.load_module() twice is effectively a reload,
      # which duplicates multiply inherited test case base classes and makes
      # super() think an instance of one isn't an instance of another.
      module = sys.modules[name]
    else:
      module = imp.load_module(name, *imp.find_module(name))

    # ugh. this is the simplest way to make all of the test classes defined in
    # the modules visible to unittest.main(), but it's really ugly.
    globals().update(vars(module))

  unittest.main()


if __name__ == '__main__':
  main()
