#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from plasTeX import Command

from plasTeX.Base import Crossref

from plasTeX.Packages.hyperref import href as plastex_href

logger = __import__('logging').getLogger(__name__)


class simpleref(plastex_href):
    pass


class ntihref(plastex_href):
    args = '[options:dict] url:url self'

    def invoke(self, tex):
        main_key = 'nti-requirements'
        token = super(ntihref, self).invoke(tex)
        if 'options' not in self.attributes or not self.attributes['options']:
            self.attributes['options'] = {}
        options = self.attributes.get('options')
        self.attributes[main_key] = u''
        requirements = options.get(main_key, u'').split()
        for requirement in requirements:
            if requirement == u'flash':
                requirement = u'mime-type:application/x-shockwave-flash'
            current = [self.attributes[main_key], requirement]
            self.attributes[main_key] = ' '.join(current)
        self.attributes[main_key] = self.attributes[main_key].strip()
        if self.attributes[main_key] == u'':
            self.attributes[main_key] = None
        return token


class ntiimagehref(Command):
    args = 'img url'


class ntifancyhref(Command):
    args = 'url:str:source self class'


class ntiidref(Crossref.ref):
    """
    Used for producing a cross-document link, like a normal
    ref, but output as an NTIID.
    """
    macroName = 'ntiidref'
    args = 'label:idref <title:str:source>'
