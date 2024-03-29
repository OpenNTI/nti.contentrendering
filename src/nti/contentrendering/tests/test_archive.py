#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import os
import shutil
import tempfile

from hamcrest import none
from hamcrest import is_in
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that

from zope import component

from nti.contentrendering import archive
from nti.contentrendering import interfaces

from nti.contentrendering.tests import ContentrenderingLayerTest


class TestArchive(ContentrenderingLayerTest):

    def setUp(self):
        super(TestArchive, self).setUp()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_utility(self):
        u = component.queryUtility(interfaces.IRenderedBookArchiver)
        assert_that(u, is_not(none()))

    def test_archive_biology(self):
        source_path = os.path.join(os.path.dirname(__file__),
                                   'intro-biology-rendered-book')
        added = archive._archive(source_path, self.temp_dir)
        assert_that(added, has_length(40))
        assert_that('intro-biology-rendered-book/eclipse-toc.xml', 
					is_in(added))
        assert_that('intro-biology-rendered-book/icons/chapters/C2.png', 
					is_in(added))
        assert_that('intro-biology-rendered-book/images/chapters/C2.png', 
					is_in(added))
        assert_that('intro-biology-rendered-book/js/worksheet.js',
					is_in(added))
        assert_that('intro-biology-rendered-book/styles/prealgebra.css', 
					is_in(added))
        assert_that('intro-biology-rendered-book/.version', is_in(added))
