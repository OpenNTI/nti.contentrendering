#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that

from nti.testing.matchers import verifiably_provides

import shutil
import tempfile

from zope import component

from nti.contentrendering.interfaces import IRenderedBookExtractor

from nti.contentrendering.realpageextractor import transform

from nti.contentrendering.RenderedBook import RenderedBook

from nti.contentrendering.tests import RenderContext
from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import ContentrenderingLayerTest

preludes = (
    '\\usepackage{nti.contentrendering.plastexpackages.ntilatexmacros}',
)


class TestRealPageExtractor(ContentrenderingLayerTest):

    def setUp(self):
        super(TestRealPageExtractor, self).setUp()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_utility(self):
        u = component.queryUtility(IRenderedBookExtractor,
                                   name="055.RealPageNumberExtractor")
        assert_that(u, verifiably_provides(IRenderedBookExtractor))

    def test_extractor_realpagenumber(self):
        source_str = r"""
        \realpagenumber{}
        \chapter{A}
        \realpagenumber{}
        \section{AA}
        \realpagenumber{}
        \realpagenumber{}
        \section{AB}
        \realpagenumber{}
        \chapter{B}
        \realpagenumber{}
        \realpagenumber{}
        \section{BA}
        \realpagenumber{}
        \realpagenumber{}
        \section{BB}
        \realpagenumber{}
        \realpagenumber{}
        \section{BC}
        \realpagenumber{}
        \realpagenumber{}
        """

        with RenderContext(simpleLatexDocumentText(preludes=preludes,
                                                   bodies=(source_str,))) as ref_context:
            ref_context.render()
            book = RenderedBook(ref_context.dom, ref_context.docdir)
            index = transform(book)
            assert_that(index['real-pages']['11']['NTIID'],
                        is_('tag:nextthought.com,2011-10:testing-HTML-temp.bb'))
            assert_that(index['real-pages']['11']['NavNTIID'],
                        is_('tag:nextthought.com,2011-10:testing-HTML-temp.bb'))
            assert_that(index['NTIIDs']['tag:nextthought.com,2011-10:testing-HTML-temp.bb'],
                        has_length(3))
