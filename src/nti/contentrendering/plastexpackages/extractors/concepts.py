#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract content unit statistics

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

import codecs

import simplejson as json

from zope import component
from zope import interface

from nti.contentrendering.interfaces import IRenderedBook
from nti.contentrendering.interfaces import IConceptsExtractor

logger = __import__('logging').getLogger(__name__)


@component.adapter(IRenderedBook)
@interface.implementer(IConceptsExtractor)
class _ConceptsExtractor(object):

    def __init__(self, unused_book=None, lang='en'):
        self.lang = lang
        self.outpath = None

    def transform(self, book, outpath=None):
        outpath = outpath or book.contentLocation
        self.outpath = os.path.expanduser(outpath)
        target = os.path.join(outpath, 'concepts.json')
        root = book.document

        index = self._process_concept(root)

        logger.info("Extracting concepts tree to %s", target)
        with codecs.open(target, 'w', encoding='utf-8') as fp:
            json.dump(index,
                      fp,
                      indent='\t',
                      sort_keys=False,
                      ensure_ascii=True)
        return index

    def _process_concept(self, root):
        concept_refs = root.getElementsByTagName('conceptref')
        refs_index = self._build_concept_refs_index(concept_refs)

        # assuming a book only has one concepthierarchy environment
        concept_tree = root.getElementsByTagName('concepthierarchy')
        concept = {}
        index = {'concepthierarchy': concept}
        if concept_tree:
            self._build_concept_hierarchy_index(concept_tree[0], index['concepthierarchy'], refs_index)

        return index

    def _build_concept_refs_index(self, refs):
        index = {}
        for node in refs:
            idref = node.idref['label'].ntiid
            unit_ntiid = self._search_section_level(node)
            if idref not in index:
                index[idref] = [unit_ntiid]
            else:
                index[idref] = index[idref].append(unit_ntiid)
        return index

    def _search_section_level(self, node):
        parent = node.parentNode
        ntiid = getattr(parent, 'ntiid', None)
        if not ntiid:
            ntiid = self._search_section_level(parent)
        return ntiid

    def _build_concept_hierarchy_index(self, element, index, refs_index):
        if hasattr(element, 'tagName'):
            if element.tagName == 'concept':
                ntiid = getattr(element, 'ntiid', None)
                concept_tag = u''.join(element.title.childNodes)
                element_index = index[ntiid] = {}
                element_index['name'] = concept_tag
                element_index['refs'] = []
                if ntiid in refs_index:
                    element_index['refs'] = refs_index[ntiid]
            else:
                element_index = index

            if element.hasChildNodes():
                for child in element.childNodes:
                    containing_index = element_index.setdefault('concept', {})
                    self._build_concept_hierarchy_index(child, containing_index, refs_index)
