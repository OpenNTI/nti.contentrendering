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

    def test_concept_hierarchy_2(self):
        example = r"""
            \chapter{Chapter 1}
            \label{chapter:1}
            \begin{concepthierarchy}
                \begin{concept}<Basic Math>
                    \subconcept{addition}
                    \subconcept{subtraction}
                \end{concept}
                \begin{concept}<Intermediate Math>
                    \subconcept{Multiplication}
                    \subconcept{Division}
                \end{concept}
            \end{concepthierarchy}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))
        # Check that the DOM has the expected structure
        elems = dom.getElementsByTagName('concepthierarchy')
        assert_that(elems[0], is_(concepthierarchy))

        ch = elems[0]
        concepts = ch.getElementsByTagName('concept')
        assert_that(len(concepts), is_(2))

        concept_1 = concepts[0]
        assert_that(concept_1.title, is_('Basic Math'))
        subconcepts = concept_1.getElementsByTagName('subconcept')
        assert_that(subconcepts[0].attributes['value'], is_('addition'))
        assert_that(subconcepts[1].attributes['value'], is_('subtraction'))

        concept_2 = concepts[1]
        assert_that(concept_2.title, is_('Intermediate Math'))
        subconcepts = concept_2.getElementsByTagName('subconcept')
        assert_that(subconcepts[0].attributes['value'], is_('Multiplication'))
        assert_that(subconcepts[1].attributes['value'], is_('Division'))

    def test_concept_hierarchy_3(self):
        example = r"""
            \chapter{Chapter 1}
            \label{chapter:1}
            \begin{concepthierarchy}
                \begin{concept}<Algebra>
                    \begin{concept}<Linear Programming>
                        \subconcept{Feasible LP}
                        \subconcept{Non Feasible LP}
                    \end{concept}
                    \subconcept{Quadratic Formulas}
                \end{concept}
            \end{concepthierarchy}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))
        # Check that the DOM has the expected structure
        elems = dom.getElementsByTagName('concepthierarchy')
        ch = elems[0]
        concepts_level_1 = []
        for child in ch:
            if hasattr(child, 'tagName'):
                concepts_level_1.append(child)
        assert_that(len(concepts_level_1), is_(1))
        assert_that(concepts_level_1[0].tagName, is_('concept'))
        assert_that(concepts_level_1[0].title, is_('Algebra'))

        concept_1 = concepts_level_1[0]
        concept_1_child_nodes = []
        for child in concept_1:
            if hasattr(child, 'tagName'):
                concept_1_child_nodes.append(child)
        assert_that(len(concept_1_child_nodes), is_(2))
        assert_that(concept_1_child_nodes[0].tagName, is_('concept'))
        assert_that(concept_1_child_nodes[0].title, is_('Linear Programming'))
        assert_that(concept_1_child_nodes[1].tagName, is_('subconcept'))
        assert_that(concept_1_child_nodes[1].attributes['value'], is_('Quadratic Formulas'))

        concepts_level_2 = []
        for child in concept_1_child_nodes[0]:
            if hasattr(child, 'tagName'):
                concepts_level_2.append(child)
        assert_that(len(concepts_level_2), is_(2))
        assert_that(concepts_level_2[0].tagName, is_('subconcept'))
        assert_that(concepts_level_2[0].attributes['value'], is_('Feasible LP'))
        assert_that(concepts_level_2[1].tagName, is_('subconcept'))
        assert_that(concepts_level_2[1].attributes['value'], is_('Non Feasible LP'))
