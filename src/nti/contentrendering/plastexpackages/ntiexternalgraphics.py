#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from plasTeX import TeXFragment

from plasTeX import Command

from zope.cachedescriptors.property import readproperty


class ntiexternalgraphics(Command):

    captionable = True
    args = '[options:dict] url:str'

    @readproperty
    def caption(self):
        if self.title:
            result = TeXFragment()
            result.parentNode = self
            result.appendChild(self.title)
            result.ownerDocument = self.ownerDocument
            return result

    def process_options(self):
        options = self.attributes['options']
        if options:
            style = options.get('style')
            if style is not None:
                self.style = style

            height = options.get('height')
            if height is not None:
                self.height = height

            width = options.get('width')
            if width is not None:
                self.width = width

            size = options.get('size')
            if size is not None:
                self.size = size

    def invoke(self, tex):
        res = Command.invoke(self, tex)
        self.external = self.attributes['url']
        self.process_options()
        return res

externalgraphics = ntiexternalgraphics
