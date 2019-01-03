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
    _ntiid_allow_missing_title = True
    _ntiid_cache_map_name = '_concept_ntiid_map'

    embedded_doc_cross_ref_url = property(plastexids._embedded_node_cross_ref_url)

    def invoke(self, tex):
        result = super(concept, self).invoke(tex)
        return result

    def __delitem__(self, i):
        raise NotImplementedError


class conceptref(Crossref.ref):
    macroName = 'conceptref'
    args = 'label:idref'
