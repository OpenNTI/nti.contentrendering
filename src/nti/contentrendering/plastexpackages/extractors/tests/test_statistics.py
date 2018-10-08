#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import greater_than_or_equal_to
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

class TestContentUnitStatistics(unittest.TestCase):

    layer = ExtractorTestLayer

    def data_file(self, name):
        return os.path.join(os.path.dirname(__file__), 'data', name)

    def test_book_content_unit_statistics(self):

        name = 'sample_book_1.tex'
        with open(self.data_file(name)) as fp:
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
            
            node = book.toc.dom.documentElement

            stat = _ContentUnitStatistics(book)
            result = stat.transform(book)

            assert_that(stat.lang, is_('en'))

            level_0 = result['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = level_0['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:1']
            level_2_2 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:2']

            assert_that(len(level_0['Items']), is_(1))
            assert_that(len(level_1['Items']), is_(2))
            
            assert_that(level_2_1['NTIID'], is_(u'tag:nextthought.com,2011-10:testing-HTML-temp.section:1'))
            assert_that(level_2_1['data']['number_of_words'], is_(42))
            assert_that(level_2_1['data']['number_of_sentences'], is_(6))
            assert_that(level_2_1['data']['number_of_paragraphs'], is_(1))

            assert_that(level_2_2['NTIID'], is_(u'tag:nextthought.com,2011-10:testing-HTML-temp.section:2'))
            assert_that(level_2_2['data']['number_of_words'], is_(86))
            assert_that(level_2_2['data']['number_of_sentences'], is_(5))
            assert_that(level_2_2['data']['number_of_paragraphs'], is_(2))

        
            check_number_of_words = level_2_1['data']['number_of_words'] + level_2_2['data']['number_of_words']
            assert_that(level_1['data']['number_of_words'], greater_than_or_equal_to(check_number_of_words))

            check_number_of_sentences = level_2_1['data']['number_of_sentences'] + level_2_2['data']['number_of_sentences']
            assert_that(level_1['data']['number_of_sentences'], greater_than_or_equal_to(check_number_of_sentences))

            check_number_of_paragraphs = level_2_1['data']['number_of_paragraphs'] + level_2_2['data']['number_of_paragraphs'] 
            assert_that(level_1['data']['number_of_paragraphs'], greater_than_or_equal_to(check_number_of_paragraphs))
            
            