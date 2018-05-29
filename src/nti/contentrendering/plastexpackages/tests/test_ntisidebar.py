#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that

import unittest

from nti.contentrendering.plastexpackages.ntisidebar import sidebar

from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import buildDomFromString as _buildDomFromString


def _simpleLatexDocument(maths):
    return simpleLatexDocumentText(
        preludes=(r'\usepackage{nti.contentrendering.plastexpackages.ntisidebar}',),
        bodies=maths)


class TestNTISidebar(unittest.TestCase):

    def test_ntienumerate(self):
        example = r"""
            \begin{sidebar}
                Ichigo
            \end{sidebar}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))

        # Check that the DOM has the expected structure
        assert_that(dom.getElementsByTagName('sidebar'), has_length(1))
        assert_that(dom.getElementsByTagName('sidebar')[0],
                    is_(sidebar))
