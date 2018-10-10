#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import is_not
from hamcrest import assert_that

import os

from nti.contentrendering.plastexpackages.extractors.html.reader import HTMLReader

from nti.contentrendering.plastexpackages.extractors.html.processor import process_html_body

from nti.contentrendering.plastexpackages.extractors.html.tests import HTMLSample
from nti.contentrendering.plastexpackages.extractors.html.tests import HTMLExtractorTests


class HTMLReaderTest(HTMLExtractorTests):

    def data_file(self, name):
        return os.path.join(os.path.dirname(__file__), 'data', name)

    def test_reader(self):
        filename = "tag_nextthought_com_2011-10_IFSTA-HTML-sample_book_chapter_FAQ.html"
        reader = HTMLReader(self.data_file(filename))
        assert_that(reader.script, is_not(None))
        assert_that(reader.element, is_not(None))
        assert_that(reader.element.find('body'), is_not(None))

    def test_reader_processor(self):
        filename = "tag_nextthought_com_2011-10_IFSTA-HTML-sample_book_section_General_Features.html"
        reader = HTMLReader(self.data_file(filename))
        assert_that(reader.script, is_not(None))
        assert_that(reader.element, is_not(None))
        assert_that(reader.element.find('body'), is_not(None))

        html = HTMLSample()
        text = process_html_body(reader.element, html)
        assert_that(html.number_paragraph, is_(2))
        assert_that(html.number_sidebar, is_(0))
        assert_that(text, is_(u'  General Features \n \n  You control who is able to see your note. To change who your note is shared with or add someone to the note, begin typing a contact, list, or group\u2019s name in the sharing field and click on them to share.  \n To remove a person, group, or list, hover over their name in the sharing field, and an \u201cx\u201d will appear. Click the x to remove. If no one is listed in the sharing field, the note will be private and only you can access it.  \n '))

    def test_html_with_glossary(self):
        filename = "tag_nextthought_com_2011-10_IFSTA-HTML-sample_book_section_Book_Organization_and_Navigation_2.html"
        reader = HTMLReader(self.data_file(filename))
        html = HTMLSample()
        text = process_html_body(reader.element, html)
        assert_that(html.number_ntiglossary, is_(2))
        assert_that(len(html.glossaries), is_(2))
        assert_that(len(html.glossaries), is_(html.number_ntiglossary))
