#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import os
import shutil
import tempfile

from hamcrest import is_
from hamcrest import assert_that
from hamcrest import contains_string

from nti.contentrendering import html5cachefile

from nti.contentrendering.tests import ContentrenderingLayerTest


class TestHTML5CacheFile(ContentrenderingLayerTest):

    def setUp(self):
        super(TestHTML5CacheFile, self).setUp()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_cachefile(self):
        source_path = os.path.join(os.path.dirname(__file__),
                                   'intro-biology-rendered-book')
        path = html5cachefile.main(source_path, self.temp_dir)
        assert_that(os.path.exists(path), is_(True))
        with open(path, "rb") as fp:
            content = fp.read()
        assert_that(content, contains_string('CACHE MANIFEST'))
        assert_that(content, contains_string('icons/chapters/Biology2.png'))
        assert_that(content, contains_string('index.html'))
        assert_that(content, contains_string('thumbnails/index.png'))
