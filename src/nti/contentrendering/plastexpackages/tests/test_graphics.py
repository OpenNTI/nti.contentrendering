#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import has_length
from hamcrest import assert_that

import unittest

from nti.contentrendering.tests import simpleLatexDocumentText
from nti.contentrendering.tests import buildDomFromString as _buildDomFromString

def _simpleLatexDocument(maths):
	return simpleLatexDocumentText( preludes=(br'\usepackage{nti.contentrendering.plastexpackages.graphics}',),
									bodies=maths)

class TestGraphics(unittest.TestCase):

	def test_DeclareGraphicsRule(self):
		example = br"""
		\DeclareGraphicsRule{*}{mps}{*}{}
		"""
		dom = _buildDomFromString(_simpleLatexDocument((example,)))
		assert_that(dom.getElementsByTagName('DeclareGraphicsRule'), has_length(1))
