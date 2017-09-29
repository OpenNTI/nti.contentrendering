#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import os
import shutil
import tempfile

from zope import component

from nti.contentrendering import interfaces
from nti.contentrendering import realpageextractor

from nti.contentrendering.RenderedBook import RenderedBook

from nti.contentrendering.tests import ContentrenderingLayerTest
from nti.contentrendering.tests import RenderContext
from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import buildDomFromString as _buildDomFromString
from nti.testing.matchers import verifiably_provides


import fudge
from hamcrest import assert_that
from hamcrest import has_length
from hamcrest import is_

preludes = ('\\usepackage{nti.contentrendering.plastexpackages.ntilatexmacros}',)

class TestRealPageExtractor(ContentrenderingLayerTest):

    def setUp(self):
        super(TestRealPageExtractor, self).setUp()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_utility(self):
        u = component.getUtility(interfaces.IRenderedBookExtractor, name="055.RealPageNumberExtractor")
        assert_that(u, verifiably_provides(interfaces.IRenderedBookExtractor) )

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
            index = realpageextractor.transform(book)
            assert_that(index['real-pages']['11'], is_('tag:nextthought.com,2011-10:testing-HTML-temp.bb'))
            assert_that(index['NTIIDs']['tag:nextthought.com,2011-10:testing-HTML-temp.bb'], has_length(3))
