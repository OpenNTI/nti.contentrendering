#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.cachedescriptors.property import readproperty

from plasTeX import Base

from nti.contentrendering import plastexids

from nti.contentrendering.plastexpackages._util import LocalContentMixin


class ntimediaref(Base.Crossref.ref):

    args = '[options:dict] label:idref'

    _options = {}
    to_render = False

    def digest(self, tokens):
        tok = super(ntimediaref, self).digest(tokens)
        self._options = self.attributes.get('options', {}) or {}
        if 'to_render' in self._options.keys():
            if self._options['to_render'] in [u'true', u'True']:
                self.to_render = True
        return tok

    @readproperty
    def media(self):
        return self.idref['label']

    @readproperty
    def visibility(self):
        visibility = self._options.get('visibility') or None
        if visibility is None:
            return self.media.visibility
        return visibility


class ntimedia(LocalContentMixin, Base.Float, plastexids.NTIIDMixin):

    blockType = True
    args = '[ options:dict ]'

    _ntiid_title_attr_name = 'ref'
    _ntiid_allow_missing_title = False

    creator = None
    num_sources = 0
    closed_caption = None

    title = 'No Title'

    @readproperty
    def description(self):
        return None

    @readproperty
    def transcripts(self):
        return None
