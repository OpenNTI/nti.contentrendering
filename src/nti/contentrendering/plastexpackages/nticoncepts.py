#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

logger = __import__('logging').getLogger(__name__)

from plasTeX import Command
from plasTeX import Environment

from plasTeX.Base import Crossref

from nti.contentrendering import plastexids


class concepthierarchy(Environment):
    blockType = True


class concept(Environment, plastexids.NTIIDMixin):
    args = '<title>'
    blockType = True

    counter = 'concept'

    _ntiid_suffix = u'concept.'
    _ntiid_title_attr_name = 'title'
    _ntiid_type = u'NTIConcept'
    _ntiid_allow_missing_title = False
    _ntiid_cache_map_name = '_concept_ntiid_map'

    def invoke(self, tex):
        result = super(concept, self).invoke(tex)
        return result

    def digest(self, tokens):
        result = super(concept, self).digest(tokens)
        # generate id from ntiid if \label is not specified under the concept environment
        # TODO : how the \conceptref{} can point the concept env when the \label is not specified
        _id = getattr(self, "@id", self)
        if _id is self:
            dlabel = getattr(self, "ntiid", self)
            idx = dlabel.rfind(self._ntiid_suffix)
            idx = idx + len(self._ntiid_suffix)
            dlabel = u'concept:{}'.format(dlabel[idx:])
            setattr(self, "@id", dlabel)
            label_node = Crossref.label()
            label_node.argSource = u'{%s}' % (dlabel)
            label_node.setAttribute('label', dlabel)
            self.appendChild(label_node)
        return result

    def __delitem__(self, i):
        raise NotImplementedError


class conceptref(Crossref.ref):
    macroName = 'conceptref'
    args = 'label:idref'
