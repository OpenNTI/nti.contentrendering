#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import greater_than_or_equal_to

import os
import unittest

from shutil import copyfile

from nti.contentrendering.plastexpackages.extractors import _CourseExtractor
from nti.contentrendering.plastexpackages.extractors import _ContentUnitStatistics

from nti.contentrendering.plastexpackages.tests import ExtractorTestLayer

from nti.contentrendering.RenderedBook import EclipseTOC
from nti.contentrendering.resources import ResourceRenderer

from nti.contentrendering.tests import RenderContext
from nti.contentrendering.tests import simpleLatexDocumentText


class Book(object):
    toc = None
    document = None
    contentLocation = None


class TestContentUnitStatistics(unittest.TestCase):

    layer = ExtractorTestLayer

    def data_file(self, name):
        return os.path.join(os.path.dirname(__file__), 'data', name)

    def test_book_content_unit_statistics(self):

        name = 'sample_book_1.tex'
        with open(self.data_file(name)) as fp:
            book_string = fp.read()

        book = Book()

        with RenderContext(simpleLatexDocumentText(
                preludes=("\\usepackage{ntilatexmacros}",),
                bodies=(book_string, )),
                packages_on_texinputs=True) as ctx:
            book.document = ctx.dom
            book.contentLocation = ctx.docdir

            render = ResourceRenderer.createResourceRenderer('XHTML', None)
            render.render(ctx.dom)
            book.toc = EclipseTOC(os.path.join(ctx.docdir, 'eclipse-toc.xml'))
            ctx.dom.renderer = render

            ext = _CourseExtractor()
            ext.transform(book)

            stat = _ContentUnitStatistics(book)
            result = stat.transform(book)

            assert_that(stat.lang, is_('en'))

            level_0 = result['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = level_0['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:1']
            level_2_2 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:2']

            assert_that(len(level_0['Items']), is_(1))
            assert_that(len(level_1['Items']), is_(2))

            assert_that(level_2_1['NTIID'], 
                        is_(u'tag:nextthought.com,2011-10:testing-HTML-temp.section:1'))
            assert_that(level_2_1['number_of_words'], is_(42))
            assert_that(level_2_1['number_of_sentences'], is_(6))
            assert_that(level_2_1['number_of_paragraphs'], is_(1))

            assert_that(level_2_2['NTIID'],
                        is_(u'tag:nextthought.com,2011-10:testing-HTML-temp.section:2'))
            assert_that(level_2_2['number_of_words'], is_(86))
            assert_that(level_2_2['number_of_sentences'], is_(5))
            assert_that(level_2_2['number_of_paragraphs'], is_(2))

            check_number_of_words = level_2_1['number_of_words'] + level_2_2['number_of_words']
            assert_that(level_1['number_of_words'],
                        greater_than_or_equal_to(check_number_of_words))

            check_number_of_sentences = level_2_1['number_of_sentences'] + level_2_2['number_of_sentences']
            assert_that(level_1['number_of_sentences'], 
                        greater_than_or_equal_to(check_number_of_sentences))

            check_number_of_paragraphs = level_2_1['number_of_paragraphs'] + level_2_2['number_of_paragraphs']
            assert_that(level_1['number_of_paragraphs'], 
                        greater_than_or_equal_to(check_number_of_paragraphs))

            assert_that(level_1['number_of_unique_words'], 
                        greater_than_or_equal_to(level_2_1['number_of_unique_words']))
            assert_that(level_1['number_of_unique_words'], 
                        greater_than_or_equal_to(level_2_2['number_of_unique_words']))

            assert_that(level_1['number_of_chars'], greater_than_or_equal_to(level_1['number_of_non_whitespace_chars']))
            assert_that(level_1['number_of_non_whitespace_chars'], is_(605))
            assert_that(level_2_1['number_of_chars'], greater_than_or_equal_to(level_2_1['number_of_non_whitespace_chars']))
            assert_that(level_2_2['number_of_chars'], greater_than_or_equal_to(level_2_2['number_of_non_whitespace_chars']))

            avg_word_per_sentence = level_1['number_of_words']/level_1['number_of_sentences']
            assert_that(level_1['avg_word_per_sentence'], is_(avg_word_per_sentence))
            avg_word_per_paragraph = level_1['number_of_words']/level_1['number_of_paragraphs']
            assert_that(level_1['avg_word_per_paragraph'], is_(avg_word_per_paragraph))

            avg_word_per_sentence = level_2_1['number_of_words']/level_2_1['number_of_sentences']
            assert_that(level_2_1['avg_word_per_sentence'], is_(avg_word_per_sentence))
            avg_word_per_paragraph = level_2_1['number_of_words']/level_2_1['number_of_paragraphs']
            assert_that(level_2_1['avg_word_per_paragraph'], is_(avg_word_per_paragraph))

            avg_word_per_sentence = level_2_2['number_of_words']/level_2_2['number_of_sentences']
            assert_that(level_2_2['avg_word_per_sentence'], is_(avg_word_per_sentence))
            avg_word_per_paragraph = level_2_2['number_of_words']/level_2_2['number_of_paragraphs']
            assert_that(level_2_2['avg_word_per_paragraph'], is_(avg_word_per_paragraph))

            unique_percentage_of_words = level_1['number_of_unique_words']/level_1['number_of_words']
            assert_that(level_1['unique_percentage_of_words'], is_(unique_percentage_of_words))

            unique_percentage_of_words = level_2_1['number_of_unique_words']/level_2_1['number_of_words']
            assert_that(level_2_1['unique_percentage_of_words'], is_(unique_percentage_of_words))

            unique_percentage_of_words = level_2_2['number_of_unique_words']/level_2_2['number_of_words']
            assert_that(level_2_2['unique_percentage_of_words'], is_(unique_percentage_of_words))

            len_shortest_word = level_1['length_of_the_shortest_word']
            len_longest_word = level_1['length_of_the_longest_word']
            assert_that(len_shortest_word, is_(1))
            assert_that(len_longest_word, is_(11))

    def test_book_3_levels(self):

        name = 'sample_book_2.tex'
        with open(self.data_file(name)) as fp:
            book_string = fp.read()

        book = Book()

        with RenderContext(simpleLatexDocumentText(
                preludes=("\\usepackage{ntilatexmacros}",),
                bodies=(book_string, )),
                packages_on_texinputs=True) as ctx:
            book.document = ctx.dom
            book.contentLocation = ctx.docdir

            render = ResourceRenderer.createResourceRenderer('XHTML', None)
            render.render(ctx.dom)
            book.toc = EclipseTOC(os.path.join(ctx.docdir, 'eclipse-toc.xml'))
            ctx.dom.renderer = render

            ext = _CourseExtractor()
            ext.transform(book)

            stat = _ContentUnitStatistics(book)
            result = stat.transform(book)

            level_0 = result['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            chapter_1 = level_0['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            # section_1_1 = chapter_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:1_1']
            # section_1_2 = chapter_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:1_2']
            chapter_2 = level_0['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:2']
            # section_2_1 = chapter_2['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:2_1']
            # subsection_2_1_1 = section_2_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.subsection:2_2_1']
            # subsection_2_1_2 = section_2_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.subsection:2_2_2']
            # section_2_2 = chapter_2['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:2_2']

            assert_that(chapter_1, has_entries('NTIID', u'tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1',
                                               'Items',
                                               has_entries('tag:nextthought.com,2011-10:testing-HTML-temp.section:1_1',
                                                           has_entries('NTIID', u'tag:nextthought.com,2011-10:testing-HTML-temp.section:1_1',
                                                                       'number_of_paragraphs', 2,
                                                                       'number_of_sentences', 8),
                                                           'tag:nextthought.com,2011-10:testing-HTML-temp.section:1_2',
                                                           has_entries('NTIID', u'tag:nextthought.com,2011-10:testing-HTML-temp.section:1_2',
                                                                       'number_of_paragraphs', 1,
                                                                       'number_of_sentences', 2
                                                                       )
                                                           )
                                               )
                        )
            # since this render split-level = 1, then subsection does not have
            # its own html
            assert_that(chapter_2, has_entries('NTIID', u'tag:nextthought.com,2011-10:testing-HTML-temp.chapter:2',
                                               'Items',
                                               has_entries('tag:nextthought.com,2011-10:testing-HTML-temp.section:2_1',
                                                           has_entries('NTIID', u'tag:nextthought.com,2011-10:testing-HTML-temp.section:2_1',
                                                                       'number_of_paragraphs', 3,
                                                                       'number_of_sentences', 8
                                                                       ),
                                                           'tag:nextthought.com,2011-10:testing-HTML-temp.section:2_2',
                                                           has_entries('NTIID', u'tag:nextthought.com,2011-10:testing-HTML-temp.section:2_2',
                                                                       'number_of_paragraphs', 1,
                                                                       'number_of_sentences', 4
                                                                       )
                                                           )
                                               )
                        )

            assert_that(stat.lang, is_('en'))
    
    def test_book_with_table_sidebar_ntiglossary(self):

        name = 'sample_book_3.tex'
        with open(self.data_file(name)) as fp:
            book_string = fp.read()

        book = Book()

        with RenderContext(simpleLatexDocumentText(
                preludes=("\\usepackage{ntilatexmacros}",),
                bodies=(book_string, )),
                packages_on_texinputs=True) as ctx:
            book.document = ctx.dom
            book.contentLocation = ctx.docdir

            render = ResourceRenderer.createResourceRenderer('XHTML', None)
            render.render(ctx.dom)
            book.toc = EclipseTOC(os.path.join(ctx.docdir, 'eclipse-toc.xml'))
            ctx.dom.renderer = render

            ext = _CourseExtractor()
            ext.transform(book)

            stat = _ContentUnitStatistics(book)
            result = stat.transform(book)

            level_0 = result['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = level_0['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:1']
            level_2_2 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:2']

            assert_that(level_1['number_of_table'], is_(1))
            assert_that(level_2_1['number_of_table'], is_(1))
            assert_that(level_2_2['number_of_table'], is_(0))

            assert_that(level_1['number_of_sidebar'], is_(1))
            assert_that(level_2_1['number_of_sidebar'], is_(0))
            assert_that(level_2_2['number_of_sidebar'], is_(1))

            assert_that(level_1['number_of_ntiglossary'], is_(1))
            assert_that(level_2_1['number_of_ntiglossary'], is_(0))
            assert_that(level_2_2['number_of_ntiglossary'], is_(1))

    def test_book_with_table_sidebar_ntiglossary(self):

        name = 'sample_book_4.tex'
        with open(self.data_file(name)) as fp:
            book_string = fp.read()

        book = Book()

        with RenderContext(simpleLatexDocumentText(
                preludes=("\\usepackage{ntilatexmacros}",),
                bodies=(book_string, )),
                packages_on_texinputs=True) as ctx:
            book.document = ctx.dom
            book.contentLocation = ctx.docdir

            render = ResourceRenderer.createResourceRenderer('XHTML', None)
            render.render(ctx.dom)
            book.toc = EclipseTOC(os.path.join(ctx.docdir, 'eclipse-toc.xml'))
            ctx.dom.renderer = render

            ext = _CourseExtractor()
            ext.transform(book)

            stat = _ContentUnitStatistics(book)
            result = stat.transform(book) 

            level_0 = result['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = level_0['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:1']
            level_2_2 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:2']

            assert_that(level_1['number_of_unordered_list'], is_(1))
            assert_that(level_2_1['number_of_unordered_list'], is_(1))
            assert_that(level_2_2['number_of_unordered_list'], is_(0))

            assert_that(level_1['number_of_ordered_list'], is_(1))
            assert_that(level_2_1['number_of_ordered_list'], is_(0))
            assert_that(level_2_2['number_of_ordered_list'], is_(1))

            assert_that(level_1['number_of_sentences'], is_(3))
            assert_that(level_2_1['number_of_sentences'], is_(1))
            assert_that(level_2_2['number_of_sentences'], is_(1))

            assert_that(level_1['number_of_paragraphs'], is_(3))
            assert_that(level_2_1['number_of_paragraphs'], is_(1))
            assert_that(level_2_2['number_of_paragraphs'], is_(1))