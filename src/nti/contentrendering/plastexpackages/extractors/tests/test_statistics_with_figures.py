#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that
from hamcrest import is_

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

            assert_that(level_1['number_of_figures'], is_(2))
            assert_that(level_2_1['number_of_figures'], is_(1))
            assert_that(level_2_2['number_of_figures'], is_(1))
