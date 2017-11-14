#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from plasTeX import Environment

from plasTeX.DOM import Text as BaseText

from plasTeX.Packages.html import rawhtml

from nti.property.property import alias

logger = __import__('logging').getLogger(__name__)


class Text(BaseText):
    isMarkup = alias('is_markup')


class ntirawhtml(rawhtml):

    isMarkup = True

    def set_html(self, html):
        self.unicode = Text(html)
        self.unicode.isMarkup = True


class ntiblockquote(Environment):
    blockType = True
