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

from nti.contentrendering.plastexpackages.ntiexternalgraphics import ntiexternalgraphics

from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import buildDomFromString as _buildDomFromString


def _simpleLatexDocument(maths):
    return simpleLatexDocumentText(
                  preludes=(br'\usepackage{nti.contentrendering.plastexpackages.ntilatexmacros}',),
                            bodies=maths)


class TestNTIExternalGraphics(unittest.TestCase):

    def test_externalfigure(self):
        example = br"""
            \begin{figure}
                \ntiexternalgraphics[width=600px]{https://bleach.com/ichigo_bankai.png}\\
                \caption{\textbf{Bankai} Tensa Zangetsu a fearsome Bankai}
                \label{fig:ichigo}
            \end{figure}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))

        # Check that the DOM has the expected structure
        assert_that(dom.getElementsByTagName('ntiexternalgraphics'), has_length(1))
        assert_that(dom.getElementsByTagName('ntiexternalgraphics')[0], 
                    is_(ntiexternalgraphics))

        # Check ntiexternalgraphics
        elem = dom.getElementsByTagName('ntiexternalgraphics')[0]
        assert_that(elem, has_property('width', is_('600px')))
        assert_that(elem, has_property('external', is_('https://bleach.com/ichigo_bankai.png')))
        
