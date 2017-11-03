#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from plasTeX.DOM import Text

from plasTeX.Packages.html import rawhtml

logger = __import__('logging').getLogger(__name__)


class ntirawhtml(rawhtml):

    def set_html(self, html):
        self.unicode = Text(html)
        self.unicode.isMarkup = True
