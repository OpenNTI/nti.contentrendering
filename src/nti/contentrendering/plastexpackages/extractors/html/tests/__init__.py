#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import unittest

from nti.contentrendering.tests import SharedConfiguringTestLayer


class HTMLSample(object):
	number_paragraph = 0
	number_sidebar = 0

class HTMLExtractorTests(unittest.TestCase):
    layer = SharedConfiguringTestLayer
