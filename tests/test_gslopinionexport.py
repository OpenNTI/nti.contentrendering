#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" """
from __future__ import print_function, unicode_literals
from hamcrest import assert_that, contains_string
from nose.tools import assert_raises
import os
import sys

import nti.tests
import nti.contentrendering
from nti.contentrendering import gslopinionexport

try:
	import cStringIO as StringIO
except ImportError:
	import StringIO

import pyquery

class TestGSL(nti.tests.ConfiguringTestBase):
	set_up_packages = (nti.contentrendering,)

	def test_runthrough(self):
		out = StringIO.StringIO()
		pq = pyquery.PyQuery( filename=os.path.join( os.path.dirname(__file__), 'gslopinion.html' ) )
		gslopinionexport._opinion_to_tex( pq, out, 'http://foo.bar' )
		assert_that( out.getvalue(), contains_string( br'\href{/scholar\_case' ) )
		assert_that( out.getvalue(), contains_string( br'{ \textit{Bushman,} 1 Cal. 3d, at 773, 463 P. 2d, at 730, }' ) )
		assert_that( out.getvalue(), contains_string( br'created. \footnote{It is illuminating' ) )
		assert_that( out.getvalue(), contains_string( br'\textbf{403 U.S. 15 (1971)}' ) )


	def test_main(self):
		old = gslopinionexport.requests
		old_out = sys.stdout

		class MockRequests(object):
			text = None
			def get(self, url):
				self.text = open( os.path.join( os.path.dirname(__file__), 'gslopinion.html' ), 'rU' ).read()
				return self

		try:
			sys.stdout = StringIO.StringIO()
			gslopinionexport.requests = MockRequests()
			gslopinionexport.main()
		finally:
			gslopinionexport.requests = old
			sys.stdout = old_out
