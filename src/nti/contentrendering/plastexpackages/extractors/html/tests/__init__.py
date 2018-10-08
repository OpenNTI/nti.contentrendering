#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

import unittest

from nti.contentrendering.tests import SharedConfiguringTestLayer


class HTMLSample(object):
    number_paragraph = 0
    number_sidebar = 0


class HTMLExtractorTests(unittest.TestCase):
    layer = SharedConfiguringTestLayer
