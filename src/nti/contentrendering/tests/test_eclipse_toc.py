#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import none
from hamcrest import is_not
from hamcrest import equal_to
from hamcrest import assert_that

import os

from nti.contentrendering.RenderedBook import EclipseTOC

from nti.contentrendering.tests import ContentrenderingLayerTest


class TestEclipseTOC(ContentrenderingLayerTest):

    def setUp(self):
        self.eclipsetoc = EclipseTOC(os.path.join(
            os.path.dirname(__file__),  'eclipse-toc.xml'))

    def test_getrootnode(self):
        rootNode = self.eclipsetoc.getRootTOCNode()
        assert_that(rootNode, is_not(none()), 'root node should not be none')
        self.assertValidNode(rootNode,
                             ntiid=u'aops-prealgebra-31',
                             href=u'index.html',
                             label=u'Prealgebra',
                             height=u'11990',
                             icon=u'icons/chapters/PreAlgebra-cov-icon.png')

    def test_getnodebyid(self):
        rootNode = self.eclipsetoc.getRootTOCNode()
        assert_that(rootNode,
                    equal_to(self.eclipsetoc.getPageNodeWithNTIID('aops-prealgebra-31')))

        self.assertAttribute(self.eclipsetoc.getPageNodeWithNTIID('aops-prealgebra-25'),
                             'ntiid',
                             'aops-prealgebra-25')

    def test_getnodebyattribute(self):
        rootNode = self.eclipsetoc.getRootTOCNode()
        assert_that(rootNode,
                    equal_to(self.eclipsetoc.getPageNodeWithAttribute('label', value='Prealgebra')[0]))

        self.assertAttribute(self.eclipsetoc.getPageNodeWithAttribute('label', 'Greatest Common Divisor')[0],
                             'label',
                             'Greatest Common Divisor')

    def test_getPageNodes(self):
        nodes = self.eclipsetoc.getPageNodes()

        self.assertEqual(31, len(nodes))

        labels = [node.getAttribute('label') for node in nodes]

        self.assertFalse('Index' in labels)

    def assertValidNode(self, node, ntiid=None, href=None, label=None,
                        height=None, icon=None):
        assert_that(node, is_not(none()), 'node should not be none')
        if ntiid:
            self.assertAttribute(node, 'ntiid', ntiid)
        if href:
            self.assertAttribute(node, 'href', href)
        if label:
            self.assertAttribute(node, 'label', label)
        if height:
            self.assertAttribute(node, 'NTIRelativeScrollHeight', height)
        if icon:
            self.assertAttribute(node, 'icon', icon)

    def assertAttribute(self, node, attrname, attrval):
        assert_that(node, is_not(none()), 'node should not be none')
        self.assertTrue(hasattr(node, 'hasAttribute'),
                        '%s isn\'t a node with attributes' % node)
        self.assertTrue(node.hasAttribute(attrname),
                        '%s has no attribute named %s' % (node, attrname))

        value = node.getAttribute(attrname)
        self.assertEqual(value, attrval,
                         'For node %s, attribute %s expected value %s but got %s' % (node, attrname, attrval, value))
