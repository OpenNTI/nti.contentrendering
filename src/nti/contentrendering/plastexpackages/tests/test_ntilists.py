#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import unittest

from nti.contentrendering.plastexpackages.ntilists import ntienumerate

from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import buildDomFromString as _buildDomFromString


def _simpleLatexDocument(maths):
    return simpleLatexDocumentText(
                  preludes=(br'\usepackage{nti.contentrendering.plastexpackages.ntilists}',),
                            bodies=maths)


class TestNTILists(unittest.TestCase):

    def test_ntienumerate(self):
        example = br"""
            \begin{ntienumerate}
                \item[0] Ichigo
                \item[1] Aizen
                \item[2] Zaraki
            \end{ntienumerate}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))

        # Check that the DOM has the expected structure
        assert_that(dom.getElementsByTagName('ntienumerate'), has_length(1))
        assert_that(dom.getElementsByTagName('ntienumerate')[0], 
					is_(ntienumerate))

        # Check that the ntienumerate object has the expected children
        elem = dom.getElementsByTagName('ntienumerate')[0]
        assert_that(elem, has_property('childNodes', has_length(3)))
        assert_that(elem.childNodes[0], has_property('tagName', is_('item')))
        assert_that(elem.childNodes[1], has_property('tagName', is_('item')))
        assert_that(elem.childNodes[2], has_property('tagName', is_('item')))
