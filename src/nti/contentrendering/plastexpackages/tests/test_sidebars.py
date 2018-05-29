#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import contains_string

import unittest

from nti.contentrendering.plastexpackages.ntisidebar import sidebar

from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import buildDomFromString as _buildDomFromString


def _simpleLatexDocument(maths):
    return simpleLatexDocumentText(
        preludes=(r'\usepackage{nti.contentrendering.plastexpackages.ntisidebar}',),
        bodies=maths)


class TestSidebars(unittest.TestCase):

    def test_basic(self):
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


    def test_sidebar_basic(self):
        example = br"""
        \begin{sidebar}{Title}
        \label{sidebar:Basic_Sidebar}
        Body Text
        \end{sidebar}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))

        # Check that the DOM has the expected structure
        assert_that(dom.getElementsByTagName('sidebar'), has_length(1))

        sidebar_el = dom.getElementsByTagName('sidebar')[0]

        # Check that the relatedworkref object has the expected attributes
        assert_that(sidebar_el.attributes.get('title').source,
                    contains_string('Title'))
        assert_that(sidebar_el.childNodes[2].source,
                    contains_string('Body Text'))

        assert_that(sidebar_el.css_class, contains_string('sidebar'))

    def test_sidebar_basic_styled(self):
        example = br"""
        \begin{sidebar}[css-class=warning]{Title}
        \label{sidebar:Basic_Sidebar}
        Body Text
        \end{sidebar}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))

        # Check that the DOM has the expected structure
        assert_that(dom.getElementsByTagName('sidebar'), has_length(1))

        sidebar_el = dom.getElementsByTagName('sidebar')[0]

        assert_that(sidebar_el.css_class, contains_string('sidebar warning'))

    def test_sidebar_basic_ntiid(self):
        example = br"""
        \begin{sidebar}{Title}
        \label{sidebar:Basic_Sidebar}
        Body Text
        \end{sidebar}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))
        dom.config.set('NTI', 'strict-ntiids', True)

        # Check that the DOM has the expected structure
        assert_that(dom.getElementsByTagName('sidebar'), has_length(1))

        sidebar_el = dom.getElementsByTagName('sidebar')[0]

        # Check that the relatedworkref object has the expected attributes
        assert_that(sidebar_el.ntiid,
                    contains_string('tag:nextthought.com,2011-10:testing-HTML:NTISidebar-temp.sidebar.sidebar_Basic_Sidebar'))

    def test_sidebar_flat(self):
        example = br"""
        \begin{flatsidebar}{Title}
        \label{sidebar:Flat_Sidebar}
        Body Text
        \end{flatsidebar}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))

        # Check that the DOM has the expected structure
        assert_that(dom.getElementsByTagName('flatsidebar'), has_length(1))

        sidebar_el = dom.getElementsByTagName('flatsidebar')[0]

        # Check that the relatedworkref object has the expected attributes
        assert_that(sidebar_el.attributes.get(
            'title').source, contains_string('Title'))
        assert_that(sidebar_el.childNodes[2].source,
                    contains_string('Body Text'))

    def test_sidebar_graphic(self):
        example = br"""
        \begin{ntigraphicsidebar}{Title}{testing}
        \label{sidebar:Graphic_Sidebar}
        Body Text
        \end{ntigraphicsidebar}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))

        # Check that the DOM has the expected structure
        assert_that(dom.getElementsByTagName('ntigraphicsidebar'),
                    has_length(1))

        sidebar_el = dom.getElementsByTagName('ntigraphicsidebar')[0]

        # Check that the relatedworkref object has the expected attributes
        assert_that(sidebar_el.attributes.get('title').source,
                    contains_string('Title'))
        assert_that(sidebar_el.attributes.get('graphic_class'),
                    contains_string('testing'))
        assert_that(sidebar_el.childNodes[2].source,
                    contains_string('Body Text'))
