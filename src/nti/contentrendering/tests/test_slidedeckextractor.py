#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import has_length
from hamcrest import assert_that

from nti.testing.matchers import verifiably_provides

import os
import shutil
import tempfile

import fudge

from zope import component

from nti.contentrendering import slidedeckextractor

from nti.contentrendering.interfaces import IRenderedBookExtractor

from nti.contentrendering.tests import ContentrenderingLayerTest


class TestSlideDeckExtractor(ContentrenderingLayerTest):

    def setUp(self):
        super(TestSlideDeckExtractor, self).setUp()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_utility(self):
        u = component.getUtility(IRenderedBookExtractor,
                                 name="060.SlideDeckExtractor")
        assert_that(u, verifiably_provides(IRenderedBookExtractor))

    @fudge.patch('nti.contentrendering.RenderedBook.EclipseTOC.save')
    def test_extractor_prmia(self, fake_save):
        fake_save.is_callable()

        source_path = os.path.join(os.path.dirname(__file__),
                                   'prmia_riskcourse')
        extracted = slidedeckextractor.extract(source_path, self.temp_dir)
        assert_that(extracted, has_length(6))
