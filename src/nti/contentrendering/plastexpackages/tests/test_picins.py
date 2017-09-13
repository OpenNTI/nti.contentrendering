#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import has_length
from hamcrest import assert_that

import unittest

from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import buildDomFromString as _buildDomFromString


def _simpleLatexDocument(maths):
    return simpleLatexDocumentText(preludes=(r'\usepackage{nti.contentrendering.plastexpackages.picins}',),
                                   bodies=maths)


class TestPicins(unittest.TestCase):

    def test_picskip(self):
        example = r"""
		\picskip{0}
		"""
        dom = _buildDomFromString(_simpleLatexDocument((example,)))
        assert_that(dom.getElementsByTagName('picskip'), has_length(0))

    def test_parpic(self):
        example = r"""
		\parpic(0pt,2.8in)[r][t]{\includegraphics{test}}
		"""
        dom = _buildDomFromString(_simpleLatexDocument((example,)))
        assert_that(dom.getElementsByTagName('parpic'), has_length(1))
