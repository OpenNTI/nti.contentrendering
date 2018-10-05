#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

import os

from hamcrest import is_
from hamcrest import assert_that
from hamcrest import greater_than

from nti.contentrendering.plastexpackages.extractors.html.reader import HTMLReader

from nti.contentrendering.plastexpackages.extractors.html.statistics import HTMLExtractor

from nti.contentrendering.plastexpackages.extractors.html.tests import HTMLExtractorTests


class HTMLExtractorTest(HTMLExtractorTests):

    def data_file(self, name):
        return os.path.join(os.path.dirname(__file__), 'data', name)

    def test_chapter(self):
        filename = "tag_nextthought_com_2011-10_IFSTA-HTML-sample_book_chapter_Getting_Started.html"
        reader = HTMLReader(self.data_file(filename))
        element = reader.element
        extractor = HTMLExtractor(element)
        assert_that(extractor.number_paragraph, is_(0))
        assert_that(extractor.total_number_of_words(), is_(2))

    def test_section(self):
        filename = "tag_nextthought_com_2011-10_IFSTA-HTML-sample_book_section_General_Features.html"
        reader = HTMLReader(self.data_file(filename))
        element = reader.element
        extractor = HTMLExtractor(element)
        assert_that(extractor.number_paragraph, is_(2))
        number_of_words = extractor.total_number_of_words()
        assert_that(number_of_words, greater_than(50))
        assert_that(extractor.number_sentence, is_(5))
