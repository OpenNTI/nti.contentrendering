#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import os

from hamcrest import is_
from hamcrest import assert_that
from hamcrest import greater_than

from nti.contentrendering.plastexpackages.extractors.html.tests import HTMLExtractorTests

from nti.contentrendering.plastexpackages.extractors.html.reader import HTMLReader

from nti.contentrendering.plastexpackages.extractors.html.processor import process_html_body

from nti.contentrendering.plastexpackages.extractors.html.statistics import HTMLExtractor

class HTMLExtractorTest(HTMLExtractorTests):
	def test_chapter(self):
		filename = "tag_nextthought_com_2011-10_IFSTA-HTML-sample_book_chapter_Getting_Started.html"
		inputfile = os.path.join(os.path.dirname(__file__), filename)
		reader = HTMLReader(inputfile)
		element = reader.element
		extractor = HTMLExtractor(element)
		assert_that(extractor.number_paragraph, is_(0))
		assert_that(extractor.total_number_of_words(), is_(2))

	def test_section(self):
		filename = "tag_nextthought_com_2011-10_IFSTA-HTML-sample_book_section_General_Features.html"
		inputfile = os.path.join(os.path.dirname(__file__), filename)
		reader = HTMLReader(inputfile)
		element = reader.element
		extractor = HTMLExtractor(element)
		assert_that(extractor.number_paragraph, is_(2))
		number_of_words = extractor.total_number_of_words()
		assert_that(number_of_words, greater_than(50))
		assert_that(extractor.number_sentence, is_(5))
		