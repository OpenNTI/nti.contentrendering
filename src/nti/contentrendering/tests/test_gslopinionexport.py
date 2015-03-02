#!/usr/bin/env python
# -*- coding: utf-8 -*-
# $Id$

from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

#disable: accessing protected members, too many methods
#pylint: disable=W0212,R0904


from hamcrest import assert_that
from hamcrest import contains_string
from hamcrest import is_
from nose.tools import assert_raises

import os
import shutil

from . import ContentrenderingLayerTest
import nti.contentrendering
from nti.contentrendering import gslopinionexport

try:
	import cStringIO as StringIO
except ImportError:
	import StringIO

import pyquery
import fudge

class TestGSL(ContentrenderingLayerTest):
	set_up_packages = (nti.contentrendering,)

	def test_runthrough(self):
		out = StringIO.StringIO()
		pq = pyquery.PyQuery( filename=os.path.join( os.path.dirname(__file__), 'gslopinion.html' ) )
		gslopinionexport._opinion_to_tex( pq, out, 'http://foo.bar' )
		assert_that( out.getvalue(), contains_string( br'\href{/scholar\_case' ) )
		assert_that( out.getvalue(), contains_string( br'\subsection{Opinion of the Court' ) )
		assert_that( out.getvalue(), contains_string( br'\section{MR. JUSTICE BLACKMUN' ) )
		assert_that( out.getvalue(), contains_string( br'\section{MR. JUSTICE WHITE' ) )
		assert_that( out.getvalue(), contains_string( br'{ \textit{Bushman,} 1 Cal. 3d, at 773, 463 P. 2d, at 730, }' ) )
		assert_that( out.getvalue(), contains_string( br'created. \footnote{It is illuminating' ) )
		assert_that( out.getvalue(), contains_string( br'\textbf{403 U.S. 15 (1971)}' ) )


	@fudge.patch('requests.get', 'nti.contentrendering.gslopinionexport.sys')
	def test_main(self, fake_get, fake_sys):
		fake_get.expects_call().returns_fake().has_attr( text=open( os.path.join( os.path.dirname(__file__), 'gslopinion.html' ), 'rU' ).read() )
		fake_sys.has_attr( argv=['a', 'b'], stdout=fudge.Fake(name='stdout').provides('write') )

		contentLocation = 'COHEN_v__CALIFORNIA_'
		try:
			os.chdir( '/tmp' )
			gslopinionexport.main(_do_config=False) # as we've already loaded it
			assert_that( os.path.exists(os.path.join( contentLocation, 'COHEN_v__CALIFORNIA_.tex' ) ),
						    is_(True) )
			assert_that( os.path.exists(os.path.join( contentLocation, 'nti_render_conf.ini' ) ),
						    is_(True) )
		finally:
			if os.path.exists( contentLocation ):
				shutil.rmtree( contentLocation )