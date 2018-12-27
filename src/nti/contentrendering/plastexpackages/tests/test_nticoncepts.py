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

from nti.contentrendering.plastexpackages.ntilatexmacros import concepthierarchy

from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import buildDomFromString as _buildDomFromString


def _simpleLatexDocument(maths):
    return simpleLatexDocumentText(
        preludes=(r'\usepackage{nti.contentrendering.plastexpackages.ntilatexmacros}',),
        bodies=maths)


class TestNTIConcepts(unittest.TestCase):

    def test_concept_hierarchy(self):
        example = r"""
            \chapter{Glossary}
            \label{glossaryid}
            \begin{concepthierarchy}
            \begin{concept}<math>
            \subconcept{algebra}
            \subconcept{subtraction}
            \end{concept}
            \end{concepthierarchy}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))
        # Check that the DOM has the expected structure
        elems = dom.getElementsByTagName('concepthierarchy')
        assert_that(elems[0], is_(concepthierarchy))

        concept_list = elems[0].getElementsByTagName('concept')
        assert_that(len(concept_list), is_(1))
        assert_that(concept_list[0].title, is_('math'))

        concept = concept_list[0]
        subconcepts = concept.getElementsByTagName('subconcept')
        assert_that(subconcepts[0].attributes['value'], is_('algebra'))
        assert_that(subconcepts[1].attributes['value'], is_('subtraction'))
