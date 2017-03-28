#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from plasTeX import Base
from plasTeX import Environment

from nti.contentrendering.plastexpackages._util import LocalContentMixin


class ntisequenceitem(LocalContentMixin, Environment):
    args = '[options:dict]'

    def invoke(self, tex):
        res = super(ntisequenceitem, self).invoke(tex)
        if 'options' not in self.attributes or not self.attributes['options']:
            self.attributes['options'] = {}
        return res

    def digest(self, tokens):
        tok = super(ntisequenceitem, self).digest(tokens)
        if self.macroMode != Environment.MODE_END:
            options = self.attributes.get('options', {}) or {}
            __traceback_info__ = options, self.attributes
            for k, v in options.items():
                setattr(self, k, v)
        return tok


class ntisequence(LocalContentMixin, Base.List):
    args = '[options:dict]'

    def invoke(self, tex):
        res = super(ntisequence, self).invoke(tex)
        if 'options' not in self.attributes or not self.attributes['options']:
            self.attributes['options'] = {}
        return res

    def digest(self, tokens):
        tok = super(ntisequence, self).digest(tokens)
        if self.macroMode != Environment.MODE_END:
            items = self.getElementsByTagName('ntisequenceitem')
            assert len(items) >= 1
            options = self.attributes.get('options', {}) or {}
            for k, v in options.items():
                setattr(self, k, v)
        return tok


class ntisequenceref(Base.Crossref.ref):
    args = '[options:dict] label:idref'
