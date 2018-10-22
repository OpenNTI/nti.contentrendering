#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that
from hamcrest import is_
from hamcrest import has_entries

import io
import os
import unittest

from zope import interface

import fudge

from nti.contentrendering import _programs

from nti.contentrendering import interfaces as cdr_interfaces

from nti.contentrendering.resources import ResourceRenderer
from nti.contentrendering.resources.interfaces import ConverterUnusableError

from nti.contentrendering.tests import RenderContext
from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import buildDomFromString as _buildDomFromString

from nti.contentrendering.plastexpackages.tests import ExtractorTestLayer

from nti.contentrendering.plastexpackages.extractors import _ContentUnitStatistics

from nti.contentrendering.RenderedBook import EclipseTOC

class Book(object):
    toc = None
    document = None
    contentLocation = None

def _simpleLatexDocument(maths):
    return simpleLatexDocumentText( preludes=(br'\usepackage{nti.contentrendering.plastexpackages.ntilatexmacros}',
                                              br'\usepackage{graphicx}'),
                                    bodies=maths )

@interface.implementer(cdr_interfaces.IRenderedBook)
class _MockRenderedBook(object):
    document = None
    contentLocation = None

class TestFigure(unittest.TestCase):
    layer = ExtractorTestLayer
    toc = None

    def setUp(self):
        super(TestFigure,self).setUp()
        self.toc = None

    def data_file(self, name):
        return os.path.join(os.path.dirname(__file__), 'data', name)

    def test_two_figures(self, do_images=True):
        name = 'sample_book_5.tex'
        with open(self.data_file(name)) as fp:
            book_string = fp.read()


        book = Book()

        with RenderContext(_simpleLatexDocument( (book_string,) ), 
                           output_encoding='utf-8',
                           files=(os.path.join( os.path.dirname(__file__ ), 'test.png' ),),
                           packages_on_texinputs=True) as ctx:
            book.document = ctx.dom
            book.contentLocation = ctx.docdir
            dom  = ctx.dom
            dom.getElementsByTagName( 'document' )[0].filenameoverride = 'index'
            res_db = None
            if do_images:
                from nti.contentrendering import nti_render
                try:
                    res_db = nti_render.generateImages( dom )
                except ConverterUnusableError as e:
                    raise unittest.SkipTest(e)

            render = ResourceRenderer.createResourceRenderer('XHTML', res_db)
            render.importDirectory( os.path.join( os.path.dirname(__file__), '..' ) )
            render.render( dom )
            
            book.toc = EclipseTOC(os.path.join(ctx.docdir, 'eclipse-toc.xml'))

            stat = _ContentUnitStatistics(book)
            result = stat.transform(book) 

            level_0 = result['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = level_0['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:1']
            level_2_2 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:2']

            
            assert_that(level_1, has_entries('BlockElementDetails', 
                                              has_entries('figure', 
                                                           has_entries('count', is_(2),
                                                                       'sentence_count', is_(3),
                                                                       'word_count', is_(24),
                                                                       'char_count', is_(160),
                                                                       'non_whitespace_char_count',is_(138)
                                                                       )
                                                           )
                                              )
            )

            #'Figure 1.1: Post and beam framing is heavier than light-frame construction but lighter than timber construction. Courtesy of Ed Prendergast.'
            assert_that(level_2_1, has_entries('BlockElementDetails', 
                                              has_entries('figure', 
                                                           has_entries('count', is_(1),
                                                                       'sentence_count', is_(2),
                                                                       'word_count', is_(20),
                                                                       'char_count', is_(140),
                                                                       'non_whitespace_char_count',is_(121)
                                                                       )
                                                           )
                                              )
            )

            #'Figure 1.2: Figure 2'
            assert_that(level_2_2, has_entries('BlockElementDetails', 
                                              has_entries('figure', 
                                                           has_entries('count', is_(1),
                                                                       'sentence_count', is_(1),
                                                                       'word_count', is_(4),
                                                                       'char_count', is_(20),
                                                                       'non_whitespace_char_count',is_(17)
                                                                       )
                                                           )
                                              )
            )
    
    def test_figure_in_sidebar(self, do_images=True):
        name = 'sample_book_6.tex'
        with open(self.data_file(name)) as fp:
            book_string = fp.read()


        book = Book()

        with RenderContext(_simpleLatexDocument( (book_string,) ), 
                           output_encoding='utf-8',
                           files=(os.path.join( os.path.dirname(__file__ ), 'test.png' ),),
                           packages_on_texinputs=True) as ctx:
            book.document = ctx.dom
            book.contentLocation = ctx.docdir
            dom  = ctx.dom
            dom.getElementsByTagName( 'document' )[0].filenameoverride = 'index'
            res_db = None
            if do_images:
                from nti.contentrendering import nti_render
                try:
                    res_db = nti_render.generateImages( dom )
                except ConverterUnusableError as e:
                    raise unittest.SkipTest(e)

            render = ResourceRenderer.createResourceRenderer('XHTML', res_db)
            render.importDirectory( os.path.join( os.path.dirname(__file__), '..' ) )
            render.render( dom )
            
            book.toc = EclipseTOC(os.path.join(ctx.docdir, 'eclipse-toc.xml'))

            stat = _ContentUnitStatistics(book)
            result = stat.transform(book) 

            level_0 = result['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = level_0['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:1']
            level_2_2 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:2']

            assert_that(level_1, has_entries('BlockElementDetails', 
                                              has_entries('figure', 
                                                           has_entries('count', is_(2))
                                                           )
                                              )
            )

            assert_that(level_2_1, has_entries('BlockElementDetails', 
                                              has_entries('figure', 
                                                           has_entries('count', is_(1))
                                                           )
                                              )
            )

            assert_that(level_2_2, has_entries('BlockElementDetails', 
                                              has_entries('figure', 
                                                           has_entries('count', is_(1))
                                                           )
                                              )
            )

    def test_non_figure_image(self, do_images=True):
        name = 'sample_book_9.tex'
        with open(self.data_file(name)) as fp:
            book_string = fp.read()


        book = Book()

        with RenderContext(_simpleLatexDocument( (book_string,) ), 
                           output_encoding='utf-8',
                           files=(os.path.join( os.path.dirname(__file__ ), 'test.png' ),),
                           packages_on_texinputs=True) as ctx:
            book.document = ctx.dom
            book.contentLocation = ctx.docdir
            dom  = ctx.dom
            dom.getElementsByTagName( 'document' )[0].filenameoverride = 'index'
            res_db = None
            if do_images:
                from nti.contentrendering import nti_render
                try:
                    res_db = nti_render.generateImages( dom )
                except ConverterUnusableError as e:
                    raise unittest.SkipTest(e)

            render = ResourceRenderer.createResourceRenderer('XHTML', res_db)
            render.importDirectory( os.path.join( os.path.dirname(__file__), '..' ) )
            render.render( dom )
            
            book.toc = EclipseTOC(os.path.join(ctx.docdir, 'eclipse-toc.xml'))

            stat = _ContentUnitStatistics(book)
            result = stat.transform(book) 

            level_0 = result['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = level_0['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:1']
            level_2_2 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:2']

            assert_that(level_1, has_entries('BlockElementDetails', 
                                              has_entries('figure', 
                                                           has_entries('count', is_(2))
                                                           )
                                              )
            )

            assert_that(level_2_1, has_entries('BlockElementDetails', 
                                              has_entries('figure', 
                                                           has_entries('count', is_(1))
                                                           )
                                              )
            )

            assert_that(level_2_2, has_entries('BlockElementDetails', 
                                              has_entries('figure', 
                                                           has_entries('count', is_(1))
                                                           )
                                              )
            )

            assert_that(level_1, has_entries('non_figure_image_count', is_(1)))

    def test_total_stats(self, do_images=True):
        name = 'sample_book_9.tex'
        with open(self.data_file(name)) as fp:
            book_string = fp.read()


        book = Book()

        with RenderContext(_simpleLatexDocument( (book_string,) ), 
                           output_encoding='utf-8',
                           files=(os.path.join( os.path.dirname(__file__ ), 'test.png' ),),
                           packages_on_texinputs=True) as ctx:
            book.document = ctx.dom
            book.contentLocation = ctx.docdir
            dom  = ctx.dom
            dom.getElementsByTagName( 'document' )[0].filenameoverride = 'index'
            res_db = None
            if do_images:
                from nti.contentrendering import nti_render
                try:
                    res_db = nti_render.generateImages( dom )
                except ConverterUnusableError as e:
                    raise unittest.SkipTest(e)

            render = ResourceRenderer.createResourceRenderer('XHTML', res_db)
            render.importDirectory( os.path.join( os.path.dirname(__file__), '..' ) )
            render.render( dom )
            
            book.toc = EclipseTOC(os.path.join(ctx.docdir, 'eclipse-toc.xml'))

            stat = _ContentUnitStatistics(book)
            result = stat.transform(book) 

            level_0 = result['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.0']
            level_1 = level_0['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.chapter:1']
            level_2_1 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:1']
            level_2_2 = level_1['Items']['tag:nextthought.com,2011-10:testing-HTML-temp.section:2']

            level_0_total_word_count = level_0['word_count'] + level_0['BlockElementDetails']['table']['word_count'] \
                                       + level_0['BlockElementDetails']['figure']['word_count'] \
                                       + level_0['BlockElementDetails']['sidebar_caution']['word_count'] \
                                       + level_0['BlockElementDetails']['sidebar_warning']['word_count'] \
                                       + level_0['BlockElementDetails']['sidebar_note']['word_count'] \
                                       + level_0['BlockElementDetails']['glossary']['word_count']
            assert_that(level_0['total_word_count'], is_(level_0_total_word_count))

            level_1_total_word_count = level_1['word_count'] + level_1['BlockElementDetails']['table']['word_count'] \
                                       + level_1['BlockElementDetails']['figure']['word_count'] \
                                       + level_1['BlockElementDetails']['sidebar_caution']['word_count'] \
                                       + level_1['BlockElementDetails']['sidebar_warning']['word_count'] \
                                       + level_1['BlockElementDetails']['sidebar_note']['word_count'] \
                                       + level_1['BlockElementDetails']['glossary']['word_count']
            assert_that(level_1['total_word_count'], is_(level_1_total_word_count))

            level_2_1_total_word_count = level_2_1['word_count'] + level_2_1['BlockElementDetails']['table']['word_count'] \
                                       + level_2_1['BlockElementDetails']['figure']['word_count'] \
                                       + level_2_1['BlockElementDetails']['sidebar_caution']['word_count'] \
                                       + level_2_1['BlockElementDetails']['sidebar_warning']['word_count'] \
                                       + level_2_1['BlockElementDetails']['sidebar_note']['word_count'] \
                                       + level_2_1['BlockElementDetails']['glossary']['word_count']
            assert_that(level_2_1['total_word_count'], is_(level_2_1_total_word_count))

            level_2_2_total_word_count = level_2_2['word_count'] + level_2_2['BlockElementDetails']['table']['word_count'] \
                                       + level_2_2['BlockElementDetails']['figure']['word_count'] \
                                       + level_2_2['BlockElementDetails']['sidebar_caution']['word_count'] \
                                       + level_2_2['BlockElementDetails']['sidebar_warning']['word_count'] \
                                       + level_2_2['BlockElementDetails']['sidebar_note']['word_count'] \
                                       + level_2_2['BlockElementDetails']['glossary']['word_count']
            assert_that(level_2_2['total_word_count'], is_(level_2_2_total_word_count))
