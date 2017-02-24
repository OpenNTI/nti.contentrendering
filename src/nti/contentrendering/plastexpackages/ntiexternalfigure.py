#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from plasTeX import Command
from plasTeX import TeXFragment

from zope.cachedescriptors.property import readproperty


class ntiexternalfigure(Command):

    captionable = True
    macroName = 'ntiexternalfigure'
    args = '* [ options:dict ] url:str'

    @readproperty
    def caption(self):
        if self.title:
            result = TeXFragment()
            result.parentNode = self
            result.appendChild(self.title)
            result.ownerDocument = self.ownerDocument
            return result
