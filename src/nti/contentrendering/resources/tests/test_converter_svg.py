#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


$Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

#disable: accessing protected members, too many methods
#pylint: disable=W0212,R0904

import os

from hamcrest import assert_that
from hamcrest import is_
from hamcrest import none
from hamcrest import has_length
from hamcrest import has_property
from hamcrest import close_to


from .. converter_svg import _do_convert, PDF2SVG, _programs
import unittest
import shutil
import tempfile
import functools

from .. import converter_svg

def skipIfNotOnPath(f):
	@functools.wraps(f)
	def test(self):
		verify = _programs.verify(('pdf2svg', 'pdfcrop'))
		if not verify:
			raise unittest.SkipTest("Program not on path: %s" % verify)
		f(self)

	return test

class TestSvgConverter(unittest.TestCase):

	input_filename = os.path.join(os.path.dirname(__file__), 'datastructure_comparison.pdf')

	@skipIfNotOnPath
	def test_do_convert(self):
		tempdir = tempfile.mkdtemp()
		cwd = os.getcwd()
		os.chdir(tempdir)
		try:
			filename  = _do_convert( 1, self.input_filename )
		finally:
			os.chdir(cwd)
			shutil.rmtree( tempdir )

		assert_that( filename, is_('img1.svg'))

	@skipIfNotOnPath
	def test_converter(self):
		tempdir = tempfile.mkdtemp()
		cwd = os.getcwd()
		os.chdir(tempdir)
		class Executor(object):
			def __init__(self, **kwargs):
				pass
			def map(self, *args):
				return map(*args)

			def __enter__(self):
				return self

			def __exit__(self, t, v, tb):
				return

		class Image(object):
			pass

		orig_exec = converter_svg.ProcessPoolExecutor
		converter_svg.ProcessPoolExecutor = Executor
		try:
			with open(self.input_filename, 'rb') as f:
				imager = PDF2SVG.__new__(PDF2SVG)
				imager.images = {'key' + str(i): Image() for i in range(24)}
				_, images = imager.executeConverter(f)

			assert_that( images, has_length(24) )
			assert_that( imager.images['key0'], has_property('width', close_to(640.0, 7.0)) )
		finally:
			converter_svg.ProcessPoolExecutor = orig_exec
			os.chdir(cwd)
			shutil.rmtree( tempdir )

	def test_do_convert_if_no_output(self):
		assert_that(_do_convert( 1, self.input_filename, _converter_program='echo' ),
					is_(none()))
