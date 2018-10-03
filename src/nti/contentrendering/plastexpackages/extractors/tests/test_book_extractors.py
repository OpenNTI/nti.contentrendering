#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
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
from nti.contentrendering.plastexpackages.extractors import _ContentUnitStatistics

from nti.contentrendering.plastexpackages.tests import ExtractorTestLayer

class TestBookExtractor(unittest.TestCase):

	layer = ExtractorTestLayer

	def test_book_extractor_works(self):
		# Does very little verification. Mostly makes sure we don't crash
		name = 'sample_book.tex'
		with open(os.path.join( os.path.dirname(__file__), name)) as fp:
			book_string = fp.read()
		
		class Book(object):
			toc = None
			document = None
			contentLocation = None
		book = Book()

		with RenderContext(simpleLatexDocumentText(
								preludes=("\\usepackage{ntilatexmacros}",),
								bodies=(book_string, )),
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
			assert_that(book.toc.dom.documentElement.nodeName, is_('toc'))
			assert_that(book.toc.dom.documentElement.getElementsByTagName('topic'), has_length(5))
			assert_that(book.toc.dom.documentElement.attributes, has_entry('href', 'tag_nextthought_com_2011-10_testing-HTML-temp_0.html'))
			assert_that(book.toc.dom.documentElement.getAttributeNode('href').value, is_('tag_nextthought_com_2011-10_testing-HTML-temp_0.html'))
			
			node = book.toc.dom.documentElement
			
			for i, child in enumerate(node.childNodes):
				if child.nodeName == 'topic':
					if i == 1 :
						assert_that(child.getAttributeNode('href').value, is_('tag_nextthought_com_2011-10_testing-HTML-temp_chapter_FAQ.html'))
						assert_that(child.getAttributeNode('ntiid').value, is_('tag:nextthought.com,2011-10:testing-HTML-temp.chapter:FAQ'))
					if i == 3:
						assert_that(child.getAttributeNode('href').value, is_('tag_nextthought_com_2011-10_testing-HTML-temp_chapter_Getting_Started.html'))
						assert_that(child.getAttributeNode('ntiid').value, is_('tag:nextthought.com,2011-10:testing-HTML-temp.chapter:Getting_Started'))

			
			stat = _ContentUnitStatistics(book)
			result = stat.transform(book)
			
			level_0 = result['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.0']
			assert_that(level_0, has_entry('NTIID', 'tag:nextthought.com,2011-10:testing-HTML-temp.0'))
			assert_that(len(level_0['Items']), is_(2))

			level_1 = level_0['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:FAQ']
			assert_that(len(level_1['Items']), is_(2))

			level_1 = level_0['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:Getting_Started']
			assert_that(len(level_1['Items']), is_(1))