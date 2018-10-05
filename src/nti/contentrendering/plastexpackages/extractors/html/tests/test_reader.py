#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import os

from hamcrest import is_not
from hamcrest import assert_that

from nti.contentrendering.plastexpackages.extractors.html.tests import HTMLExtractorTests

from nti.contentrendering.plastexpackages.extractors.html.reader import HTMLReader

class HTMLReaderTest(HTMLExtractorTests):
	def test_reader(self):
		filename = "tag_nextthought_com_2011-10_IFSTA-HTML-sample_book_chapter_FAQ.html"
		inputfile = os.path.join(os.path.dirname(__file__), filename)
		reader = HTMLReader(inputfile)
		assert_that(reader.script, is_not(None))
		assert_that(reader.element, is_not(None))

