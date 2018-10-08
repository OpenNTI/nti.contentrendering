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
from nti.contentrendering.interfaces import IContentUnitStatistics

from nti.contentrendering.plastexpackages.extractors.html.reader import HTMLReader

from nti.contentrendering.plastexpackages.extractors.html.statistics import HTMLExtractor

logger = __import__('logging').getLogger(__name__)


@component.adapter(IRenderedBook)
@interface.implementer(IContentUnitStatistics)
class _ContentUnitStatistics(object):

    def __init__(self, book=None, lang='en'):
        self.lang = lang

    def transform(self, book, outpath=None):
        outpath = outpath or book.contentLocation
        self.outpath = os.path.expanduser(outpath)
        target = os.path.join(outpath, 'content_index.json')
        dom = book.toc.dom
        root = dom.documentElement
        index = {'Items': {}}
        self._process_topic(root, index['Items'])
        

        logger.info("Extracting content statistics to %s", target)
        with codecs.open(target, 'w', encoding='utf-8') as fp:
            json.dump(index,
                      fp,
                      indent='\t',
                      sort_keys=True,
                      ensure_ascii=True)
        return index

    def _process_topic(self, node, index):
        unique_words = set()
        if node.hasAttribute('ntiid'):
            ntiid = node.getAttributeNode('ntiid').value
            element_index = index[ntiid] = {}
            element_index['NTIID'] = ntiid
            element_index['href'] = node.getAttributeNode('href').value
            if u'#' not in element_index['href']:
                element_index['data']={}
                html_element = self._read_html(element_index['href'])
                extractor = HTMLExtractor(html_element, self.lang)
                element_index['data']['number_of_paragraphs'] = extractor.number_paragraph
                element_index['data']['number_of_words'] = extractor.number_word
                element_index['data']['number_of_sentences'] = extractor.number_sentence
                element_index['data']['number_of_unique_words'] = extractor.number_unique_word
                unique_words = extractor.unique_words
        
        if node.hasChildNodes():
            for child in node.childNodes:
                if child.nodeName == 'topic':
                    containing_index = element_index.setdefault('Items', {})
                    child_unique_words = self._process_topic(child, containing_index)
                    child_ntiid = child.getAttributeNode('ntiid').value
                    if 'data' in containing_index[child_ntiid]:
                        element_index['data']['number_of_paragraphs'] += containing_index[child_ntiid]['data']['number_of_paragraphs']
                        element_index['data']['number_of_sentences'] += containing_index[child_ntiid]['data']['number_of_sentences']
                        element_index['data']['number_of_words'] += containing_index[child_ntiid]['data']['number_of_words']
                        unique_words = unique_words.union(child_unique_words)
            element_index['data']['number_of_unique_words'] = len(unique_words)
        return unique_words
                    
    def _read_html(self, name):
        filename = os.path.join(os.path.dirname(__file__), self.outpath, name)
        reader = HTMLReader(filename)
        element = reader.element
        return element
