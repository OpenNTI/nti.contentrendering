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

from nti.contentrendering.plastexpackages.ntilatexmacros import expectedconsumptiontime

from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import buildDomFromString as _buildDomFromString


def _simpleLatexDocument(maths):
    return simpleLatexDocumentText(
        preludes=(r'\usepackage{nti.contentrendering.plastexpackages.ntilatexmacros}',),
        bodies=maths)


class TestNTIContentMetrics(unittest.TestCase):

    def test_expectedconsumptiontime(self):
        example = r"""
            \chapter{Glossary}
            \label{glossaryid}
            \expectedconsumptiontime{600}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))
        # Check that the DOM has the expected structure
        elems = dom.getElementsByTagName('expectedconsumptiontime')
        assert_that(elems[0], is_(expectedconsumptiontime))
