#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import has_entries
from hamcrest import assert_that

import os
import unittest


from nti.contentrendering.tests import RenderContext
from nti.contentrendering.tests import simpleLatexDocumentText

from nti.contentrendering.RenderedBook import EclipseTOC
from nti.contentrendering.resources import ResourceRenderer

from nti.contentrendering.plastexpackages.extractors import _CourseExtractor
from nti.contentrendering.plastexpackages.extractors import _RelatedWorkExtractor

from nti.contentrendering.plastexpackages.tests import ExtractorTestLayer

class TestCourseExtractor(unittest.TestCase):

	layer = ExtractorTestLayer

	def test_course_and_related_extractor_works(self):
		# Does very little verification. Mostly makes sure we don't crash
		name = 'sample_book.tex'
		with open(os.path.join( os.path.dirname(__file__), name)) as fp:
			course_string = fp.read()
		
		class Book(object):
			toc = None
			document = None
			contentLocation = None
		book = Book()

		with RenderContext(simpleLatexDocumentText(
								preludes=("\\usepackage{nticourse}", "\\usepackage{ntilatexmacros}"),
								bodies=(course_string, )),
						   	packages_on_texinputs=True) as ctx:
			book.document = ctx.dom
			book.contentLocation = ctx.docdir

			render = ResourceRenderer.createResourceRenderer('XHTML', None)
			render.render( ctx.dom )
			book.toc = EclipseTOC(os.path.join(ctx.docdir, 'eclipse-toc.xml'))
			ctx.dom.renderer = render

			ext = _CourseExtractor()
			ext.transform(book)

			__traceback_info__ = book.toc.dom.toprettyxml()

			assert_that(book.toc.dom.documentElement.attributes, has_entry('isCourse', 'false'))
			