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
            stat.transform(book)
            result = stat.index

            assert_that(stat.lang, is_('en'))

            level_0 = result['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:1']
            level_2_2 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:2']

            assert_that(level_2_1['word_count'], is_(42))
            assert_that(level_2_1['sentence_count'], is_(6))
            assert_that(level_2_1['paragraph_count'], is_(1))

            assert_that(level_2_2['word_count'], is_(86))
            assert_that(level_2_2['sentence_count'], is_(5))
            assert_that(level_2_2['paragraph_count'], is_(2))

            check_number_of_words = level_2_1['word_count'] + level_2_2['word_count']
            assert_that(level_1['word_count'],
                        greater_than_or_equal_to(check_number_of_words))

            check_number_of_sentences = level_2_1['sentence_count'] + level_2_2['sentence_count']
            assert_that(level_1['sentence_count'],
                        greater_than_or_equal_to(check_number_of_sentences))

            check_number_of_paragraphs = level_2_1['paragraph_count'] + level_2_2['paragraph_count']
            assert_that(level_1['paragraph_count'],
                        greater_than_or_equal_to(check_number_of_paragraphs))

            assert_that(level_1['unique_word_count'],
                        greater_than_or_equal_to(level_2_1['unique_word_count']))
            assert_that(level_1['unique_word_count'],
                        greater_than_or_equal_to(level_2_2['unique_word_count']))

            assert_that(level_1['char_count'], greater_than_or_equal_to(level_1['non_whitespace_char_count']))
            assert_that(level_1['non_whitespace_char_count'], is_(605))
            assert_that(level_2_1['char_count'], greater_than_or_equal_to(level_2_1['non_whitespace_char_count']))
            assert_that(level_2_2['char_count'], greater_than_or_equal_to(level_2_2['non_whitespace_char_count']))

            avg_word_per_sentence = level_1['word_count'] / level_1['sentence_count']
            assert_that(level_1['avg_word_per_sentence'], is_(avg_word_per_sentence))
            avg_word_per_paragraph = level_1['word_count'] / level_1['paragraph_count']
            assert_that(level_1['avg_word_per_paragraph'], is_(avg_word_per_paragraph))

            avg_word_per_sentence = level_2_1['word_count'] / level_2_1['sentence_count']
            assert_that(level_2_1['avg_word_per_sentence'], is_(avg_word_per_sentence))
            avg_word_per_paragraph = level_2_1['word_count'] / level_2_1['paragraph_count']
            assert_that(level_2_1['avg_word_per_paragraph'], is_(avg_word_per_paragraph))

            avg_word_per_sentence = level_2_2['word_count'] / level_2_2['sentence_count']
            assert_that(level_2_2['avg_word_per_sentence'], is_(avg_word_per_sentence))
            avg_word_per_paragraph = level_2_2['word_count'] / level_2_2['paragraph_count']
            assert_that(level_2_2['avg_word_per_paragraph'], is_(avg_word_per_paragraph))

            unique_percentage_of_words = level_1['unique_word_count'] / level_1['word_count']
            assert_that(level_1['unique_percentage_of_word_count'], is_(unique_percentage_of_words))

            unique_percentage_of_words = level_2_1['unique_word_count'] / level_2_1['word_count']
            assert_that(level_2_1['unique_percentage_of_word_count'], is_(unique_percentage_of_words))

            unique_percentage_of_words = level_2_2['unique_word_count'] / level_2_2['word_count']
            assert_that(level_2_2['unique_percentage_of_word_count'], is_(unique_percentage_of_words))

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
            stat.transform(book)
            result = stat.index

            level_0 = result['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            chapter_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            chapter_2 = result['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:2']

            word_count = chapter_1['word_count'] + chapter_2['word_count']
            assert_that(level_0['word_count'], is_(word_count))

            total_word_count = chapter_1['total_word_count'] + chapter_2['total_word_count']
            assert_that(level_0['total_word_count'], is_(word_count))

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
            stat.transform(book)
            result = stat.index

            level_0 = result['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:1']
            level_2_2 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:2']

            assert_that(level_1, has_entries('BlockElementDetails',
                                             has_entries('table',
                                                         has_entries('count', is_(1))
                                                         )
                                             )
                        )
            assert_that(level_2_1, has_entries('BlockElementDetails',
                                               has_entries('table',
                                                           has_entries('count', is_(1))
                                                           )
                                               )
                        )
            assert_that(level_2_2, has_entries('BlockElementDetails',
                                               has_entries('table',
                                                           has_entries('count', is_(0))
                                                           )
                                               )
                        )

            assert_that(level_1, has_entries('BlockElementDetails',
                                             has_entries('glossary',
                                                         has_entries('count', is_(1))
                                                         )
                                             )
                        )
            assert_that(level_2_1, has_entries('BlockElementDetails',
                                               has_entries('glossary',
                                                           has_entries('count', is_(0))
                                                           )
                                               )
                        )
            assert_that(level_2_2, has_entries('BlockElementDetails',
                                               has_entries('glossary',
                                                           has_entries('count', is_(1))
                                                           )
                                               )
                        )

    def test_book_with_lists(self):

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
            stat.transform(book)
            result = stat.index

            level_0 = result['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:1']
            level_2_2 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:2']

            assert_that(level_1['sentence_count'], is_(5))
            # it count the list as one sentence
            assert_that(level_2_1['sentence_count'], is_(2))
            # it count the list as one sentence
            assert_that(level_2_2['sentence_count'], is_(2))

            assert_that(level_1['paragraph_count'], is_(3))
            assert_that(level_2_1['paragraph_count'], is_(1))
            assert_that(level_2_2['paragraph_count'], is_(1))

    def test_book_with_sidebar_option(self):

        name = 'sample_book_7.tex'
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
            stat.transform(book)
            result = stat.index

            level_0 = result['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:1']
            level_2_2 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:2']

            # number of sentences = 5 because the title = 'WARNING!' if the title = 'WARNING' then the number_of_sentences = 4
            assert_that(level_2_1, has_entries('BlockElementDetails',
                                               has_entries('sidebar_warning',
                                                           has_entries('sentence_count', 5,
                                                                       'word_count', 24,
                                                                       'char_count', 175,
                                                                       'non_whitespace_char_count', 150)
                                                           )
                                               )
                        )

            assert_that(level_2_1, has_entries('BlockElementDetails',
                                               has_entries('sidebar_caution',
                                                           has_entries('sentence_count', 2,
                                                                       'word_count', 21,
                                                                       'char_count', 137,
                                                                       'non_whitespace_char_count', 115)
                                                           )
                                               )
                        )

            assert_that(level_2_2, has_entries('BlockElementDetails',
                                               has_entries('sidebar_note',
                                                           has_entries('sentence_count', 1,
                                                                       'word_count', 10,
                                                                       'char_count', 72,
                                                                       'non_whitespace_char_count', 61)
                                                           )
                                               )
                        )

    def test_book_with_equation(self):
        name = 'sample_book_8.tex'
        with open(self.data_file(name)) as fp:
            book_string = fp.read()

        book = Book()

        with RenderContext(simpleLatexDocumentText(
                preludes=("\\usepackage{ntilatexmacros}",
                          "\\usepackage{amsmath}"),
                bodies=(book_string, )),
                packages_on_texinputs=True) as ctx:
            book.document = ctx.dom
            book.contentLocation = ctx.docdir

            ctx.render()
            book.toc = EclipseTOC(os.path.join(ctx.docdir, 'eclipse-toc.xml'))

            stat = _ContentUnitStatistics(book)
            stat.transform(book)
            result = stat.index

            level_0 = result['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:1']
            level_2_2 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:2']

    def test_book_with_expected_consumption_time(self):
        name = 'sample_book_10.tex'
        with open(self.data_file(name)) as fp:
            book_string = fp.read()

        book = Book()

        with RenderContext(simpleLatexDocumentText(
                preludes=("\\usepackage{ntilatexmacros}",),
                bodies=(book_string, )),
                packages_on_texinputs=True) as ctx:
            book.document = ctx.dom
            book.contentLocation = ctx.docdir

            ctx.render()
            book.toc = EclipseTOC(os.path.join(ctx.docdir, 'eclipse-toc.xml'))

            stat = _ContentUnitStatistics(book)
            stat.transform(book)
            result = stat.index
            level_0 = result['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:System_Requirements']
            level_2_2 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:General_Features']

            assert_that(level_1['expected_consumption_time'], is_(600.0))
            assert_that(level_2_1['expected_consumption_time'], is_(300.0))
            assert_that(level_2_2['expected_consumption_time'], is_(300.0))

    def test_book_with_expected_consumption_time_2(self):
        name = 'sample_book_11.tex'
        with open(self.data_file(name)) as fp:
            book_string = fp.read()

        book = Book()

        with RenderContext(simpleLatexDocumentText(
                preludes=("\\usepackage{ntilatexmacros}",),
                bodies=(book_string, )),
                packages_on_texinputs=True) as ctx:
            book.document = ctx.dom
            book.contentLocation = ctx.docdir

            ctx.render()
            book.toc = EclipseTOC(os.path.join(ctx.docdir, 'eclipse-toc.xml'))

            stat = _ContentUnitStatistics(book)
            stat.transform(book)
            result = stat.index
            level_0 = result['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:System_Requirements']
            level_2_2 = result['tag:nextthought.com,2011-10:testing-HTML-temp.section:General_Features']
            assert_that(level_1['expected_consumption_time'], is_(100.0))
            assert_that(level_2_1['expected_consumption_time'], is_(None))
            assert_that(level_2_2['expected_consumption_time'], is_(None))
