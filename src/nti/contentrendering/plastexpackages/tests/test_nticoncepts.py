#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

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
                    \begin{concept}<algebra>
                    \end{concept}
                    \begin{concept}<subtraction>
                    \end{concept}
                \end{concept}
            \end{concepthierarchy}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))
        # Check that the DOM has the expected structure
        elems = dom.getElementsByTagName('concepthierarchy')
        assert_that(elems[0], is_(concepthierarchy))

        concepts = dom.getElementsByTagName('concept')
        assert_that(u''.join(concepts[0].title.childNodes), is_('math'))
        assert_that(u''.join(concepts[1].title.childNodes), is_('algebra'))
        assert_that(u''.join(concepts[2].title.childNodes), is_('subtraction'))

    def test_concept_hierarchy_2(self):
        example = r"""
            \chapter{Chapter 1}
            \label{chapter:1}
            \begin{concepthierarchy}
                \begin{concept}<Basic Math>
                    \begin{concept}<addition>
                    \end{concept}
                    \begin{concept}<subtraction>
                    \end{concept}
                \end{concept}
                \begin{concept}<Intermediate Math>
                    \begin{concept}<Multiplication>
                    \end{concept}
                    \begin{concept}<Division>
                    \end{concept}
                \end{concept}
            \end{concepthierarchy}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))
        # Check that the DOM has the expected structure
        elems = dom.getElementsByTagName('concepthierarchy')
        assert_that(elems[0], is_(concepthierarchy))

        concept_l1 = []
        for child in elems[0].childNodes:
            if hasattr(child, 'tagName'):
                concept_l1.append(child)

        c1 = concept_l1[0]
        c2 = concept_l1[1]
        assert_that(u''.join(c1.title.childNodes), is_('Basic Math'))
        assert_that(u''.join(c2.title.childNodes), is_('Intermediate Math'))

        concept_l2_1 = []
        for child in c1.childNodes:
            if hasattr(child, 'tagName'):
                if child.tagName == 'concept':
                    concept_l2_1.append(child)

        assert_that(u''.join(concept_l2_1[0].title.childNodes), is_('addition'))
        assert_that(u''.join(concept_l2_1[1].title.childNodes), is_('subtraction'))

        concept_l2_2 = []
        for child in c2.childNodes:
            if hasattr(child, 'tagName'):
                if child.tagName == 'concept':
                    concept_l2_2.append(child)

        assert_that(u''.join(concept_l2_2[0].title.childNodes), is_('Multiplication'))
        assert_that(u''.join(concept_l2_2[1].title.childNodes), is_('Division'))

    def test_concept_hierarchy_3(self):
        example = r"""
            \section{Section 1}
            \label{section:1}
            \conceptref{concept:Calculus}

            \begin{sidebar}{Title Bar 1}
            \label{sidebar:1}
            This is sample sidebar 1
            \end{sidebar}

            \begin{sidebar}{Title Bar 2}
            This is sample sidebar 2
            \end{sidebar}

            \ntiidref{sidebar:1}<This is a sidebar 1>

            \begin{concepthierarchy}
                \begin{concept}<Algebra>
                    \begin{concept}<Linear Programming>
                    \end{concept}
                    \begin{concept}<Quadratic Formulas>
                    \end{concept}
                \end{concept}
                \begin{concept}<Calculus>
                \label{concept:Calculus}
                \end{concept}
            \end{concepthierarchy}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))
        # Check that the DOM has the expected structure
        elems = dom.getElementsByTagName('concepthierarchy')
        ch = elems[0]
        assert_that(ch, is_(concepthierarchy))
        concepts = []
        for child in ch:
            if hasattr(child, 'tagName'):
                concepts.append(child)

        assert_that(concepts[0].tagName, is_('concept'))
        assert_that(concepts[1].tagName, is_('concept'))

        crefs = dom.getElementsByTagName('conceptref')
        cref = crefs[0]
        nrefs = dom.getElementsByTagName('ntiidref')
        nref = nrefs[0]
        sidebars = dom.getElementsByTagName('sidebar')
        sidebar = sidebars[0]

        assert_that(u''.join(concepts[0].title.childNodes), is_('Algebra'))
        assert_that(u''.join(concepts[1].title.childNodes), is_('Calculus'))

    def test_concept_hierarchy_4(self):
        example = r"""
            \begin{concepthierarchy}
                \begin{concept}<Algebra>
                    \label{c1}
                \end{concept}
                \begin{concept}<Calculus>
                    \label{c2}
                \end{concept}
            \end{concepthierarchy}

            \section{Section 1}
            \label{section:1}
            \conceptref{c1}

            \section{Section 2}
            \label{section:2}
            \conceptref{c2}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))
        concepts = dom.getElementsByTagName('concept')
        crefs = dom.getElementsByTagName('conceptref')
        cref1 = crefs[0]
        cref2 = crefs[1]

        assert_that(cref1.idref['label'], is_(concepts[0]))
        assert_that(cref1.idref['label'].ntiid, is_(u'tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.c1'))

        assert_that(cref2.idref['label'], is_(concepts[1]))
        assert_that(cref2.idref['label'].ntiid, is_(u'tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.c2'))

    def test_concept_hierarchy_5(self):
        example = r"""
            \begin{concepthierarchy}
                \begin{concept}<Algebra>
                \label{con:algb}
                \end{concept}
                \begin{concept}<Calculus>
                \end{concept}
            \end{concepthierarchy}

            \section{Section 1}
            \label{section:1}
            \conceptref{concept:algebra}

            \section{Section 2}
            \label{section:2}
            \conceptref{concept:calculus}
        """
        dom = _buildDomFromString(_simpleLatexDocument((example,)))
        concepts = dom.getElementsByTagName('concept')
        crefs = dom.getElementsByTagName('conceptref')
        cref1 = crefs[0]
        cref2 = crefs[1]

        assert_that(concepts[0].ntiid, is_(u'tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.con:algb'))
        assert_that(concepts[1].ntiid, is_(u'tag:nextthought.com,2011-10:testing-NTIConcept-temp.concept.calculus'))

        # # TODO : get the next line works
        # assert_that(cref1.idref['label'], is_(concepts[0]))
        # assert_that(cref2.idref['label'], is_(concepts[1]))
