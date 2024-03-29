#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import os

from hamcrest import is_
from hamcrest import none
from hamcrest import has_length
from hamcrest import assert_that

from nti.testing.matchers import provides

from nti.contentrendering import tociconsetter

from nti.contentrendering.interfaces import JobComponents
from nti.contentrendering.interfaces import IRenderedBookTransformer

from nti.contentrendering.tests import ContentrenderingLayerTest

from nti.contentrendering.utils import EmptyMockDocument
from nti.contentrendering.utils import NoPhantomRenderedBook


class TestTransforms(ContentrenderingLayerTest):

    def _chapters_of(self, book):
        return [
            x for x in book.toc.dom.getElementsByTagName("toc")[0].childNodes
            if x.nodeType == x.ELEMENT_NODE and x.localName == 'topic'
        ]

    def _assert_base_state(self, book):
        assert_that(self._chapters_of(book), has_length(2))
        assert_that(self._chapters_of(book)[0].getAttribute('icon'),
                    is_(''))
        assert_that(self._chapters_of(book)[0].getAttribute('label'),
                    is_('What is Biology?'))
        assert_that(self._chapters_of(book)[1].getAttribute('icon'),
                    is_('icons/chapters/Biology2.png'))

    def test_module_provides(self):
        assert_that(tociconsetter,
                    provides(IRenderedBookTransformer))

    def test_transforms_no_jobname(self):
        # With no jobname no icons are changed
        book = NoPhantomRenderedBook(EmptyMockDocument(),
                                     os.path.join(os.path.dirname(__file__),
                                                  'intro-biology-rendered-book'))
        self._assert_base_state(book)

        res, _ = tociconsetter.transform(book, save_toc=False)

        assert_that(res, is_(True))
        # No changes
        self._assert_base_state(book)

    def test_transforms_with_jobname_icon_intact(self):
        # With a jobname existing icons stay in place
        tex_doc = EmptyMockDocument()
        tex_doc.userdata['jobname'] = 'prealgebra'
        book = NoPhantomRenderedBook(tex_doc,
                                     os.path.join(os.path.dirname(__file__),
                                                  'intro-biology-rendered-book'))
        self._assert_base_state(book)

        res, _ = tociconsetter.transform(book, save_toc=False)

        assert_that(res, is_(True))
        # No changes
        self._assert_base_state(book)

    def test_transforms_with_jobname_on_disk_icon(self):
        # With a jobname, only topics with no icon that have an icon on disk
        # are set
        tex_doc = EmptyMockDocument()
        tex_doc.userdata['jobname'] = 'testing'
        context = JobComponents('testing')
        bio_dir = os.path.join(os.path.dirname(__file__),
                               'intro-biology-rendered-book')
        # First, make sure our filesystem matches our expectations
        assert_that(os.path.isfile(os.path.join(bio_dir, 'icons', 'chapters', 'C2.png')),
                    is_(True))
        assert_that(os.path.isfile(os.path.join(bio_dir, 'icons', 'chapters', 'C1.png')),
                    is_(False))
        book = NoPhantomRenderedBook(tex_doc,
                                     os.path.join(os.path.dirname(__file__),
                                                  'intro-biology-rendered-book'))
        self._assert_base_state(book)
        # Throw away the icon for C2
        self._chapters_of(book)[1].removeAttribute('icon')

        res, nodes = tociconsetter.transform(book, save_toc=False,
                                             context=context)

        assert_that(res, is_(True))
        # Only icons that exist are used
        assert_that(self._chapters_of(book)[0].getAttribute('icon'), is_(''))
        assert_that(self._chapters_of(book)[1].getAttribute('icon'),
                    is_('icons/chapters/C2.png'))
        assert_that(nodes[0].get_background_image(), is_(none()))
        assert_that(nodes[1].get_background_image(),
                    is_("background-image: url('images/chapters/C2.png')"))
