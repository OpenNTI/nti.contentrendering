#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that

import unittest

from nti.contentrendering.plastexpackages.ntilatexmacros import realpagenumber

from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import buildDomFromString as _buildDomFromString


def _simpleLatexDocument(maths):
    return simpleLatexDocumentText(
                  preludes=(r'\usepackage{nti.contentrendering.plastexpackages.ntilatexmacros}',),
                            bodies=maths)


class TestRealPageNumber(unittest.TestCase):

    def test_autoincrement(self):
        example = r"""
            \realpagenumber{}
            \realpagenumber{}
            \realpagenumber{}
            \realpagenumber{}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))

        # Check that the DOM has the expected structure
        elems = dom.getElementsByTagName('realpagenumber')
        assert_that(elems, has_length(4))
        assert_that(elems[0], is_(realpagenumber))

        # Check that the ntienumerate object has the expected children
        assert_that(elems[0].pagenumber, is_(1))
        assert_that(elems[1].pagenumber, is_(2))
        assert_that(elems[2].pagenumber, is_(3))
        assert_that(elems[3].pagenumber, is_(4))

    def test_manualnumber(self):
        example = r"""
            \realpagenumber{A-1}
            \realpagenumber{A-2}
            \realpagenumber{A-3}
            \realpagenumber{A-4}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))

        # Check that the DOM has the expected structure
        elems = dom.getElementsByTagName('realpagenumber')
        assert_that(elems, has_length(4))
        assert_that(elems[0], is_(realpagenumber))

        # Check that the ntienumerate object has the expected children
        assert_that(elems[0].pagenumber, is_('A-1'))
        assert_that(elems[1].pagenumber, is_('A-2'))
        assert_that(elems[2].pagenumber, is_('A-3'))
        assert_that(elems[3].pagenumber, is_('A-4'))
